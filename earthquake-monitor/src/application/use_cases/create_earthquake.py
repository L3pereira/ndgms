from datetime import datetime

from src.domain.entities.earthquake import Earthquake
from src.domain.entities.location import Location
from src.domain.entities.magnitude import Magnitude, MagnitudeScale
from src.domain.repositories.earthquake_repository import EarthquakeRepository


class CreateEarthquakeRequest:
    def __init__(
        self,
        latitude: float,
        longitude: float,
        depth: float,
        magnitude_value: float,
        magnitude_scale: str = "moment",
        occurred_at: datetime = None,
        source: str = "USGS",
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.depth = depth
        self.magnitude_value = magnitude_value
        self.magnitude_scale = magnitude_scale
        self.occurred_at = occurred_at or datetime.now(datetime.UTC)
        self.source = source


class CreateEarthquakeUseCase:
    def __init__(self, earthquake_repository: EarthquakeRepository):
        self._earthquake_repository = earthquake_repository

    async def execute(self, request: CreateEarthquakeRequest) -> str:
        # Create value objects
        location = Location(
            latitude=request.latitude,
            longitude=request.longitude,
            depth=request.depth,
        )

        magnitude_scale = MagnitudeScale(request.magnitude_scale)
        magnitude = Magnitude(value=request.magnitude_value, scale=magnitude_scale)

        # Create earthquake entity
        earthquake = Earthquake(
            location=location,
            magnitude=magnitude,
            occurred_at=request.occurred_at,
            source=request.source,
        )

        # Save to repository
        await self._earthquake_repository.save(earthquake)

        return earthquake.id
