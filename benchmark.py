"""
Exact benchmark: the best possible week under the scheduler's own rules.

Run on demand (not part of main.py or the app):
    pip install -r requirements-benchmark.txt
    python3 benchmark.py

Method: for each day, list every group of patients that can be seen that
day (up to the visit limit) with its driving in the best visit order,
using the same day simulation as the heuristic. Then choose one group per
day so every patient is seen exactly once with the least total driving
(set partitioning), solved and proven optimal by OR-Tools CP-SAT.

This only works because the instance is small: the number of groups
grows quickly with more patients or more visits per day, which is why
the app uses the heuristic.
"""

import time
from itertools import combinations

from ortools.sat.python import cp_model

from clinician import Clinician
from insertion import WeekSchedule
from main import WEEK_START, plan_week, print_stages, print_week
from patient import load_patients
from reorder import best_order
from travel import TravelTimes

# CP-SAT needs integer costs; drive minutes have two decimals.
SCALE = 100


def day_options(patients, clinician, travel):
    """{day: [(route, plan)]} for every feasible group, in its best order."""
    options = {}

    for day in clinician.work_days:
        eligible = sorted(p for p in patients if day in patients[p].windows)
        options[day] = []

        for size in range(clinician.max_visits_per_day + 1):
            for group in combinations(eligible, size):
                route, plan = best_order(
                    day, list(group), patients, clinician, travel
                )
                if plan.feasible:
                    options[day].append((route, plan))

    return options


def optimal_week(patients, clinician, travel, time_limit=60):
    """
    Return (WeekSchedule, proven_optimal, stats) for the week with the
    least driving that sees every patient exactly once.
    """
    started = time.perf_counter()
    options = day_options(patients, clinician, travel)
    enumerated = time.perf_counter()

    model = cp_model.CpModel()
    choose = {
        (day, i): model.new_bool_var(f"{day}_{i}")
        for day, day_routes in options.items()
        for i in range(len(day_routes))
    }

    # Exactly one group per day.
    for day, day_routes in options.items():
        model.add_exactly_one(choose[day, i] for i in range(len(day_routes)))

    # Every patient seen exactly once across the week.
    for patient_id in patients:
        model.add_exactly_one(
            choose[day, i]
            for day, day_routes in options.items()
            for i, (route, _) in enumerate(day_routes)
            if patient_id in route
        )

    model.minimize(sum(
        round(plan.drive_minutes * SCALE) * choose[day, i]
        for day, day_routes in options.items()
        for i, (_, plan) in enumerate(day_routes)
    ))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"No complete week found ({solver.status_name(status)})")

    routes, plans = {}, {}
    for day, day_routes in options.items():
        for i, (route, plan) in enumerate(day_routes):
            if solver.value(choose[day, i]):
                routes[day], plans[day] = route, plan

    stats = {
        "groups": sum(len(day_routes) for day_routes in options.values()),
        "enumerate_seconds": enumerated - started,
        "solve_seconds": solver.wall_time,
    }
    week = WeekSchedule(routes=routes, plans=plans)
    return week, status == cp_model.OPTIMAL, stats


def main():
    patients = load_patients(WEEK_START)
    clinician = Clinician()
    travel = TravelTimes()

    stages, _ = plan_week(patients, clinician, travel)
    optimum, proven, stats = optimal_week(patients, clinician, travel)
    heuristic = stages[-1][1]

    print_week(optimum, patients)
    print_stages([*stages, ("Optimal" if proven else "Best found", optimum)])

    gap = heuristic.drive_minutes - optimum.drive_minutes
    print(
        f"\nHeuristic is {gap:.1f} min "
        f"({gap / optimum.drive_minutes:.1%}) above the "
        f"{'proven optimum' if proven else 'best week found'}."
    )
    print(
        f"{stats['groups']:,} day groups enumerated in "
        f"{stats['enumerate_seconds']:.1f} s; solved in "
        f"{stats['solve_seconds']:.1f} s."
    )


if __name__ == "__main__":
    main()
