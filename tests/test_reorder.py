from datetime import date

import pytest

from clinician import Clinician
from insertion import build_schedule
from patient import DAY_END, Patient, load_patients
from reorder import best_order, reorder_week
from schedule import evaluate_day
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


def make_patients(windows=None):
    windows = windows or {}
    return {
        p: Patient(
            patient_id=p,
            first_name="Test",
            last_name=p,
            address="",
            visit_type="RA",
            windows={"Mon": windows.get(p, ALL_DAY)},
        )
        for p in "ABC"
    }


# HOME at 0. A at +1, B at -1, C at +2.
# A, B, C drives 1 + 2 + 3 + 2 = 8; A, C, B drives 1 + 1 + 3 + 1 = 6.
TRAVEL = LineTravel({"A": 1, "B": -1, "C": 2})


def test_finds_shorter_order():
    route, plan = best_order(
        "Mon", ["A", "B", "C"], make_patients(), Clinician(), TRAVEL
    )
    # Several orders tie at 6; the first one found (A, C, B) is kept.
    assert plan.drive_minutes == 6
    assert route == ["A", "C", "B"]


def test_respects_windows():
    # C only fits 8:00-8:45, so it must go first: C, A, B (also 6).
    patients = make_patients({"C": [(480, 525)]})
    route, plan = best_order("Mon", ["A", "B", "C"], patients, Clinician(), TRAVEL)
    assert plan.feasible
    assert route == ["C", "A", "B"]


def test_tie_keeps_original_order():
    # Out and back on one side of HOME: A, C and C, A both drive 4.
    route, _ = best_order("Mon", ["C", "A"], make_patients(), Clinician(), TRAVEL)
    assert route == ["C", "A"]


@pytest.mark.parametrize("route", [[], ["A"]])
def test_short_routes_unchanged(route):
    result, plan = best_order("Mon", route, make_patients(), Clinician(), TRAVEL)
    assert result == route
    assert plan.feasible


# --- Real data ---

@pytest.fixture(scope="module")
def real():
    patients = load_patients(date(2026, 10, 19))
    travel = TravelTimes()
    clinician = Clinician()
    inserted = build_schedule(patients, clinician, travel)
    reordered = reorder_week(inserted, patients, clinician, travel)
    return patients, clinician, travel, inserted, reordered


def test_same_patients_each_day(real):
    *_, inserted, reordered = real
    for day in inserted.routes:
        assert sorted(reordered.routes[day]) == sorted(inserted.routes[day])
    assert reordered.unscheduled == inserted.unscheduled


def test_never_longer_and_still_feasible(real):
    patients, clinician, travel, inserted, reordered = real
    for day, route in reordered.routes.items():
        plan = evaluate_day(day, route, patients, clinician, travel)
        assert plan.feasible
        assert plan.drive_minutes <= inserted.plans[day].drive_minutes + 1e-9


def test_does_not_modify_input(real):
    patients, clinician, travel, inserted, _ = real
    before = {day: list(route) for day, route in inserted.routes.items()}
    reorder_week(inserted, patients, clinician, travel)
    assert inserted.routes == before
