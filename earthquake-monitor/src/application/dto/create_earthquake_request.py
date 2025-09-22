"""Request DTOs for earthquake use cases."""

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class CreateEarthquakeRequest:
    """Request object for creating an earthquake."""

    latitude: float
    longitude: float
    depth: float
    magnitude_value: float
    magnitude_scale: str = "moment"
    occurred_at: datetime | None = None
    source: str = "USGS"
    external_id: str | None = None
    raw_data: str | None = None

    def __post_init__(self) -> None:
        """Set default values after initialization."""
        if self.occurred_at is None:
            self.occurred_at = datetime.now(UTC)
