import random

from insertion import WeekSchedule
from schedule import evaluate_day

SEED = 0


def random_schedule(patients, clinician, travel, rng, max_attempts=1000):
    """
    Build one valid week with no optimization: take patients in random
    order and put each in a random feasible (day, position). If someone
    cannot be placed, start over. Every result respects all restrictions,
    so it is a fair "no routing effort" baseline.
    """
    for _ in range(max_attempts):
        routes = {day: [] for day in clinician.work_days}
        plans = {
            day: evaluate_day(day, [], patients, clinician, travel)
            for day in routes
        }
        order = sorted(patients)
        rng.shuffle(order)

        for patient_id in order:
            options = []

            for day, route in routes.items():
                if day not in patients[patient_id].windows:
                    continue
                if len(route) >= clinician.max_visits_per_day:
                    continue

                for position in range(len(route) + 1):
                    candidate = route[:position] + [patient_id] + route[position:]
                    plan = evaluate_day(day, candidate, patients, clinician, travel)

                    if plan.feasible:
                        options.append((day, position, plan))

            if not options:
                break

            day, position, plan = rng.choice(options)
            routes[day].insert(position, patient_id)
            plans[day] = plan
        else:
            return WeekSchedule(routes=routes, plans=plans)

    raise RuntimeError(
        f"No valid random schedule found in {max_attempts} attempts"
    )


def sample_schedules(patients, clinician, travel, samples, seed=SEED):
    """Generate `samples` random valid weeks, reproducibly from `seed`."""
    rng = random.Random(seed)
    return [
        random_schedule(patients, clinician, travel, rng)
        for _ in range(samples)
    ]
