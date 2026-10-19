import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MATRIX_FILE = ROOT / "data" / "distance_matrix.csv"


class TravelTimes:
    """
    Directed travel lookups between location IDs ("HOME", "101", ...).

    The scheduler should only call minutes() and miles(), so the storage or
    source (e.g. departure-time-aware estimates) can change behind them.
    """

    def __init__(self, path=MATRIX_FILE):
        # (from_id, to_id) -> (miles, minutes)
        self._routes = {}

        with Path(path).open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                key = (row["from_id"], row["to_id"])

                if key in self._routes:
                    raise ValueError(f"Duplicate route: {key}")

                self._routes[key] = (
                    float(row["distance_miles"]),
                    float(row["base_travel_minutes"]),
                )

        self.locations = sorted({origin for origin, _ in self._routes})

    def _lookup(self, from_id, to_id):
        if from_id == to_id:
            return (0.0, 0.0)

        try:
            return self._routes[(from_id, to_id)]
        except KeyError:
            raise KeyError(f"No route from {from_id} to {to_id}") from None

    def miles(self, from_id, to_id):
        return self._lookup(from_id, to_id)[0]

    def minutes(self, from_id, to_id):
        return self._lookup(from_id, to_id)[1]

    def __len__(self):
        return len(self._routes)
