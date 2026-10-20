import math
from datetime import date

import pytest

from clinician import Clinician
from insertion import build_schedule, regret
from patient import DAY_END, Patient, load_patients
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


def make_patient(patient_id, days, windows=None):
    return Patient(
        patient_id=patient_id,
        first_name="Test",
        last_name=patient_id,
        address="",
        visit_type="RA",
        windows={day: windows or ALL_DAY for day in days},
    )


def by_id(*patient_list):
    return {p.patient_id: p for p in patient_list}


# --- Regret ---

def test_regret_is_gap_between_two_cheapest_days():
    options = {"Mon": (2.0, 0, None), "Tue": (9.0, 0, None), "Wed": (5.0, 0, None)}
    assert regret(options) == 3.0


def test_single_option_has_infinite_regret():
    assert regret({"Mon": (2.0, 0, None)}) == math.inf


# --- Small hand-checked scenarios ---

def test_regret_protects_single_day_patient():
    # One visit per day. Cheapest-first could put B on Monday and strand A;
    # regret places A (Monday only) first.
    clinician = Clinician(work_days=["Mon", "Tue"], max_visits_per_day=1)
    patients = by_id(
        make_patient("A", ["Mon"]),
        make_patient("B", ["Mon", "Tue"]),
    )
    travel = LineTravel({"A": 5, "B": 1})
    result = build_schedule(patients, clinician, travel)
    assert result.routes == {"Mon": ["A"], "Tue": ["B"]}
    assert result.unscheduled == []


def test_high_regret_patient_placed_before_low_regret_patient():
    # HOME at 0. A (Mon only) at +10, B (Tue only) at -10.
    # C at +9: +0 min on Monday, +18 on Tuesday -> regret 18.
    # D at +1: +0 min on Monday, +2 on Tuesday -> regret 2.
    clinician = Clinician(work_days=["Mon", "Tue"], max_visits_per_day=2)
    patients = by_id(
        make_patient("A", ["Mon"]),
        make_patient("B", ["Tue"]),
        make_patient("C", ["Mon", "Tue"]),
        make_patient("D", ["Mon", "Tue"]),
    )
    travel = LineTravel({"A": 10, "B": -10, "C": 9, "D": 1})
    result = build_schedule(patients, clinician, travel)

    assert result.placement_order == ["A", "B", "C", "D"]
    assert result.routes["Mon"] == ["C", "A"]
    assert result.routes["Tue"] == ["D", "B"]


def test_impossible_patient_reported_not_dropped():
    clinician = Clinician(work_days=["Mon"])
    # 8:00-8:30 cannot hold a 60 min visit.
    patients = by_id(
        make_patient("A", ["Mon"]),
        make_patient("X", ["Mon"], windows=[(480, 510)]),
    )
    result = build_schedule(patients, clinician, LineTravel({"A": 1, "X": 2}))
    assert result.unscheduled == ["X"]
    assert result.routes == {"Mon": ["A"]}


def test_overflow_patients_reported():
    clinician = Clinician(work_days=["Mon"], max_visits_per_day=2)
    patients = by_id(*(make_patient(p, ["Mon"]) for p in "ABC"))
    result = build_schedule(patients, clinician, LineTravel({"A": 1, "B": 2, "C": 3}))
    assert len(result.routes["Mon"]) == 2
    assert len(result.unscheduled) == 1


# --- Real data ---

@pytest.fixture(scope="module")
def real():
    patients = load_patients(date(2026, 10, 19))
    travel = TravelTimes()
    clinician = Clinician()
    return patients, clinician, travel, build_schedule(patients, clinician, travel)


def test_every_patient_accounted_for_once(real):
    patients, _, _, result = real
    scheduled = [p for route in result.routes.values() for p in route]
    assert len(scheduled) == len(set(scheduled))
    assert sorted(scheduled + result.unscheduled) == sorted(patients)


def test_capacity_respected(real):
    _, clinician, _, result = real
    assert all(len(r) <= clinician.max_visits_per_day for r in result.routes.values())


def test_every_day_is_feasible(real):
    patients, clinician, travel, result = real
    for day, route in result.routes.items():
        assert evaluate_day(day, route, patients, clinician, travel).feasible


def test_patients_only_on_eligible_days(real):
    patients, _, _, result = real
    for day, route in result.routes.items():
        for patient_id in route:
            assert day in patients[patient_id].eligible_days


def test_mandatory_soc_days(real):
    _, _, _, result = real
    assert "102" in result.routes["Tue"]
    assert "112" in result.routes["Wed"]


def test_mandatory_patients_placed_first(real):
    _, _, _, result = real
    assert result.placement_order[:2] == ["102", "112"]
