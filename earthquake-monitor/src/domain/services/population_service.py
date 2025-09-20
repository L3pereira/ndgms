from abc import ABC, abstractmethod
from typing import List
from ..entities.location import Location


class PopulationService(ABC):
    """Abstract service for population-related operations."""

    @abstractmethod
    async def is_near_populated_area(self, location: Location) -> bool:
        """Check if a location is near a populated area."""
        pass

    @abstractmethod
    async def get_affected_population_estimate(
        self,
        center: Location,
        radius_km: float
    ) -> int:
        """Estimate population affected within a radius."""
        pass


class PopulationServiceImpl(PopulationService):
    """Implementation of population service with basic logic."""

    def __init__(self, populated_areas: List[tuple] = None):
        self._populated_areas = populated_areas or [
            (37.7749, -122.4194),  # San Francisco
            (34.0522, -118.2437),  # Los Angeles
            (40.7128, -74.0060),   # New York
            (35.6762, 139.6503),   # Tokyo
            (55.7558, 37.6176),    # Moscow
        ]

    async def is_near_populated_area(self, location: Location) -> bool:
        """Check if location is within 100km of any populated area."""
        for lat, lon in self._populated_areas:
            area_location = Location(lat, lon, 0)
            if location.distance_to(area_location) < 100:
                return True
        return False

    async def get_affected_population_estimate(
        self,
        center: Location,
        radius_km: float
    ) -> int:
        """Simple population estimation based on proximity to known areas."""
        total_population = 0
        for lat, lon in self._populated_areas:
            area_location = Location(lat, lon, 0)
            distance = center.distance_to(area_location)
            if distance < radius_km:
                # Simple calculation: closer areas contribute more
                factor = max(0, 1 - (distance / radius_km))
                total_population += int(1000000 * factor)  # Base 1M per area
        return total_population