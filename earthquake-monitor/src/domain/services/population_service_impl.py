"""Implementation of population service using configuration."""

from ..entities.location import Location
from .population_config import PopulationCenterConfig
from .population_service_interface import PopulationServiceInterface


class ConfigurablePopulationService(PopulationServiceInterface):
    """Population service implementation using configurable population centers."""

    def __init__(self, population_centers: list = None):
        """Initialize with optional population centers list."""
        self._population_centers = (
            population_centers
            if population_centers is not None
            else PopulationCenterConfig.get_default_population_centers()
        )

    def is_location_near_populated_area(self, location: Location) -> bool:
        """Check if a location is near a populated area using configured centers."""
        for center in self._population_centers:
            center_location = Location(center.latitude, center.longitude, 0)
            if location.distance_to(center_location) < center.proximity_threshold_km:
                return True
        return False
