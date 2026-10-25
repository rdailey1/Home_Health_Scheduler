# Patient Routing Tool

A Python-based scheduling and route optimization tool designed for home-health clinicians.

## Project Overview

Home-health clinicians must coordinate patient visits across a workweek while accounting for clinical deadlines, patient scheduling restrictions, visit durations, and geographical travel.

This project aims to automate that process by generating feasible weekly schedules and optimizing patient assignments across days to reduce unnecessary travel and inefficient scheduling attempts by a clinician.

The scheduling approach is inspired by real-world home-health workflows: place mandatory visits first, build geographical clusters around those appointments, and rearrange flexible visits to improve overall weekly efficiency.

## Technical Approach

The application will use:

- **Constraint-based scheduling** to satisfy mandatory visit dates, patient restrictions, and clinician working hours.
- **Nearest Neighbor (NN)** to construct daily routes using a precomputed travel matrix.
- **Weekly local search** to evaluate patient swaps and relocations between days.
- **Schedule validation** to ensure that travel, appointment durations, and time windows remain feasible.

The optimization objective is to minimize weekly clinician travel while respecting the following priorities:

1. Clinical scheduling requirements and hard patient restrictions.
2. Clinician routing efficiency.
3. Patient soft scheduling preferences.

## Synthetic Dataset

The project uses 20 fictional patient records spread across a realistic single-clinician territory in Pittsburgh, Pennsylvania: downtown and the Hill District (15219, 15222), Oakland and Lawrenceville (15201, 15213), the North Side (15212, 15214), south of the Monongahela (15203, 15210, 15211), and beyond the Liberty Tunnel (15216, 15226). The clinician lives just outside the territory near Frick Park (15217). Pittsburgh was chosen for its terrain: three rivers, many bridges, and two tunnels make day assignment and visit order matter.

The data deliberately includes scenarios that test the scheduler:

- **Tunnel trips:** Medicare fixes two start-of-care visits beyond the tunnel on different days, forcing two trips; flexible nearby patients should join those days.
- **Dialysis:** a North Side patient available only Tuesday/Thursday should be pulled away from the tunnel day.
- **Narrow windows:** one patient is available only 14:00–17:00; two patients on opposite sides of the river are both limited to Thursday 9:00–10:30, so one must move.
- **Same building:** two patients live in one senior building; consecutive visits there need no driving or parking.

Patient locations use public-address stand-ins rather than actual residential or patient addresses. All patient identities, clinical information, and scheduling restrictions are synthetic.

The dataset includes:

- Patient identifiers and names
- Visit types (SOC:start of care, RC:recertification, ROC:resumption of care, RA:reassessment, DC:discharge)
- Certification-period information and scheduling windows
- Patient scheduling restrictions and preferences

Patients are assumed available during clinician working hours unless a specific restriction applies.

## Scheduling Assumptions

- **Target week:** Monday–Friday, October 19–23, 2026.
- **Clinician:** one clinician working 8:00 AM–5:00 PM, up to four visits per day. Each day starts and ends at the clinician's home base.
- **Visit frequency:** one visit per patient per week, the standard frequency in home health.
- **Visit durations:** 45 minutes, except start of care (SOC) at 75 minutes and discharge (DC) at 30 minutes. Driving and parking are modeled separately.
- **Mandatory days:** SOC visits occur on a fixed day. Visit times are never fixed.
- **Discharge (DC) and resumption of care (ROC):** a DC day must be set 48 hours in advance and an ROC day is agreed with the patient. Because schedules are assumed to be built the week prior, the scheduler chooses these days, limited only by patient and clinician availability.
- **Recertification (RC):** must occur within the five-day window ending on the last day of the certification period.
- **Availability:** patient data records exceptions rather than full availability. `restricted_days` and `restricted_times` are hard restrictions. For low-availability patients, `available_times` limits visits to the listed windows; days not listed are unavailable. Restricted times are applied after available times.
- **Preferences:** `preferred_days` and `preferred_times` are soft and never override hard restrictions.

## Development Roadmap

### MVP — Weekly Scheduling

- [ ] Import synthetic patient records from CSV.
- [ ] Extract and index patient addresses.
- [ ] Load a precomputed distance/travel-time matrix.
- [ ] Implement visit-type scheduling requirements.
- [ ] Assign mandatory visits before flexible visits.
- [ ] Construct geographically efficient daily routes.
- [ ] Validate patient restrictions, visit durations, and working hours.
- [ ] Output a feasible Monday–Friday schedule with up to four visits per day.

### V2 — Weekly Optimization

- [ ] Implement cross-day patient swaps and relocations.
- [ ] Evaluate alternative geographical clusters.
- [ ] Preserve scheduling feasibility during optimization.
- [ ] Compare initial and optimized weekly travel totals.
- [ ] Benchmark against a basic scheduling approach.

### V3 — Configurable Scheduling and Routing

- [ ] Integrate a routing API to generate travel-time and distance matrices.
- [ ] Cache routing data.
- [ ] Support configurable clinician working days and hours.
- [ ] Allow flexible daily visit capacity.
- [ ] Account for other clinicians' appointments.
- [ ] Balance travel efficiency with workload distribution.

### V4 — User Interface

- [ ] Develop an interface for patient and schedule management.
- [ ] Display weekly schedules and daily routes.
- [ ] Support manual visit reassignment.
- [ ] Re-optimize schedules after changes.
- [ ] Identify scheduling conflicts and unscheduled visits.

## Current Status

**Early development — synthetic dataset preparation and scheduling architecture.**

The initial development focus is a command-line Python application capable of generating and optimizing a weekly schedule.

## Background

This project builds on concepts explored in a previous package-routing optimization assignment, including address indexing, distance matrices, and nearest-neighbor routing.

Unlike the original delivery-routing problem, home-health scheduling requires assigning appointments across multiple days while satisfying patient-specific time restrictions and clinical scheduling requirements.

The goal is to develop a practical scheduling heuristic, evaluate its performance, and demonstrate measurable improvements in weekly routing efficiency.

## Disclaimer

This is a portfolio and educational project. It does not use protected health information (PHI), and it is not intended for clinical deployment. Clinical scheduling assumptions are simplified for development and should not be interpreted as authoritative Medicare guidance.