from datetime import date

import pytest

pytest.importorskip("ortools")  # benchmark-only dependency

from benchmark import optimal_week  # noqa: E402
from clinician import Clinician  # noqa: E402
from main import plan_week  # noqa: E402
from patient import DAY_END, Patient, load_patients  # noqa: E402
from schedule import evaluate_day  # noqa: E402
from travel import TravelTimes  # noqa: E402


class LineTravel:
    """Locations on a number line; drive minutes = distance between them."""

    def __init__(self, positions):
        self.positions = {"HOME": 0, **positions}

    def minutes(self, a, b):
        return abs(self.positions[a] - self.positions[b])

    def miles(self, a, b):
        return self.minutes(a, b)


def make_patient(patient_id, days=("Mon", "Tue")):
    return Patient(
        patient_id=patient_id,
        first_name="Test",
        last_name=patient_id,
        address="",
        visit_type="RA",
        windows={day: [(0, DAY_END)] for day in days},
    )


def test_small_week_groups_by_direction():
    # HOME at 0; A, C east and B, D west. Best: one direction per day (44).
    patients = {p: make_patient(p) for p in "ABCD"}
    travel = LineTravel({"A": 10, "B": -10, "C": 11, "D": -11})
    clinician = Clinician(work_days=["Mon", "Tue"], max_visits_per_day=2)

    week, proven, _ = optimal_week(patients, clinician, travel)

    assert proven
    assert week.drive_minutes == 44
    assert {frozenset(r) for r in week.routes.values()} == {
        frozenset("AC"), frozenset("BD"),
    }


def test_impossible_week_raises():
    # Three Monday-only patients, two visits allowed.
    patients = {p: make_patient(p, days=["Mon"]) for p in "ABC"}
    travel = LineTravel({"A": 1, "B": 2, "C": 3})
    clinician = Clinician(work_days=["Mon"], max_visits_per_day=2)

    with pytest.raises(RuntimeError, match="No complete week"):
        optimal_week(patients, clinician, travel)


# --- Real data ---

@pytest.fixture(scope="module")
def real():
    patients = load_patients(date(2026, 10, 19))
    clinician = Clinician()
    travel = TravelTimes()
    week, proven, _ = optimal_week(patients, clinician, travel)
    return patients, clinician, travel, week, proven


def test_optimum_is_proven_and_valid(real):
    patients, clinician, travel, week, proven = real
    assert proven

    scheduled = [p for route in week.routes.values() for p in route]
    assert sorted(scheduled) == sorted(patients)

    for day, route in week.routes.items():
        assert all(day in patients[p].eligible_days for p in route)
        assert evaluate_day(day, route, patients, clinician, travel).feasible


def test_heuristic_never_beats_optimum(real):
    patients, clinician, travel, week, _ = real
    stages, _ = plan_week(patients, clinician, travel)
    for _, schedule in stages:
        assert schedule.drive_minutes >= week.drive_minutes - 1e-6
