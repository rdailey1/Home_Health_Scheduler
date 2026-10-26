from datetime import date

import pytest

from clinician import Clinician
from insertion import WeekSchedule, build_schedule
from patient import DAY_END, Patient, load_patients
from schedule import evaluate_day
from swaps import swap_between_days
from travel import TravelTimes

ALL_DAY = [(0, DAY_END)]


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
        windows={day: ALL_DAY for day in days},
    )


def week(routes, patients, clinician, travel):
    plans = {
        day: evaluate_day(day, route, patients, clinician, travel)
        for day, route in routes.items()
    }
    return WeekSchedule(routes=routes, plans=plans)


# HOME at 0. A, C east (+10, +11); B, D west (-10, -11).
# Each day going both directions drives 40 + 44 = 84 total;
# one direction per day drives 22 + 22 = 44.
TRAVEL = LineTravel({"A": 10, "B": -10, "C": 11, "D": -11})
CLINICIAN = Clinician(work_days=["Mon", "Tue"], max_visits_per_day=2)


def test_swap_groups_patients_by_direction():
    patients = {p: make_patient(p) for p in "ABCD"}
    start = week({"Mon": ["A", "B"], "Tue": ["C", "D"]}, patients, CLINICIAN, TRAVEL)

    result, swaps = swap_between_days(start, patients, CLINICIAN, TRAVEL)

    assert result.drive_minutes == 44
    assert {frozenset(r) for r in result.routes.values()} == {
        frozenset("AC"), frozenset("BD"),
    }
    assert len(swaps) == 1
    assert swaps[0].saved_minutes == 40


def test_swap_respects_eligible_days():
    # B (Mon only) and D (Tue only) cannot move, so the only allowed swap
    # (A with C) still leaves each day going both directions: no gain.
    patients = {p: make_patient(p) for p in "AC"}
    patients["B"] = make_patient("B", days=["Mon"])
    patients["D"] = make_patient("D", days=["Tue"])
    start = week({"Mon": ["A", "B"], "Tue": ["C", "D"]}, patients, CLINICIAN, TRAVEL)

    result, swaps = swap_between_days(start, patients, CLINICIAN, TRAVEL)

    assert "B" in result.routes["Mon"]
    assert "D" in result.routes["Tue"]
    assert swaps == []


# --- Real data ---

@pytest.fixture(scope="module")
def real():
    patients = load_patients(date(2026, 10, 19))
    travel = TravelTimes()
    clinician = Clinician()
    inserted = build_schedule(patients, clinician, travel)
    swapped, swaps = swap_between_days(inserted, patients, clinician, travel)
    return patients, clinician, travel, inserted, swapped, swaps


def test_never_longer_and_still_valid(real):
    patients, clinician, travel, inserted, swapped, _ = real
    assert swapped.drive_minutes <= inserted.drive_minutes

    scheduled = [p for route in swapped.routes.values() for p in route]
    assert sorted(scheduled) == sorted(inserted_ids(inserted))

    for day, route in swapped.routes.items():
        assert len(route) == len(inserted.routes[day])
        assert all(day in patients[p].eligible_days for p in route)
        assert evaluate_day(day, route, patients, clinician, travel).feasible


def test_savings_add_up(real):
    *_, inserted, swapped, swaps = real
    assert swaps
    # Swaps start from the reordered week, so their savings are counted
    # from there; the total must still not exceed the full improvement.
    assert sum(s.saved_minutes for s in swaps) <= (
        inserted.drive_minutes - swapped.drive_minutes + 1e-9
    )


def test_same_building_patients_end_up_together(real):
    *_, swapped, _ = real
    days = {day for day, route in swapped.routes.items() if {"107", "114"} & set(route)}
    assert len(days) == 1


def test_mandatory_soc_days_kept(real):
    *_, swapped, _ = real
    assert "102" in swapped.routes["Tue"]
    assert "112" in swapped.routes["Wed"]


def inserted_ids(schedule):
    return [p for route in schedule.routes.values() for p in route]
