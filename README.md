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

The project uses 20 fictional patient records across four Pittsburgh, Pennsylvania ZIP codes: 15222, 15203, 15213, and 15217. Pittsburgh, PA was chosen due to its interestingn geographical terrain, including, bridges, tunnels as well as taffic patterns.

Patient locations use public-address stand-ins rather than actual residential or patient addresses. All patient identities, clinical information, and scheduling restrictions are synthetic.

The dataset includes:

- Patient identifiers and names
- Visit types (SOC:start of care, RC:recertification, ROC:resumption of care, RA:reassessment, DC:discharge)
- Certification-period information and scheduling windows
- Patient scheduling restrictions and preferences

Patients are assumed available during clinician working hours unless a specific restriction applies.

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