from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..entities.earthquake import Earthquake


class EarthquakeRepository(ABC):
    """Abstract repository interface for earthquake data operations."""

    @abstractmethod
    async def save(self, earthquake: Earthquake) -> None:
        """Save an earthquake to the repository."""
        pass

    @abstractmethod
    async def find_by_id(self, earthquake_id: str) -> Optional[Earthquake]:
        """Find an earthquake by its ID."""
        pass

    @abstractmethod
    async def exists(self, earthquake_id: str) -> bool:
        """Check if an earthquake exists in the repository."""
        pass

    @abstractmethod
    async def find_by_magnitude_range(
        self, min_magnitude: float, max_magnitude: Optional[float] = None
    ) -> List[Earthquake]:
        """Find earthquakes within a magnitude range."""
        pass

    @abstractmethod
    async def find_by_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> List[Earthquake]:
        """Find earthquakes within a time range."""
        pass

    @abstractmethod
    async def find_by_location_radius(
        self, latitude: float, longitude: float, radius_km: float
    ) -> List[Earthquake]:
        """Find earthquakes within a radius of a location."""
        pass

    @abstractmethod
    async def find_unreviewed(self) -> List[Earthquake]:
        """Find all unreviewed earthquakes."""
        pass

    @abstractmethod
    async def find_with_filters(
        self,
        filters: Optional[dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Earthquake]:
        """Find earthquakes with complex filters and pagination."""
        pass

    @abstractmethod
    async def count_with_filters(self, filters: Optional[dict] = None) -> int:
        """Count earthquakes matching the given filters."""
        pass
