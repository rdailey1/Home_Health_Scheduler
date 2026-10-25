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
    assert travel.miles("HOME", "107") == 7.94
    assert travel.minutes("HOME", "107") == 20.21


def test_matrix_is_directed(travel):
    assert travel.minutes("104", "112") == 0.93
    assert travel.minutes("112", "104") == 1.41


def test_same_location_is_zero(travel):
    assert travel.minutes("101", "101") == 0.0
    assert travel.miles("HOME", "HOME") == 0.0


def test_unknown_location_raises(travel):
    with pytest.raises(KeyError, match="No route from HOME to 999"):
        travel.minutes("HOME", "999")


def test_same_building_is_zero(travel):
    # 107 and 114 live at the same senior building.
    assert travel.minutes("107", "114") == 0.0
    assert travel.miles("114", "107") == 0.0


def test_different_addresses_are_positive(travel):
    patients = load_patients(date(2026, 10, 19))
    address = {pid: p.address for pid, p in patients.items()}

    for a in travel.locations:
        for b in travel.locations:
            if a != b and (a not in address or address.get(a) != address.get(b)):
                assert travel.minutes(a, b) > 0
                assert travel.miles(a, b) > 0
