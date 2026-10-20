from datetime import date

import pytest

from patient import (
    DAY_END,
    DAY_START,
    build_windows,
    load_patients,
    parse_windows,
    subtract_windows,
    to_minutes,
)

WEEK_START = date(2026, 10, 19)
ALL_DAY = [(DAY_START, DAY_END)]


def make_row(**overrides):
    """A patients.csv row with no restrictions, overridable per test."""
    row = {
        "earliest_visit_date": "",
        "latest_visit_date": "",
        "restricted_days": "",
        "restricted_times": "",
        "available_times": "",
    }
    row.update(overrides)
    return row


@pytest.fixture(scope="module")
def patients():
    return load_patients(WEEK_START)


# --- Parsing helpers ---

def test_to_minutes():
    assert to_minutes("08:00") == 480
    assert to_minutes("14:30") == 870


def test_parse_windows_groups_by_day():
    assert parse_windows("Mon:08:00-10:00|Mon:12:00-13:00|Wed:09:00-11:00") == {
        "Mon": [(480, 600), (720, 780)],
        "Wed": [(540, 660)],
    }


def test_parse_windows_empty():
    assert parse_windows("") == {}


@pytest.mark.parametrize("value", ["Sat:08:00-10:00", "Mon:10:00-09:00"])
def test_parse_windows_rejects_bad_input(value):
    with pytest.raises(ValueError):
        parse_windows(value)


# --- Window subtraction ---

def test_subtract_splits_window():
    assert subtract_windows([(480, 1020)], [(720, 780)]) == [(480, 720), (780, 1020)]


def test_subtract_trims_start():
    assert subtract_windows([(480, 1020)], [(480, 600)]) == [(600, 1020)]


def test_subtract_non_overlapping_block_is_ignored():
    assert subtract_windows([(600, 900)], [(480, 540)]) == [(600, 900)]


def test_subtract_full_block_removes_window():
    assert subtract_windows([(600, 900)], [(480, 1020)]) == []


# --- Availability rules (build_windows) ---

def test_no_restrictions_means_all_week_all_day():
    windows = build_windows(make_row(), WEEK_START)
    assert windows == {day: ALL_DAY for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]}


def test_available_times_excludes_unlisted_days():
    windows = build_windows(make_row(available_times="Tue:10:00-15:00"), WEEK_START)
    assert windows == {"Tue": [(600, 900)]}


def test_available_times_not_limited_by_clinician_hours():
    # Clinician hours are applied by the scheduler, not the patient model.
    windows = build_windows(make_row(available_times="Mon:07:00-18:00"), WEEK_START)
    assert windows == {"Mon": [(420, 1080)]}


def test_restricted_times_subtracted_from_available_times():
    windows = build_windows(make_row(
        available_times="Tue:10:00-15:00",
        restricted_times="Tue:12:00-13:00",
    ), WEEK_START)
    assert windows == {"Tue": [(600, 720), (780, 900)]}


def test_restricted_days_override_available_times():
    windows = build_windows(make_row(
        available_times="Tue:10:00-15:00|Thu:10:00-15:00",
        restricted_days="Thu",
    ), WEEK_START)
    assert windows == {"Tue": [(600, 900)]}


def test_fully_restricted_day_is_dropped():
    windows = build_windows(make_row(restricted_times="Mon:00:00-24:00"), WEEK_START)
    assert "Mon" not in windows


def test_visit_date_window_limits_days():
    # Week starts Mon 2026-10-19; Tue-Thu is 10-20 to 10-22.
    windows = build_windows(make_row(
        earliest_visit_date="2026-10-20",
        latest_visit_date="2026-10-22",
    ), WEEK_START)
    assert list(windows) == ["Tue", "Wed", "Thu"]


# --- Real dataset ---

def test_week_start_must_be_monday():
    with pytest.raises(ValueError, match="Monday"):
        load_patients(date(2026, 10, 20))


def test_loads_all_patients(patients):
    assert len(patients) == 20
    assert set(patients) == {str(i) for i in range(101, 121)}


def test_soc_102_mandatory_tuesday_after_nine(patients):
    assert patients["102"].windows == {"Tue": [(540, DAY_END)]}


def test_soc_112_mandatory_wednesday_after_nine(patients):
    assert patients["112"].windows == {"Wed": [(540, DAY_END)]}


def test_dialysis_106_tue_thu_only(patients):
    assert patients["106"].windows == {
        "Tue": [(600, 900)],
        "Thu": [(600, 900)],
    }


def test_rc_103_window_and_lunch(patients):
    # RC window closes Wed 10-21; Tuesday restricted; lunch blocked Mon/Wed.
    lunch_split = [(DAY_START, 720), (780, DAY_END)]
    assert patients["103"].windows == {"Mon": lunch_split, "Wed": lunch_split}


def test_105_no_visits_before_ten(patients):
    assert all(
        windows == [(600, DAY_END)] for windows in patients["105"].windows.values()
    )
    assert len(patients["105"].eligible_days) == 5


def test_preferences_parsed_separately_from_windows(patients):
    patient = patients["106"]
    assert patient.preferred_times == {
        "Tue": [(720, 900)],
        "Thu": [(720, 900)],
    }
    # Preferences must not narrow hard availability.
    assert patient.windows["Tue"] == [(600, 900)]


def test_most_constrained_patients(patients):
    by_days = sorted(patients.values(), key=lambda p: len(p.eligible_days))
    assert [p.patient_id for p in by_days[:2]] == ["102", "112"]
