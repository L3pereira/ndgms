"""Query operations for earthquake repository."""

from abc import ABC, abstractmethod
from datetime import datetime

from ..entities.earthquake import Earthquake


class EarthquakeQuery(ABC):
    """Interface for earthquake query operations."""

    @abstractmethod
    async def find_by_magnitude_range(
        self, min_magnitude: float, max_magnitude: float | None = None
    ) -> list[Earthquake]:
        """Find earthquakes within a magnitude range."""
        pass

    @abstractmethod
    async def find_by_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> list[Earthquake]:
        """Find earthquakes within a time range."""
        pass

    @abstractmethod
    async def find_by_location_radius(
        self, latitude: float, longitude: float, radius_km: float
    ) -> list[Earthquake]:
        """Find earthquakes within a radius of a location."""
        pass

    @abstractmethod
    async def find_unreviewed(self) -> list[Earthquake]:
        """Find all unreviewed earthquakes."""
        pass
