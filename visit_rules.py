"""General clinical scheduling rules (not patient-specific)."""

# Visit length in minutes, by visit type.
VISIT_MINUTES = {
    "SOC": 90,
    "ROC": 60,
    "RC": 60,
    "RA": 60,
    "DC": 60,
}


def visit_duration(visit_type):
    try:
        return VISIT_MINUTES[visit_type]
    except KeyError:
        raise ValueError(f"Unknown visit type: {visit_type!r}") from None
