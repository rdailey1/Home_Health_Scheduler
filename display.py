"""Plain-text formatting shared by the CLI (main.py) and the UI (app.py)."""

from datetime import timedelta

from patient import DAY_END, DAY_START, WEEKDAYS


def format_time(minutes):
    """Minutes since midnight -> 'H:MM' (24-hour), rounded to the minute."""
    hours, mins = divmod(round(minutes), 60)
    return f"{hours}:{mins:02d}"


def short_address(address):
    """'200 Lothrop St, Pittsburgh, PA 15213' -> '200 Lothrop St, 15213'."""
    street = address.split(",")[0]
    zip_code = address.split()[-1]
    return f"{street}, {zip_code}"


def format_window(start, end):
    """(600, 1440) -> 'from 10:00'; (0, 540) -> 'until 9:00'."""
    if start <= DAY_START and end >= DAY_END:
        return "any time"
    if start <= DAY_START:
        return f"until {format_time(end)}"
    if end >= DAY_END:
        return f"from {format_time(start)}"
    return f"{format_time(start)}-{format_time(end)}"


def format_availability(patient):
    """
    Describe the availability the scheduler actually uses, so a clinician
    can check it against the written restriction.
    """
    if all(patient.windows.get(day) == [(DAY_START, DAY_END)] for day in WEEKDAYS):
        return "Any weekday, any time"

    # Group days with identical times: 'Mon, Wed until 12:00, from 13:00'.
    days_by_times = {}
    for day in patient.eligible_days:
        times = ", ".join(format_window(s, e) for s, e in patient.windows[day])
        days_by_times.setdefault(times, []).append(day)

    parts = []
    for times, days in days_by_times.items():
        label = "Mon-Fri" if days == WEEKDAYS else ", ".join(days)
        parts.append(f"{label} {times}")

    return "; ".join(parts)


def day_label(day, week_start):
    """('Tue', Monday Oct 19) -> 'Tue Oct 20'."""
    date = week_start + timedelta(days=WEEKDAYS.index(day))
    return f"{day} {date:%b} {date.day}"


def format_swap(swap):
    """'Swapped 107 (Wed) and 109 (Fri): saves 5.5 min'."""
    return (
        f"Swapped {swap.first} ({swap.first_day}) and "
        f"{swap.second} ({swap.second_day}): saves {swap.saved_minutes:.1f} min"
    )
