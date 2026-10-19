import csv
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATIENTS_FILE = ROOT / "data" / "patients.csv"

# Move to config.py (build step A).
WEEK_START = date(2026, 10, 19)
WORK_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
WORK_START = 8 * 60
WORK_END = 17 * 60


@dataclass
class Patient:
    patient_id: str
    first_name: str
    last_name: str
    address: str
    visit_type: str
    restriction_reason: str = ""

    # Hard availability: day -> open (start, end) windows in minutes since
    # midnight. Only days the patient can be seen this week are present.
    windows: dict[str, list[tuple[int, int]]] = field(default_factory=dict)

    # Soft preferences (never override windows).
    preferred_days: list[str] = field(default_factory=list)
    preferred_times: dict[str, list[tuple[int, int]]] = field(
        default_factory=dict
    )

    @property
    def eligible_days(self):
        return [day for day in WORK_DAYS if day in self.windows]


def to_minutes(value):
    """Convert 'HH:MM' to minutes since midnight."""
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def parse_days(value):
    """Parse 'Mon|Tue' into ['Mon', 'Tue']."""
    days = [day for day in value.split("|") if day]

    for day in days:
        if day not in WORK_DAYS:
            raise ValueError(f"Unknown day: {day!r}")

    return days


def parse_windows(value):
    """Parse 'Mon:08:00-10:00|Wed:12:00-13:00' into {day: [(start, end)]}."""
    windows = {}

    for entry in filter(None, value.split("|")):
        day, span = entry.split(":", 1)
        start, end = (to_minutes(part) for part in span.split("-"))

        if day not in WORK_DAYS:
            raise ValueError(f"Unknown day in {entry!r}")
        if start >= end:
            raise ValueError(f"Window ends before it starts: {entry!r}")

        windows.setdefault(day, []).append((start, end))

    return windows


def subtract_windows(windows, blocks):
    """Remove each blocked (start, end) span from a list of open windows."""
    for block_start, block_end in blocks:
        remaining = []

        for start, end in windows:
            if block_end <= start or block_start >= end:
                remaining.append((start, end))
                continue
            if start < block_start:
                remaining.append((start, block_start))
            if block_end < end:
                remaining.append((block_end, end))

        windows = remaining

    return windows


def build_windows(row):
    """
    Apply the availability rules in order for each work day:

    1. Visit-date window (earliest/latest_visit_date), if set.
    2. restricted_days.
    3. available_times if set (unlisted days unavailable), else work hours.
    4. Subtract restricted_times.
    """
    earliest = row["earliest_visit_date"]
    latest = row["latest_visit_date"]
    restricted_days = parse_days(row["restricted_days"])
    available = parse_windows(row["available_times"])
    restricted = parse_windows(row["restricted_times"])

    windows = {}

    for offset, day in enumerate(WORK_DAYS):
        visit_date = WEEK_START + timedelta(days=offset)

        if earliest and visit_date < date.fromisoformat(earliest):
            continue
        if latest and visit_date > date.fromisoformat(latest):
            continue
        if day in restricted_days:
            continue

        if available:
            open_windows = [
                (max(start, WORK_START), min(end, WORK_END))
                for start, end in available.get(day, [])
                if start < WORK_END and end > WORK_START
            ]
        else:
            open_windows = [(WORK_START, WORK_END)]

        open_windows = subtract_windows(open_windows, restricted.get(day, []))

        if open_windows:
            windows[day] = open_windows

    return windows


def load_patients(path=PATIENTS_FILE):
    """Read patients.csv once and return {patient_id: Patient}."""
    patients = {}

    with Path(path).open(newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            patient_id = row["patient_id"]

            if patient_id in patients:
                raise ValueError(f"Duplicate patient ID: {patient_id}")

            patients[patient_id] = Patient(
                patient_id=patient_id,
                first_name=row["first_name"],
                last_name=row["last_name"],
                address=(
                    f"{row['street_address']}, {row['city']}, "
                    f"{row['state']} {row['zip_code']}"
                ),
                visit_type=row["visit_type"],
                restriction_reason=row["restriction_reason"],
                windows=build_windows(row),
                preferred_days=parse_days(row["preferred_days"]),
                preferred_times=parse_windows(row["preferred_times"]),
            )

    return patients
