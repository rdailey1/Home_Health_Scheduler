# PatientRoutingTool

Weekly scheduling and route optimization for a single home-health clinician.
Portfolio project; synthetic data only (no PHI); not clinical guidance.
The developer is a home-health physical therapist; defer to them on clinical workflow.

## Collaboration rules
- Work incrementally: one file or focused change at a time; keep commits small.
- Discuss architecture and tradeoffs before major changes.
- Do not implement when the question is conceptual or design-oriented.
- Briefly explain non-obvious algorithmic decisions; favor simple, testable code.
- Challenge weak assumptions. Stay focused on a working end-to-end MVP.
- The repo is the source of truth; inspect before assuming something exists.

## Scheduling design
- Priorities, strictly ordered: (1) hard clinical/patient restrictions,
  (2) driving time, (3) soft patient preferences. Soft never overrides hard.
- Mirror clinician reasoning: place the most constrained visits first, cluster
  around them, fill with flexible visits, then rearrange across the week.
  Do not optimize five fixed daily routes independently.
- Days can be mandatory (SOC); appointment times are never fixed.
  DC and ROC days are chosen by the scheduler (schedule built a week ahead).
- One visit per patient per week. Visits 1 hr; SOC 1.5 hr.
- Each day starts and ends at HOME.
- MVP assumptions (Mon–Fri, 8:00–17:00, 4 visits/day) must stay configurable.
  Later: flexible visits/day, selectable work days, max wait between visits.
- RA/DC timing rules are out of scope (would come from the clinician's calendar).
- Patient-specific dates/restrictions live in patients.csv; general clinical
  rules and visit durations live in code/config, not per row.

## Availability rules (patients.csv)
- Data records exceptions, not full availability.
- Mandatory day: earliest_visit_date == latest_visit_date.
- restricted_days / restricted_times: hard.
- available_times: if set, visits only within listed windows; unlisted days are
  unavailable. If empty, available all working hours. restricted_times is
  subtracted afterward in both cases.
- preferred_days / preferred_times: soft.
- Time format: `Day:HH:MM-HH:MM`, multiple entries separated by `|`.

## Data files
- data/patients.csv: source of patient data and addresses (no separate locations file).
- data/coordinates.json: reviewed geocodes; derived, committed for provenance.
- data/distance_matrix.csv: directed (A→B ≠ B→A), columns
  from_id,to_id,distance_miles,base_travel_minutes.
- Location IDs: HOME (2005 Beechwood Blvd, 15217) and patient IDs 101–120.
- Driving time is the optimization metric; mileage is for reporting.
- Travel times are static baselines; keep lookups behind an interface so
  departure-time-aware travel can be added without a scheduler rewrite.
- Reject unverifiable geocodes rather than accept inaccurate coordinates.

## Secrets
- ORS_API_KEY lives in .env (gitignored). Never print, log, or commit it.

## Commands
- Install:            pip install -r requirements.txt
- Geocode and review: python generate_distance_matrix.py
- Build matrix:       python generate_distance_matrix.py --generate
  (uses data/coordinates.json; no re-geocoding)
- Run tests:          python3 -m pytest
