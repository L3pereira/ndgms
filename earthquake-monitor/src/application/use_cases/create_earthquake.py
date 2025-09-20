from datetime import datetime, timezone

from src.application.events.event_publisher import EventPublisher
from src.domain.entities.earthquake import Earthquake
from src.domain.entities.location import Location
from src.domain.entities.magnitude import Magnitude, MagnitudeScale
from src.domain.events.earthquake_detected import EarthquakeDetected
from src.domain.events.high_magnitude_alert import HighMagnitudeAlert
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
        self.occurred_at = occurred_at or datetime.now(timezone.utc)
        self.source = source


class CreateEarthquakeUseCase:
    def __init__(
        self,
        earthquake_repository: EarthquakeRepository,
        event_publisher: EventPublisher,
    ):
        self._earthquake_repository = earthquake_repository
        self._event_publisher = event_publisher

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

        # Publish earthquake detected event
        earthquake_detected = EarthquakeDetected(
            earthquake_id=earthquake.id,
            occurred_at=earthquake.occurred_at,
            magnitude=earthquake.magnitude.value,
            latitude=earthquake.location.latitude,
            longitude=earthquake.location.longitude,
            depth=earthquake.location.depth,
            source=earthquake.source,
        )
        await self._event_publisher.publish(earthquake_detected)

        # Check for high magnitude alert
        if earthquake.requires_immediate_alert():
            impact_assessment = earthquake.get_impact_assessment()
            high_magnitude_alert = HighMagnitudeAlert(
                earthquake_id=earthquake.id,
                magnitude=earthquake.magnitude.value,
                alert_level=earthquake.magnitude.get_alert_level(),
                latitude=earthquake.location.latitude,
                longitude=earthquake.location.longitude,
                affected_radius_km=impact_assessment["affected_radius_km"],
                requires_immediate_response=impact_assessment[
                    "requires_immediate_alert"
                ],
            )
            await self._event_publisher.publish(high_magnitude_alert)

        return earthquake.id
