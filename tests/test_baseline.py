import random
from datetime import date

import pytest

from baseline import random_schedule, sample_schedules
from clinician import Clinician
from patient import DAY_END, Patient, load_patients
from schedule import evaluate_day
from travel import TravelTimes


def make_patient(patient_id, windows):
    return Patient(
        patient_id=patient_id,
        first_name="Test",
        last_name=patient_id,
        address="",
        visit_type="RA",
        windows={"Mon": windows},
    )


class FakeTravel:
    def minutes(self, a, b):
        return 0.0 if a == b else 10.0

    def miles(self, a, b):
        return self.minutes(a, b)


def test_impossible_week_raises():
    # 8:00-8:30 cannot hold a 45 min visit.
    patients = {"X": make_patient("X", [(480, 510)])}
    with pytest.raises(RuntimeError, match="No valid random schedule"):
        random_schedule(
            patients, Clinician(work_days=["Mon"]), FakeTravel(),
            random.Random(0), max_attempts=5,
        )


def test_small_week_places_everyone():
    patients = {p: make_patient(p, [(0, DAY_END)]) for p in "ABC"}
    week = random_schedule(
        patients, Clinician(work_days=["Mon"]), FakeTravel(), random.Random(0)
    )
    assert sorted(week.routes["Mon"]) == ["A", "B", "C"]


# --- Real data ---

@pytest.fixture(scope="module")
def real():
    patients = load_patients(date(2026, 10, 19))
    travel = TravelTimes()
    clinician = Clinician()
    weeks = sample_schedules(patients, clinician, travel, samples=20)
    return patients, clinician, travel, weeks


def test_every_random_week_is_valid(real):
    patients, clinician, travel, weeks = real
    for week in weeks:
        scheduled = [p for route in week.routes.values() for p in route]
        assert sorted(scheduled) == sorted(patients)

        for day, route in week.routes.items():
            assert len(route) <= clinician.max_visits_per_day
            assert all(day in patients[p].eligible_days for p in route)
            assert evaluate_day(day, route, patients, clinician, travel).feasible


def test_same_seed_same_weeks(real):
    patients, clinician, travel, weeks = real
    again = sample_schedules(patients, clinician, travel, samples=20)
    assert [w.routes for w in again] == [w.routes for w in weeks]


def test_weeks_vary(real):
    *_, weeks = real
    assert len({w.drive_minutes for w in weeks}) > 1
