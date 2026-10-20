from dataclasses import dataclass, field

from patient import WEEKDAYS


@dataclass
class Clinician:
    """A clinician's working pattern. Times are minutes since midnight."""

    work_days: list[str] = field(default_factory=lambda: list(WEEKDAYS))
    start: int = 8 * 60
    end: int = 17 * 60
    max_visits_per_day: int = 4

    def __post_init__(self):
        for day in self.work_days:
            if day not in WEEKDAYS:
                raise ValueError(f"Unknown work day: {day!r}")
        if not 0 <= self.start < self.end <= 24 * 60:
            raise ValueError("Work hours must satisfy 0 <= start < end <= 24:00")
        if self.max_visits_per_day < 1:
            raise ValueError("max_visits_per_day must be at least 1")
