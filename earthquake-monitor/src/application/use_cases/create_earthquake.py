from src.application.dto.create_earthquake_request import CreateEarthquakeRequest
from src.application.events.event_publisher import EventPublisher
from src.domain.entities.earthquake import Earthquake
from src.domain.entities.location import Location
from src.domain.entities.magnitude import Magnitude, MagnitudeScale
from src.domain.events.earthquake_detected import EarthquakeDetected
from src.domain.events.high_magnitude_alert import HighMagnitudeAlert
from src.domain.exceptions import InvalidEarthquakeDataError
from src.domain.repositories.earthquake_repository import EarthquakeRepository


class CreateEarthquakeUseCase:
    def __init__(
        self,
        earthquake_repository: EarthquakeRepository,
        event_publisher: EventPublisher,
    ):
        self._earthquake_repository = earthquake_repository
        self._event_publisher = event_publisher

    async def execute(self, request: CreateEarthquakeRequest) -> str:
        """Execute the create earthquake use case with validation."""
        self._validate_request(request)

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

        # Set additional attributes if provided
        if request.external_id:
            earthquake.external_id = request.external_id
        if request.raw_data:
            earthquake.raw_data = request.raw_data

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

    def _validate_request(self, request: CreateEarthquakeRequest) -> None:
        """Validate the create earthquake request."""
        if not request.source or not request.source.strip():
            raise InvalidEarthquakeDataError("Source cannot be empty")

        if request.magnitude_scale not in [
            "richter",
            "moment",
            "body_wave",
            "surface_wave",
        ]:
            raise InvalidEarthquakeDataError(
                f"Invalid magnitude scale: {request.magnitude_scale}"
            )

        if request.external_id and len(request.external_id) > 100:
            raise InvalidEarthquakeDataError("External ID cannot exceed 100 characters")
