from dataclasses import dataclass
from itertools import combinations

from insertion import WeekSchedule
from reorder import TOLERANCE, best_order, reorder_week


@dataclass
class Swap:
    """Patient `first` moved from `first_day` to `second_day`, and vice versa."""

    first: str
    first_day: str
    second: str
    second_day: str
    saved_minutes: float


def best_swap(routes, plans, patients, clinician, travel):
    """
    Try exchanging every pair of patients on different days. Each changed
    day is re-ordered exactly (best_order), so a swap is judged by the best
    possible routes it allows. Return (swap, new routes/plans) for the swap
    that saves the most driving, or None if no swap helps.
    """
    best = None

    for day_a, day_b in combinations(routes, 2):
        for first in routes[day_a]:
            if day_b not in patients[first].windows:
                continue

            for second in routes[day_b]:
                if day_a not in patients[second].windows:
                    continue

                new_a = [p for p in routes[day_a] if p != first] + [second]
                route_a, plan_a = best_order(
                    day_a, new_a, patients, clinician, travel
                )
                if not plan_a.feasible:
                    continue

                new_b = [p for p in routes[day_b] if p != second] + [first]
                route_b, plan_b = best_order(
                    day_b, new_b, patients, clinician, travel
                )
                if not plan_b.feasible:
                    continue

                saved = (
                    plans[day_a].drive_minutes + plans[day_b].drive_minutes
                    - plan_a.drive_minutes - plan_b.drive_minutes
                )

                if saved > TOLERANCE and (best is None or saved > best[0].saved_minutes):
                    swap = Swap(first, day_a, second, day_b, saved)
                    best = (swap, {day_a: (route_a, plan_a), day_b: (route_b, plan_b)})

    return best


def swap_between_days(schedule, patients, clinician, travel):
    """
    Local search: repeatedly apply the single swap that saves the most
    driving until no swap helps (a local optimum, not necessarily the best
    possible week). Days keep their visit counts. Returns the improved
    WeekSchedule and the swaps made, in order.
    """
    start = reorder_week(schedule, patients, clinician, travel)
    routes = {day: list(route) for day, route in start.routes.items()}
    plans = dict(start.plans)
    swaps = []

    while (found := best_swap(routes, plans, patients, clinician, travel)):
        swap, changed = found
        for day, (route, plan) in changed.items():
            routes[day], plans[day] = route, plan
        swaps.append(swap)

    improved = WeekSchedule(
        routes=routes,
        plans=plans,
        unscheduled=list(schedule.unscheduled),
        placement_order=list(schedule.placement_order),
    )
    return improved, swaps
