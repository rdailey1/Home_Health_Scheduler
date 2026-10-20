from dataclasses import dataclass, field

from patient import WEEKDAYS


@dataclass
class Clinician:
    """A clinician's working pattern. Times are minutes since midnight."""

    work_days: list[str] = field(default_factory=lambda: list(WEEKDAYS))
    start: int = 8 * 60
    end: int = 17 * 60
    max_visits_per_day: int = 4

    # Parking/walking time added after each drive to a patient.
    visit_buffer: int = 7
    # Visits start on this increment (30 -> :00 or :30).
    start_increment: int = 30

    def __post_init__(self):
        for day in self.work_days:
            if day not in WEEKDAYS:
                raise ValueError(f"Unknown work day: {day!r}")
        if not 0 <= self.start < self.end <= 24 * 60:
            raise ValueError("Work hours must satisfy 0 <= start < end <= 24:00")
        if self.max_visits_per_day < 1:
            raise ValueError("max_visits_per_day must be at least 1")
        if self.visit_buffer < 0:
            raise ValueError("visit_buffer cannot be negative")
        if self.start_increment < 1:
            raise ValueError("start_increment must be at least 1 minute")
