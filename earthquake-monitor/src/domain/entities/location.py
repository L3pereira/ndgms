import math
from dataclasses import dataclass

from ..exceptions import InvalidLocationError


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    depth: float

    def __post_init__(self):
        if not -90 <= self.latitude <= 90:
            raise InvalidLocationError("Latitude must be between -90 and 90 degrees")
        if not -180 <= self.longitude <= 180:
            raise InvalidLocationError("Longitude must be between -180 and 180 degrees")
        if self.depth < 0:
            raise InvalidLocationError("Depth must be non-negative")

    def distance_to(self, other: "Location") -> float:
        """Calculate distance to another location using Haversine formula."""
        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        delta_lat = math.radians(other.latitude - self.latitude)
        delta_lon = math.radians(other.longitude - self.longitude)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def is_near_populated_area(self) -> bool:
        """Check if location is near a populated area.

        Note: This method provides a basic implementation for backward compatibility.
        For more accurate results, use PopulationService directly.
        """
        # Basic implementation using default population centers
        from ..services.population_config import PopulationCenterConfig

        population_centers = PopulationCenterConfig.get_default_population_centers()

        for center in population_centers:
            center_location = Location(center.latitude, center.longitude, 0)
            if self.distance_to(center_location) < center.proximity_threshold_km:
                return True
        return False
