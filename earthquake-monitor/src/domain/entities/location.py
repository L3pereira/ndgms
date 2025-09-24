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

        Note: This is a simplified implementation for backward compatibility.
        For production use, inject a PopulationServiceInterface implementation.

        This method uses basic heuristics based on proximity to major population centers.
        """
        # Simplified implementation using well-known major population center coordinates
        # This removes the dependency on infrastructure layer
        major_population_centers = [
            (40.7128, -74.0060, 50),  # New York City (50km radius)
            (34.0522, -118.2437, 40),  # Los Angeles (40km radius)
            (41.8781, -87.6298, 35),  # Chicago (35km radius)
            (29.7604, -95.3698, 30),  # Houston (30km radius)
            (33.4484, -112.0740, 25),  # Phoenix (25km radius)
            (39.9526, -75.1652, 30),  # Philadelphia (30km radius)
            (29.4241, -98.4936, 25),  # San Antonio (25km radius)
            (32.7767, -96.7970, 30),  # Dallas (30km radius)
            (37.7749, -122.4194, 35),  # San Francisco (35km radius)
            (47.6062, -122.3321, 25),  # Seattle (25km radius)
        ]

        for lat, lng, radius_km in major_population_centers:
            center_location = Location(lat, lng, 0)
            if self.distance_to(center_location) < radius_km:
                return True
        return False
