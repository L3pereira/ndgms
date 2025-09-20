import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    depth: float

    def __post_init__(self):
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        if self.depth < 0:
            raise ValueError("Depth must be non-negative")

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
        """Check if location is near a populated area (simplified logic)."""
        # This is a simplified implementation
        # In reality, this would check against a database of populated areas
        populated_areas = [
            (37.7749, -122.4194),  # San Francisco
            (34.0522, -118.2437),  # Los Angeles
            (40.7128, -74.0060),  # New York
            (35.6762, 139.6503),  # Tokyo
            (55.7558, 37.6176),  # Moscow
        ]

        for lat, lon in populated_areas:
            area_location = Location(lat, lon, 0)
            if self.distance_to(area_location) < 100:  # Within 100km
                return True
        return False
