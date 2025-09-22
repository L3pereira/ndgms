import os
from abc import ABC, abstractmethod

from ..entities.location import Location
from .population_config import PopulationCenter, PopulationCenterConfig


class PopulationService(ABC):
    """Abstract service for population-related operations."""

    @abstractmethod
    async def is_near_populated_area(self, location: Location) -> bool:
        """Check if a location is near a populated area."""
        pass

    @abstractmethod
    async def get_affected_population_estimate(
        self, center: Location, radius_km: float
    ) -> int:
        """Estimate population affected within a radius."""
        pass


class PopulationServiceImpl(PopulationService):
    """Implementation of population service with configurable population centers."""

    def __init__(self, population_centers: list[PopulationCenter] = None):
        """Initialize with population centers from config or environment."""
        if population_centers is None:
            env_centers = os.getenv("POPULATION_CENTERS", "")
            if env_centers:
                self._population_centers = PopulationCenterConfig.from_env_string(
                    env_centers
                )
            else:
                self._population_centers = (
                    PopulationCenterConfig.get_default_population_centers()
                )
        else:
            self._population_centers = population_centers

    async def is_near_populated_area(self, location: Location) -> bool:
        """Check if location is within threshold distance of any populated area."""
        for center in self._population_centers:
            center_location = Location(center.latitude, center.longitude, 0)
            if location.distance_to(center_location) < center.proximity_threshold_km:
                return True
        return False

    async def get_affected_population_estimate(
        self, center: Location, radius_km: float
    ) -> int:
        """Estimate population based on proximity to known populated centers."""
        total_population = 0
        for pop_center in self._population_centers:
            center_location = Location(pop_center.latitude, pop_center.longitude, 0)
            distance = center.distance_to(center_location)
            if distance < radius_km:
                # Simple calculation: closer areas contribute more
                factor = max(0, 1 - (distance / radius_km))
                # Use different base populations for different cities
                base_population = self._get_base_population(pop_center.name)
                total_population += int(base_population * factor)
        return total_population

    def _get_base_population(self, city_name: str) -> int:
        """Get estimated base population for major cities."""
        population_estimates = {
            "Tokyo": 37_400_000,
            "New York": 8_400_000,
            "Los Angeles": 4_000_000,
            "San Francisco": 880_000,
            "London": 9_000_000,
            "Moscow": 12_500_000,
            "Mexico City": 21_800_000,
            "Beijing": 21_500_000,
            "Mumbai": 20_400_000,
            "São Paulo": 12_300_000,
        }
        return population_estimates.get(city_name, 1_000_000)  # Default 1M
