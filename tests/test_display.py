from datetime import date

import pytest

from display import day_label, format_availability, format_window
from patient import DAY_END, Patient


def make_patient(windows):
    return Patient(
        patient_id="A",
        first_name="Test",
        last_name="A",
        address="",
        visit_type="RA",
        windows=windows,
    )


@pytest.mark.parametrize("start, end, expected", [
    (0, DAY_END, "any time"),
    (0, 540, "until 9:00"),
    (600, DAY_END, "from 10:00"),
    (600, 900, "10:00-15:00"),
])
def test_format_window(start, end, expected):
    assert format_window(start, end) == expected


def test_unrestricted_patient():
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    patient = make_patient({day: [(0, DAY_END)] for day in days})
    assert format_availability(patient) == "Any weekday, any time"


def test_same_times_every_weekday_collapse():
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    patient = make_patient({day: [(600, DAY_END)] for day in days})
    assert format_availability(patient) == "Mon-Fri from 10:00"


def test_days_grouped_by_times():
    patient = make_patient({
        "Mon": [(0, 720), (780, DAY_END)],
        "Wed": [(0, 720), (780, DAY_END)],
        "Thu": [(600, 900)],
    })
    assert format_availability(patient) == (
        "Mon, Wed until 12:00, from 13:00; Thu 10:00-15:00"
    )


def test_day_label():
    assert day_label("Tue", date(2026, 10, 19)) == "Tue Oct 20"
