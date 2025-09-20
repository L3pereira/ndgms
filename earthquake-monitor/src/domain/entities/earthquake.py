from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from .location import Location
from .magnitude import Magnitude


@dataclass
class Earthquake:
    location: Location
    magnitude: Magnitude
    occurred_at: datetime
    source: str = "USGS"
    earthquake_id: str = field(default_factory=lambda: str(uuid4()))
    _is_reviewed: bool = field(default=False, init=False)

    def __post_init__(self):
        if self.occurred_at > datetime.utcnow():
            raise ValueError("Earthquake occurrence time cannot be in the future")

    @property
    def id(self) -> str:
        return self.earthquake_id

    @property
    def is_reviewed(self) -> bool:
        return self._is_reviewed

    def mark_as_reviewed(self) -> None:
        """Mark earthquake data as reviewed by an expert."""
        self._is_reviewed = True

    def requires_immediate_alert(self) -> bool:
        """Check if earthquake requires immediate alert."""
        return (
            self.magnitude.is_significant() and self.location.is_near_populated_area()
        )

    def calculate_affected_radius_km(self) -> float:
        """Calculate the radius of areas potentially affected by the earthquake."""
        base_radius = self.magnitude.value * 20

        # Depth factor: shallower earthquakes affect larger areas
        depth_factor = max(0.1, 1 - (self.location.depth / 100))

        return base_radius * depth_factor

    def get_impact_assessment(self) -> dict:
        """Get comprehensive impact assessment."""
        return {
            "alert_level": self.magnitude.get_alert_level(),
            "affected_radius_km": self.calculate_affected_radius_km(),
            "requires_immediate_alert": self.requires_immediate_alert(),
            "magnitude_description": self.magnitude.get_description(),
            "near_populated_area": self.location.is_near_populated_area(),
            "is_significant": self.magnitude.is_significant(),
        }
