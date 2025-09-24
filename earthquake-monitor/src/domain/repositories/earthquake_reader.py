"""Read operations for earthquake repository."""

from abc import ABC, abstractmethod

from ..entities.earthquake import Earthquake


class EarthquakeReader(ABC):
    """Interface for basic earthquake read operations."""

    @abstractmethod
    async def find_by_id(self, earthquake_id: str) -> Earthquake | None:
        """Find an earthquake by its ID."""
        pass

    @abstractmethod
    async def exists(self, earthquake_id: str) -> bool:
        """Check if an earthquake exists in the repository."""
        pass

    @abstractmethod
    async def find_all(self) -> list[Earthquake]:
        """Find all earthquakes."""
        pass
