"""Streamlit UI: review patients, generate the week, inspect the schedule."""

import streamlit as st

from baseline import sample_schedules
from clinician import Clinician
from display import (
    day_label,
    format_availability,
    format_swap,
    format_time,
    short_address,
)
from main import RANDOM_SAMPLES, WEEK_START, plan_week
from patient import load_patients
from travel import TravelTimes


@st.cache_resource
def load_data():
    return load_patients(WEEK_START), Clinician(), TravelTimes()


@st.cache_resource
def random_weeks():
    patients, clinician, travel = load_data()
    return sample_schedules(patients, clinician, travel, RANDOM_SAMPLES)


def patient_details(patient):
    return {
        "ID": patient.patient_id,
        "Name": f"{patient.first_name} {patient.last_name}",
        "Type": patient.visit_type,
        "Address": short_address(patient.address),
        "Availability used by scheduler": format_availability(patient),
        "Restriction as recorded": patient.restriction_reason,
    }


def show_patients(patients):
    st.subheader("Patients")
    st.caption(
        "Check that the availability the scheduler uses matches each "
        "recorded restriction before generating the schedule."
    )
    st.dataframe(
        [patient_details(p) for p in patients.values()],
        hide_index=True,
        width="stretch",
    )


def show_schedule(schedule, patients):
    st.subheader("Schedule")
    scheduled = sum(len(route) for route in schedule.routes.values())
    st.write(
        f"**Week:** {scheduled} visits, "
        f"{schedule.drive_minutes:.1f} min driving, "
        f"{schedule.drive_miles:.1f} mi"
    )

    if schedule.unscheduled:
        st.warning(f"Unscheduled: {', '.join(schedule.unscheduled)}")

    for day, plan in schedule.plans.items():
        st.markdown(
            f"**{day_label(day, WEEK_START)}**: {len(plan.visits)} visits, "
            f"{plan.drive_minutes:.1f} min, {plan.drive_miles:.1f} mi"
        )
        rows = []
        for i, visit in enumerate(plan.visits):
            # The clinician leaves HOME in time for the first visit.
            arrival = visit.start if i == 0 else visit.arrival
            rows.append({
                "Time": f"{format_time(visit.start)}-{format_time(visit.end)}",
                "Arrive": format_time(arrival),
                **patient_details(patients[visit.patient_id]),
            })
        st.dataframe(rows, hide_index=True, width="stretch")


def stage_row(name, schedule):
    return {
        "Stage": name,
        "Minutes": round(schedule.drive_minutes, 1),
        "Miles": round(schedule.drive_miles, 1),
    }


def show_comparison(stages, swaps):
    final = stages[-1][1]

    with st.expander("How good is this schedule?"):
        rows = [stage_row(name, schedule) for name, schedule in stages]

        st.write(
            f"Compare against {RANDOM_SAMPLES:,} random schedules that respect "
            "every restriction but ignore driving."
        )
        if st.button("Run comparison (a few seconds)", key="compare"):
            weeks = sorted(random_weeks(), key=lambda w: w.drive_minutes)
            median = weeks[len(weeks) // 2]
            beaten = sum(w.drive_minutes > final.drive_minutes for w in weeks)
            rows.insert(0, stage_row(f"Random (median of {RANDOM_SAMPLES:,})", median))
            st.write(
                f"Random weeks range from {weeks[0].drive_minutes:.1f} to "
                f"{weeks[-1].drive_minutes:.1f} min. This schedule beats "
                f"{beaten / len(weeks):.1%} of them."
            )

        st.dataframe(rows, hide_index=True)

        st.markdown("**Swaps between days**")
        for swap in swaps:
            st.write(format_swap(swap))
        if not swaps:
            st.write("None")


def main():
    st.set_page_config(page_title="Home Health Scheduler", layout="wide")
    st.title("Home Health Weekly Scheduler")
    st.caption(
        f"Week of {WEEK_START:%b %d, %Y}. Synthetic patients; not clinical guidance."
    )

    patients, clinician, travel = load_data()
    show_patients(patients)

    if st.button("Generate schedule", type="primary", key="generate"):
        st.session_state.plan = plan_week(patients, clinician, travel)

    if "plan" in st.session_state:
        stages, swaps = st.session_state.plan
        show_schedule(stages[-1][1], patients)
        show_comparison(stages, swaps)


main()
