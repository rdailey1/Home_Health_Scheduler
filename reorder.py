from itertools import permutations

from insertion import WeekSchedule
from schedule import evaluate_day

# Ignore float noise when comparing drive totals.
TOLERANCE = 1e-9


def best_order(day, route, patients, clinician, travel):
    """
    Try every visit order for one day (at most 4! = 24 with 4 visits) and
    return (route, plan) for the feasible order with the least driving.
    The original order is tried first and only replaced by a strictly
    shorter one, so ties keep the existing order.
    """
    best_route = list(route)
    best_plan = evaluate_day(day, best_route, patients, clinician, travel)

    for order in permutations(route):
        plan = evaluate_day(day, list(order), patients, clinician, travel)

        if not plan.feasible:
            continue

        if (
            not best_plan.feasible
            or plan.drive_minutes < best_plan.drive_minutes - TOLERANCE
        ):
            best_route, best_plan = list(order), plan

    return best_route, best_plan


def reorder_week(schedule, patients, clinician, travel):
    """
    Return a new WeekSchedule with each day's visits in their best order.
    Days keep the same patients; only the order within a day changes.
    """
    routes = {}
    plans = {}

    for day, route in schedule.routes.items():
        routes[day], plans[day] = best_order(
            day, route, patients, clinician, travel
        )

    return WeekSchedule(
        routes=routes,
        plans=plans,
        unscheduled=list(schedule.unscheduled),
        placement_order=list(schedule.placement_order),
    )
