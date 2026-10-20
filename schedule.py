import math
from dataclasses import dataclass, field

from visit_rules import visit_duration

HOME = "HOME"


@dataclass
class Visit:
    """One scheduled visit. Times are minutes since midnight."""

    patient_id: str
    arrival: float  # after driving and parking
    start: int
    end: int


@dataclass
class DayPlan:
    day: str
    feasible: bool
    visits: list[Visit] = field(default_factory=list)
    drive_minutes: float = 0.0
    drive_miles: float = 0.0
    reason: str = ""  # why the day is infeasible


def round_up(time, increment):
    """Round time up to the next multiple of increment."""
    return math.ceil(time / increment) * increment


def earliest_start(arrival, windows, duration, clinician):
    """
    Return the earliest increment-aligned start at or after arrival where
    the whole visit fits inside one patient window and clinician hours,
    or None if no window fits.
    """
    for window_start, window_end in sorted(windows):
        start = round_up(
            max(arrival, window_start, clinician.start),
            clinician.start_increment,
        )

        if start + duration <= min(window_end, clinician.end):
            return start

    return None


def evaluate_day(day, patient_ids, patients, clinician, travel):
    """
    Simulate one day: HOME -> patients in the given order -> HOME.

    The first visit may start at clinician.start (the drive from HOME is
    outside work hours). Each later visit starts after driving, parking,
    and rounding up to the start increment, waiting if the patient's
    window has not opened. Every visit must end within the patient's
    window and by clinician.end. The drive home is outside work hours.
    Driving minutes and miles always include both HOME legs.
    """
    if len(set(patient_ids)) != len(patient_ids):
        raise ValueError(f"Duplicate patient in {day} route: {patient_ids}")

    route = [HOME, *patient_ids, HOME]
    plan = DayPlan(
        day=day,
        feasible=True,
        drive_minutes=sum(travel.minutes(a, b) for a, b in zip(route, route[1:])),
        drive_miles=sum(travel.miles(a, b) for a, b in zip(route, route[1:])),
    )

    if not patient_ids:
        return plan

    if day not in clinician.work_days:
        return infeasible(plan, f"Clinician does not work {day}")

    if len(patient_ids) > clinician.max_visits_per_day:
        return infeasible(
            plan,
            f"{len(patient_ids)} visits exceeds limit of "
            f"{clinician.max_visits_per_day}",
        )

    previous = HOME
    time = None

    for patient_id in patient_ids:
        patient = patients[patient_id]
        windows = patient.windows.get(day)

        if not windows:
            return infeasible(plan, f"{patient_id} is not available {day}")

        if previous == HOME:
            arrival = clinician.start
        else:
            arrival = (
                time
                + travel.minutes(previous, patient_id)
                + clinician.visit_buffer
            )

        duration = visit_duration(patient.visit_type)
        start = earliest_start(arrival, windows, duration, clinician)

        if start is None:
            return infeasible(
                plan, f"{patient_id} visit does not fit any window on {day}"
            )

        plan.visits.append(Visit(patient_id, arrival, start, start + duration))
        time = start + duration
        previous = patient_id

    return plan


def infeasible(plan, reason):
    plan.feasible = False
    plan.reason = reason
    return plan
