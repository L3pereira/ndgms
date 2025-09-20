import logging
from typing import TYPE_CHECKING

from src.domain.events.earthquake_detected import EarthquakeDetected
from src.domain.events.high_magnitude_alert import HighMagnitudeAlert

if TYPE_CHECKING:
    from src.infrastructure.external.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class EarthquakeEventHandlers:
    def __init__(self, websocket_manager: "WebSocketManager"):
        self._websocket_manager = websocket_manager

    async def handle_earthquake_detected(self, event: EarthquakeDetected) -> None:
        logger.info(
            f"Earthquake detected: {event.earthquake_id} with magnitude {event.magnitude}"
        )

        await self._websocket_manager.broadcast_earthquake_update(
            {
                "type": "earthquake_detected",
                "data": {
                    "id": event.earthquake_id,
                    "magnitude": event.magnitude,
                    "latitude": event.latitude,
                    "longitude": event.longitude,
                    "depth": event.depth,
                    "occurred_at": event.occurred_at.isoformat(),
                    "source": event.source,
                    "timestamp": event.timestamp.isoformat(),
                },
            }
        )

    async def handle_high_magnitude_alert(self, event: HighMagnitudeAlert) -> None:
        logger.warning(
            f"High magnitude alert: {event.earthquake_id} with magnitude {event.magnitude}"
        )

        await self._websocket_manager.broadcast_alert(
            {
                "type": "high_magnitude_alert",
                "data": {
                    "earthquake_id": event.earthquake_id,
                    "magnitude": event.magnitude,
                    "alert_level": event.alert_level,
                    "latitude": event.latitude,
                    "longitude": event.longitude,
                    "affected_radius_km": event.affected_radius_km,
                    "requires_immediate_response": event.requires_immediate_response,
                    "timestamp": event.timestamp.isoformat(),
                },
            }
        )
