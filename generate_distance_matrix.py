
import csv
import os
import sys
from pathlib import Path
import re
import requests
from urllib.parse import urlparse

import openrouteservice
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
PATIENTS_FILE = ROOT / "data" / "patients.csv"
OUTPUT_FILE = ROOT / "data" / "distance_matrix.csv"

HOME_ADDRESS = "2005 Beechwood Blvd, Pittsburgh, PA 15217"


def load_locations():
    locations = [{"id": "HOME", "address": HOME_ADDRESS}]

    with PATIENTS_FILE.open(newline="", encoding="utf-8-sig") as file:
        for patient in csv.DictReader(file):
            address = (
                f"{patient['street_address']}, "
                f"{patient['city']}, "
                f"{patient['state']} {patient['zip_code']}"
            )

            locations.append({
                "id": patient["patient_id"],
                "address": address
            })

    if len({loc["id"] for loc in locations}) != len(locations):
        raise ValueError("Duplicate patient IDs detected.")

    return locations




def normalize_street(value):
    """Normalize common street abbreviations for comparison."""
    value = value.lower().strip()
    value = re.sub(r"[.,]", " ", value)
    value = re.sub(r"\s+", " ", value)

    replacements = {
        "street": "st",
        "avenue": "ave",
        "boulevard": "blvd",
        "road": "rd",
        "drive": "dr",
        "place": "pl",
        "east": "e",
        "west": "w",
        "north": "n",
        "south": "s",
    }

    words = value.split()
    return " ".join(replacements.get(word, word) for word in words)


def matching_address(requested, matched):
    """
    Compare house number and street name.

    Returns False if either is missing or different.
    """
    requested_street = requested.split(",")[0]
    matched_street = matched.split(",")[0]

    return (
        normalize_street(requested_street)
        == normalize_street(matched_street)
    )


def census_geocode(address):
    """Return a Census address match or None."""
    url = (
        "https://geocoding.geo.census.gov/"
        "geocoder/geographies/onelineaddress"
    )

    response = requests.get(
        url,
        params={
            "address": address,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "format": "json",
        },
        timeout=20,
    )
    response.raise_for_status()

    matches = response.json()["result"]["addressMatches"]

    for match in matches:
        if matching_address(address, match["matchedAddress"]):
            coords = match["coordinates"]
            return {
                "coordinates": [coords["x"], coords["y"]],
                "label": match["matchedAddress"],
            }

    return None


def geocode_locations(client, locations):
    coordinates = []
    failed = []

    for location in locations:
        location_id = location["id"]
        requested = location["address"]
        coords = None
        label = None
        source = None

        # First attempt: openrouteservice / Pelias.
        try:
            result = client.pelias_search(
                text=requested,
                size=1,
                country="US",
                focus_point=[-79.98, 40.44],
            )

            features = result.get("features", [])

            if features:
                feature = features[0]
                properties = feature["properties"]
                candidate_label = properties.get("label", "")

                if (
                    properties.get("layer") == "address"
                    and matching_address(requested, candidate_label)
                ):
                    coords = feature["geometry"]["coordinates"]
                    label = candidate_label
                    source = "ORS"

        except Exception as error:
            print(f"ORS lookup failed for {location_id}: {error}")

        # Second attempt: US Census Geocoding API.
        if coords is None:
            try:
                census_result = census_geocode(requested)

                if census_result:
                    coords = census_result["coordinates"]
                    label = census_result["label"]
                    source = "Census"

            except Exception as error:
                print(
                    f"Census lookup failed for {location_id}: {error}"
                )

        # Reject addresses neither provider could verify.
        if coords is None:
            failed.append((location_id, requested))
            print(f"REJECTED {location_id}: {requested}")
            continue

        longitude, latitude = coords

        # Geographic sanity check.
        if not (
            -80.15 <= longitude <= -79.80
            and 40.30 <= latitude <= 40.55
        ):
            failed.append((location_id, requested))
            print(f"REJECTED {location_id}: Outside Pittsburgh")
            continue

        coordinates.append(coords)

        print(
            f"ACCEPTED {location_id:>4} | "
            f"{source:>6} | "
            f"{label} | "
            f"{coords}"
        )

    if failed:
        print("\nAddresses requiring manual correction:")

        for location_id, address in failed:
            print(f"  {location_id}: {address}")

        raise ValueError(
            f"{len(failed)} locations could not be verified. "
            "Distance matrix not generated."
        )

    return coordinates



def generate_matrix(client, locations, coordinates):
    response = client.distance_matrix(
        locations=coordinates,
        profile="driving-car",
        metrics=["distance", "duration"],
        units="m"
    )

    distances = response["distances"]
    durations = response["durations"]

    rows = []

    for i, origin in enumerate(locations):
        for j, destination in enumerate(locations):
            if i == j:
                continue

            distance = distances[i][j]
            duration = durations[i][j]

            if distance is None or duration is None:
                raise ValueError(
                    f"No driving route from "
                    f"{origin['id']} to {destination['id']}"
                )

            rows.append({
                "from_id": origin["id"],
                "to_id": destination["id"],
                "distance_miles": round(distance / 1609.344, 2),
                "base_travel_minutes": round(duration / 60, 2)
            })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "from_id",
                "to_id",
                "distance_miles",
                "base_travel_minutes"
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} routes to {OUTPUT_FILE}")


def main():
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("ORS_API_KEY")

    if not api_key:
        raise ValueError("ORS_API_KEY missing from .env")

    client = openrouteservice.Client(key=api_key)
    locations = load_locations()

    print(f"\nGeocoding {len(locations)} locations:\n")
    coordinates = geocode_locations(client, locations)

    if "--generate" not in sys.argv:
        print(
            "\nReview all matched addresses above."
            "\nIf correct, rerun with --generate."
        )
        return

    print("\nRequesting driving distance matrix...")
    generate_matrix(client, locations, coordinates)


if __name__ == "__main__":
    main()
