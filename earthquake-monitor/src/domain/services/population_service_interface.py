"""Abstract interface for population service."""

from abc import ABC, abstractmethod

from ..entities.location import Location


class PopulationServiceInterface(ABC):
    """Abstract interface for checking if a location is near populated areas."""

    @abstractmethod
    def is_location_near_populated_area(self, location: Location) -> bool:
        """Check if a location is near a populated area."""
        pass
