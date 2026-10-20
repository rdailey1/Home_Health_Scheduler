from datetime import date

import pytest

from patient import load_patients
from travel import TravelTimes


@pytest.fixture(scope="module")
def travel():
    return TravelTimes()


def test_loads_all_directed_pairs(travel):
    # 21 locations, every ordered pair except self-to-self.
    assert len(travel) == 21 * 20


def test_covers_home_and_every_patient(travel):
    expected = {"HOME"} | set(load_patients(date(2026, 10, 19)))
    assert set(travel.locations) == expected


def test_known_values(travel):
    assert travel.miles("HOME", "107") == 4.81
    assert travel.minutes("HOME", "107") == 14.65


def test_matrix_is_directed(travel):
    assert travel.minutes("112", "113") == 2.69
    assert travel.minutes("113", "112") == 0.73


def test_same_location_is_zero(travel):
    assert travel.minutes("101", "101") == 0.0
    assert travel.miles("HOME", "HOME") == 0.0


def test_unknown_location_raises(travel):
    with pytest.raises(KeyError, match="No route from HOME to 999"):
        travel.minutes("HOME", "999")


def test_all_values_positive(travel):
    for a in travel.locations:
        for b in travel.locations:
            if a != b:
                assert travel.minutes(a, b) > 0
                assert travel.miles(a, b) > 0
