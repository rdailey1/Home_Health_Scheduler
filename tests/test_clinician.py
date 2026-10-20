import pytest

from clinician import Clinician
from visit_rules import VISIT_MINUTES, visit_duration


def test_default_clinician_matches_mvp():
    clinician = Clinician()
    assert clinician.work_days == ["Mon", "Tue", "Wed", "Thu", "Fri"]
    assert (clinician.start, clinician.end) == (480, 1020)
    assert clinician.max_visits_per_day == 4
    assert clinician.visit_buffer == 7
    assert clinician.start_increment == 30


def test_custom_schedule():
    clinician = Clinician(work_days=["Mon", "Thu"], start=540, end=900)
    assert clinician.work_days == ["Mon", "Thu"]


def test_default_work_days_not_shared_between_clinicians():
    a, b = Clinician(), Clinician()
    a.work_days.remove("Fri")
    assert "Fri" in b.work_days


@pytest.mark.parametrize("kwargs", [
    {"work_days": ["Sat"]},
    {"start": 900, "end": 600},
    {"end": 25 * 60},
    {"max_visits_per_day": 0},
    {"visit_buffer": -1},
    {"start_increment": 0},
])
def test_invalid_clinician_rejected(kwargs):
    with pytest.raises(ValueError):
        Clinician(**kwargs)


def test_visit_durations():
    assert visit_duration("SOC") == 90
    for visit_type in ["ROC", "RC", "RA", "DC"]:
        assert visit_duration(visit_type) == 60


def test_unknown_visit_type_rejected():
    with pytest.raises(ValueError, match="Unknown visit type"):
        visit_duration("XYZ")


def test_every_dataset_visit_type_has_a_duration():
    from datetime import date
    from patient import load_patients

    patients = load_patients(date(2026, 10, 19))
    assert {p.visit_type for p in patients.values()} <= set(VISIT_MINUTES)
