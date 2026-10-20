import pytest

from main import format_time, main


@pytest.mark.parametrize("minutes, expected", [
    (480, "8:00"), (557, "9:17"), (556.6, "9:17"), (1020, "17:00"),
])
def test_format_time(minutes, expected):
    assert format_time(minutes) == expected


def test_main_prints_every_day_and_totals(capsys):
    main()
    output = capsys.readouterr().out
    for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
        assert f"\n{day}  " in output
    assert "Week: 20 visits" in output
    assert "Unscheduled: none" in output
