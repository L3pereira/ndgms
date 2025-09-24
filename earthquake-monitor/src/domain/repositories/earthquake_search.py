"""Advanced search operations for earthquake repository."""

from abc import ABC, abstractmethod

from ..entities.earthquake import Earthquake


class EarthquakeSearch(ABC):
    """Interface for advanced earthquake search operations."""

    @abstractmethod
    async def find_with_filters(
        self,
        filters: dict | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Earthquake]:
        """Find earthquakes with complex filters and pagination."""
        pass

    @abstractmethod
    async def count_with_filters(self, filters: dict | None = None) -> int:
        """Count earthquakes matching the given filters."""
        pass
