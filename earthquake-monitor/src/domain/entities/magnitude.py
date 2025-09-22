from dataclasses import dataclass
from enum import Enum

from ..exceptions import InvalidMagnitudeError


class MagnitudeScale(Enum):
    RICHTER = "richter"
    MOMENT = "moment"
    BODY_WAVE = "body_wave"
    SURFACE_WAVE = "surface_wave"


@dataclass(frozen=True)
class Magnitude:
    value: float
    scale: MagnitudeScale = MagnitudeScale.MOMENT

    def __post_init__(self):
        if self.value < 0:
            raise InvalidMagnitudeError("Magnitude value must be non-negative")
        if self.value > 12:
            raise InvalidMagnitudeError("Magnitude value cannot exceed 12")

    def is_significant(self) -> bool:
        """Check if magnitude is significant (5.0 or greater)."""
        return self.value >= 5.0

    def get_alert_level(self) -> str:
        """Get alert level based on magnitude value."""
        if self.value >= 7.0:
            return "CRITICAL"
        elif self.value >= 5.5:
            return "HIGH"
        elif self.value >= 4.0:
            return "MEDIUM"
        return "LOW"

    def get_description(self) -> str:
        """Get human-readable description of magnitude impact."""
        if self.value < 2.0:
            return "Micro - Not felt"
        elif self.value < 3.0:
            return "Minor - Often felt, but rarely causes damage"
        elif self.value < 4.0:
            return "Light - Noticeable shaking, rarely causes damage"
        elif self.value < 5.0:
            return "Moderate - Can cause damage to poorly constructed buildings"
        elif self.value < 6.0:
            return "Strong - Can be destructive in areas up to 160 km"
        elif self.value < 7.0:
            return "Major - Can cause serious damage over larger areas"
        elif self.value < 8.0:
            return "Great - Can cause serious damage in areas several hundred km"
        else:
            return "Extreme - Devastating in areas thousands of km"
