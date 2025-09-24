"""Write operations for earthquake repository."""

from abc import ABC, abstractmethod

from ..entities.earthquake import Earthquake


class EarthquakeWriter(ABC):
    """Interface for earthquake write operations."""

    @abstractmethod
    async def save(self, earthquake: Earthquake) -> str:
        """Save an earthquake to the repository and return its ID."""
        pass
