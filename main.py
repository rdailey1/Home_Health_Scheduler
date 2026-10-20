from datetime import date

from clinician import Clinician
from insertion import build_schedule
from patient import load_patients
from travel import TravelTimes

WEEK_START = date(2026, 10, 19)


def format_time(minutes):
    """Minutes since midnight -> 'H:MM' (24-hour), rounded to the minute."""
    hours, mins = divmod(round(minutes), 60)
    return f"{hours}:{mins:02d}"


def short_address(address):
    """'200 Lothrop St, Pittsburgh, PA 15213' -> '200 Lothrop St, 15213'."""
    street = address.split(",")[0]
    zip_code = address.split()[-1]
    return f"{street}, {zip_code}"


def print_day(plan, patients):
    print(
        f"{plan.day}  {len(plan.visits)} visits  "
        f"{plan.drive_minutes:.1f} min  {plan.drive_miles:.1f} mi"
    )

    for i, visit in enumerate(plan.visits):
        patient = patients[visit.patient_id]
        name = f"{patient.first_name} {patient.last_name}"
        # The clinician leaves HOME in time for the first visit, so no wait.
        arrival = visit.start if i == 0 else visit.arrival
        print(
            f"  {visit.patient_id}  {name:<20} {patient.visit_type:<4} "
            f"arrive {format_time(arrival):>5}  "
            f"{format_time(visit.start):>5}-{format_time(visit.end):<5}  "
            f"{short_address(patient.address)}"
        )


def print_week(schedule, patients):
    print(f"Week of {WEEK_START:%b %d, %Y}\n")

    for plan in schedule.plans.values():
        print_day(plan, patients)
        print()

    scheduled = sum(len(route) for route in schedule.routes.values())
    print(
        f"Week: {scheduled} visits  {schedule.drive_minutes:.1f} min  "
        f"{schedule.drive_miles:.1f} mi"
    )
    print(f"Unscheduled: {', '.join(schedule.unscheduled) or 'none'}")


def main():
    patients = load_patients(WEEK_START)
    schedule = build_schedule(patients, Clinician(), TravelTimes())
    print_week(schedule, patients)


if __name__ == "__main__":
    main()
