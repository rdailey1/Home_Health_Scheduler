from datetime import date

import pytest

from clinician import Clinician
from patient import DAY_END, Patient, load_patients
from schedule import evaluate_day, round_up
from travel import TravelTimes

ALL_DAY = [(0, DAY_END)]


class FakeTravel:
    """Every drive takes the same time, so timelines are easy to reason about."""

    def __init__(self, minutes=10.0, miles=2.0):
        self._minutes = minutes
        self._miles = miles

    def minutes(self, a, b):
        return 0.0 if a == b else self._minutes

    def miles(self, a, b):
        return 0.0 if a == b else self._miles


def make_patient(patient_id, visit_type="RA", windows=None, day="Mon", address=""):
    return Patient(
        patient_id=patient_id,
        first_name="Test",
        last_name=patient_id,
        address=address,
        visit_type=visit_type,
        windows={day: windows if windows is not None else ALL_DAY},
    )


def run(patient_list, day="Mon", clinician=None, travel=None):
    patients = {p.patient_id: p for p in patient_list}
    return evaluate_day(
        day,
        [p.patient_id for p in patient_list],
        patients,
        clinician or Clinician(),
        travel or FakeTravel(),
    )


def starts(plan):
    return [(v.start, v.end) for v in plan.visits]


# --- Rounding ---

@pytest.mark.parametrize("time, expected", [
    (540, 540), (540.5, 570), (557, 570), (570, 570), (571, 600),
])
def test_round_up_to_half_hour(time, expected):
    assert round_up(time, 30) == expected


# --- Day simulation (fake travel: 10 min drives, 2 mi) ---

def test_empty_day_is_feasible_with_no_driving():
    plan = run([])
    assert plan.feasible
    assert plan.visits == []
    assert plan.drive_minutes == 0


def test_first_visit_starts_at_clinician_start():
    # Drive from HOME is outside work hours; no buffer before the first visit.
    plan = run([make_patient("A")])
    assert starts(plan) == [(480, 525)]


def test_driving_includes_both_home_legs():
    plan = run([make_patient("A"), make_patient("B")])
    assert plan.drive_minutes == 30  # HOME->A, A->B, B->HOME
    assert plan.drive_miles == 6


def test_next_visit_rounds_up_to_half_hour():
    # A ends 8:45; 10 min drive + 7 min parking -> arrive 9:02 -> start 9:30.
    plan = run([make_patient("A"), make_patient("B")])
    assert plan.visits[1].arrival == 542
    assert starts(plan) == [(480, 525), (570, 615)]


def test_arrival_on_the_half_hour_is_not_pushed_back():
    # 8 min drive + 7 min parking from 8:45 -> exactly 9:00.
    plan = run([make_patient("A"), make_patient("B")], travel=FakeTravel(8))
    assert plan.visits[1].start == 540


def test_waits_for_window_to_open():
    plan = run([make_patient("A", windows=[(660, DAY_END)])])
    assert starts(plan) == [(660, 705)]


def test_uses_later_window_when_earlier_one_is_too_short():
    # 8:00-8:30 cannot hold a 45 min visit; 10:00-12:00 can.
    plan = run([make_patient("A", windows=[(480, 510), (600, 720)])])
    assert starts(plan) == [(600, 645)]


def test_visit_must_end_within_window():
    plan = run([make_patient("A", windows=[(480, 510)])])
    assert not plan.feasible
    assert "does not fit" in plan.reason


def test_visit_must_end_by_clinician_end():
    clinician = Clinician(start=480, end=600)
    # A 8:00-8:45, B arrives 9:02 -> 9:30-10:15, past 10:00.
    plan = run([make_patient("A"), make_patient("B")], clinician=clinician)
    assert not plan.feasible
    assert "B" in plan.reason


def test_window_opening_off_increment_rounds_up():
    plan = run([make_patient("A", windows=[(615, DAY_END)])])  # opens 10:15
    assert plan.visits[0].start == 630


def test_soc_lasts_75_minutes():
    plan = run([make_patient("A", visit_type="SOC")])
    assert starts(plan) == [(480, 555)]


def test_same_address_skips_parking():
    # A ends 8:45; no drive or parking -> B starts 9:00 (next half hour).
    a = make_patient("A", address="2121 Centre Ave")
    b = make_patient("B", address="2121 Centre Ave")
    plan = run([a, b], travel=FakeTravel(0))
    assert plan.visits[1].arrival == 525
    assert plan.visits[1].start == 540


def test_different_address_keeps_parking():
    a = make_patient("A", address="2121 Centre Ave")
    b = make_patient("B", address="510 Protectory Pl")
    plan = run([a, b], travel=FakeTravel(0))
    assert plan.visits[1].arrival == 532


def test_too_many_visits_is_infeasible():
    plan = run([make_patient(str(i)) for i in range(5)])
    assert not plan.feasible
    assert "exceeds limit" in plan.reason


def test_not_a_work_day_is_infeasible():
    clinician = Clinician(work_days=["Tue"])
    plan = run([make_patient("A")], clinician=clinician)
    assert not plan.feasible


def test_patient_unavailable_that_day_is_infeasible():
    plan = run([make_patient("A", day="Tue")], day="Mon")
    assert not plan.feasible
    assert "not available" in plan.reason


def test_duplicate_patient_rejected():
    patient = make_patient("A")
    with pytest.raises(ValueError):
        evaluate_day("Mon", ["A", "A"], {"A": patient}, Clinician(), FakeTravel())


# --- Real data: Tuesday with 102 (SOC, from 9:00) and 101 ---

@pytest.fixture(scope="module")
def real():
    return load_patients(date(2026, 10, 19)), TravelTimes()


def test_real_tuesday_101_then_102(real):
    patients, travel = real
    plan = evaluate_day("Tue", ["101", "102"], patients, Clinician(), travel)
    assert plan.feasible
    # 101 8:00-8:45; arrive 102 ~8:53, not before 9:00 -> 9:00-10:15 (SOC).
    assert starts(plan) == [(480, 525), (540, 615)]
    assert plan.drive_minutes == pytest.approx(
        travel.minutes("HOME", "101")
        + travel.minutes("101", "102")
        + travel.minutes("102", "HOME")
    )


def test_real_tuesday_102_then_101(real):
    patients, travel = real
    plan = evaluate_day("Tue", ["102", "101"], patients, Clinician(), travel)
    assert plan.feasible
    # 102 cannot start before 9:00 -> 9:00-10:15; 101 arrives ~10:23 -> 10:30.
    assert starts(plan) == [(540, 615), (630, 675)]


def test_real_dialysis_patient_not_seen_monday(real):
    patients, travel = real
    plan = evaluate_day("Mon", ["106"], patients, Clinician(), travel)
    assert not plan.feasible
