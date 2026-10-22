"""General clinical scheduling rules (not patient-specific)."""

# Visit length in minutes, by visit type.
VISIT_MINUTES = {
    "SOC": 75,
    "ROC": 45,
    "RC": 45,
    "RA": 45,
    "DC": 30,
}


def visit_duration(visit_type):
    try:
        return VISIT_MINUTES[visit_type]
    except KeyError:
        raise ValueError(f"Unknown visit type: {visit_type!r}") from None
