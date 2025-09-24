"""Domain service for earthquake entity creation."""

from datetime import datetime

from ..entities.earthquake import Earthquake
from ..entities.location import Location
from ..entities.magnitude import Magnitude, MagnitudeScale


class EarthquakeFactoryService:
    """Domain service responsible for creating earthquake entities."""

    def create_earthquake(
        self,
        latitude: float,
        longitude: float,
        depth: float,
        magnitude_value: float,
        magnitude_scale: str,
        occurred_at: datetime,
        source: str,
        external_id: str | None = None,
        raw_data: dict | None = None,
        title: str | None = None,
    ) -> Earthquake:
        """Create an earthquake entity with proper value objects."""
        # Create value objects
        location = Location(
            latitude=latitude,
            longitude=longitude,
            depth=depth,
        )

        magnitude_scale_enum = MagnitudeScale(magnitude_scale)
        magnitude = Magnitude(value=magnitude_value, scale=magnitude_scale_enum)

        # Create earthquake entity
        earthquake = Earthquake(
            location=location,
            magnitude=magnitude,
            occurred_at=occurred_at,
            source=source,
            external_id=external_id,
            raw_data=raw_data,
            title=title,
        )

        return earthquake
