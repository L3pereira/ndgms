"""Application service for orchestrating earthquake-related events."""

from src.application.events.event_publisher import EventPublisher
from src.domain.entities.earthquake import Earthquake
from src.domain.events.earthquake_detected import EarthquakeDetected
from src.domain.events.high_magnitude_alert import HighMagnitudeAlert


class EarthquakeEventOrchestrator:
    """Service responsible for orchestrating earthquake-related events."""

    def __init__(self, event_publisher: EventPublisher):
        self._event_publisher = event_publisher

    async def publish_earthquake_events(self, earthquake: Earthquake) -> None:
        """Publish all relevant events for an earthquake."""
        # Always publish earthquake detected event
        await self._publish_earthquake_detected(earthquake)

        # Publish high magnitude alert if needed
        if earthquake.requires_immediate_alert():
            await self._publish_high_magnitude_alert(earthquake)

    async def _publish_earthquake_detected(self, earthquake: Earthquake) -> None:
        """Publish earthquake detected event."""
        earthquake_detected = EarthquakeDetected(
            earthquake_id=earthquake.id,
            occurred_at=earthquake.occurred_at,
            magnitude=earthquake.magnitude.value,
            latitude=earthquake.location.latitude,
            longitude=earthquake.location.longitude,
            depth=earthquake.location.depth,
            source=earthquake.source,
            title=earthquake.title,
        )
        await self._event_publisher.publish(earthquake_detected)

    async def _publish_high_magnitude_alert(self, earthquake: Earthquake) -> None:
        """Publish high magnitude alert event."""
        impact_assessment = earthquake.get_impact_assessment()
        high_magnitude_alert = HighMagnitudeAlert(
            earthquake_id=earthquake.id,
            magnitude=earthquake.magnitude.value,
            alert_level=earthquake.magnitude.get_alert_level(),
            latitude=earthquake.location.latitude,
            longitude=earthquake.location.longitude,
            affected_radius_km=impact_assessment["affected_radius_km"],
            requires_immediate_response=impact_assessment["requires_immediate_alert"],
        )
        await self._event_publisher.publish(high_magnitude_alert)
