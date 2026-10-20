import math
from dataclasses import dataclass, field

from schedule import evaluate_day


@dataclass
class WeekSchedule:
    routes: dict[str, list[str]]  # day -> patient IDs in visit order
    plans: dict  # day -> DayPlan
    unscheduled: list[str] = field(default_factory=list)
    placement_order: list[str] = field(default_factory=list)

    @property
    def drive_minutes(self):
        return sum(plan.drive_minutes for plan in self.plans.values())

    @property
    def drive_miles(self):
        return sum(plan.drive_miles for plan in self.plans.values())


def best_insertion_per_day(patient, routes, plans, patients, clinician, travel):
    """
    For each day the patient could go on, return the cheapest feasible
    insertion as {day: (added_minutes, position, plan)}.
    """
    options = {}

    for day, route in routes.items():
        if day not in patient.windows:
            continue
        if len(route) >= clinician.max_visits_per_day:
            continue

        for position in range(len(route) + 1):
            candidate = route[:position] + [patient.patient_id] + route[position:]
            plan = evaluate_day(day, candidate, patients, clinician, travel)

            if not plan.feasible:
                continue

            added = plan.drive_minutes - plans[day].drive_minutes

            if day not in options or added < options[day][0]:
                options[day] = (added, position, plan)

    return options


def regret(options):
    """Second-cheapest day minus cheapest day; infinite with one option."""
    costs = sorted(added for added, _, _ in options.values())
    return costs[1] - costs[0] if len(costs) > 1 else math.inf


def build_schedule(patients, clinician, travel):
    """
    Regret insertion. Each step evaluates every unplaced patient's cheapest
    feasible insertion on each day, then places the patient whose best day
    beats their second-best day by the most. Ties go to the patient with
    fewer eligible days, then the lower ID. A patient with no feasible
    insertion is unscheduled: days only fill up, so options never return.
    """
    routes = {day: [] for day in clinician.work_days}
    plans = {
        day: evaluate_day(day, [], patients, clinician, travel)
        for day in routes
    }
    schedule = WeekSchedule(routes=routes, plans=plans)
    unplaced = set(patients)

    while unplaced:
        best = None

        for patient_id in sorted(unplaced):
            patient = patients[patient_id]
            options = best_insertion_per_day(
                patient, routes, plans, patients, clinician, travel
            )

            if not options:
                schedule.unscheduled.append(patient_id)
                continue

            key = (-regret(options), len(patient.eligible_days), patient_id)

            if best is None or key < best[0]:
                best = (key, patient_id, options)

        unplaced -= set(schedule.unscheduled)

        if best is None:
            break

        _, patient_id, options = best
        day = min(options, key=lambda d: options[d][0])
        _, position, plan = options[day]

        routes[day].insert(position, patient_id)
        plans[day] = plan
        schedule.placement_order.append(patient_id)
        unplaced.remove(patient_id)

    return schedule
