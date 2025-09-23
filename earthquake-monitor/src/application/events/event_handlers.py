import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from src.domain.events.earthquake_detected import EarthquakeDetected
from src.domain.events.high_magnitude_alert import HighMagnitudeAlert

if TYPE_CHECKING:
    from src.domain.repositories.earthquake_repository import EarthquakeRepository
    from src.infrastructure.external.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class EarthquakeEventHandlers:
    def __init__(
        self,
        websocket_manager: "WebSocketManager",
        earthquake_repository: "EarthquakeRepository" = None,
    ):
        self._websocket_manager = websocket_manager
        self._earthquake_repository = earthquake_repository

    async def _get_repository(self):
        """Get earthquake repository instance."""
        if self._earthquake_repository is None:
            # Dynamic import to get repository factory
            from src.infrastructure.database.config import (
                get_async_session_for_background,
            )
            from src.infrastructure.factory import create_earthquake_repository

            session = await get_async_session_for_background()
            self._earthquake_repository = await create_earthquake_repository(session)

        return self._earthquake_repository

    async def handle_earthquake_detected(self, event: EarthquakeDetected) -> None:
        logger.info(
            f"Earthquake detected: {event.earthquake_id} with magnitude {event.magnitude}"
        )

        try:
            # Get repository and query database to get the actual earthquake with current state
            repository = await self._get_repository()
            earthquake = await repository.find_by_id(event.earthquake_id)

            if earthquake:
                # Send actual database data (ensures no duplicates/stale data)
                earthquake_data = {
                    "type": "earthquake_detected",
                    "data": {
                        "id": earthquake.id,
                        "magnitude": earthquake.magnitude.value,
                        "latitude": earthquake.location.latitude,
                        "longitude": earthquake.location.longitude,
                        "depth": earthquake.location.depth,
                        "occurred_at": earthquake.occurred_at.isoformat(),
                        "source": earthquake.source,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "alert_level": earthquake.magnitude.get_alert_level(),
                    },
                }

                await self._websocket_manager.broadcast_earthquake_update(
                    earthquake_data
                )

                # Also send recent earthquakes list for context (last 24 hours)
                await self._send_recent_earthquakes_update()

            else:
                logger.warning(
                    f"Earthquake {event.earthquake_id} not found in database"
                )

        except Exception as e:
            logger.error(f"Error handling earthquake detected event: {e}")
            # Fallback to event data if database query fails
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

        try:
            # Get repository and query database to get the actual high-magnitude earthquake
            repository = await self._get_repository()
            earthquake = await repository.find_by_id(event.earthquake_id)

            if earthquake and earthquake.magnitude.is_significant():
                # Send actual database data with calculated values
                alert_data = {
                    "type": "high_magnitude_alert",
                    "data": {
                        "earthquake_id": earthquake.id,
                        "magnitude": earthquake.magnitude.value,
                        "alert_level": earthquake.magnitude.get_alert_level(),
                        "latitude": earthquake.location.latitude,
                        "longitude": earthquake.location.longitude,
                        "depth": earthquake.location.depth,
                        "affected_radius_km": earthquake.calculate_affected_radius_km(),
                        "requires_immediate_response": earthquake.requires_immediate_alert(),
                        "occurred_at": earthquake.occurred_at.isoformat(),
                        "source": earthquake.source,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                }

                await self._websocket_manager.broadcast_alert(alert_data)

                # Send filtered high-magnitude earthquakes list (last 7 days, magnitude ≥5.0)
                await self._send_high_magnitude_earthquakes_update()

            else:
                logger.warning(
                    f"High magnitude earthquake {event.earthquake_id} not found or not significant"
                )

        except Exception as e:
            logger.error(f"Error handling high magnitude alert event: {e}")
            # Fallback to event data if database query fails
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

    async def _send_recent_earthquakes_update(self) -> None:
        """Send recent earthquakes list to WebSocket clients with filtering."""
        try:
            # Get recent earthquakes from last 24 hours
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)

            repository = await self._get_repository()
            recent_earthquakes = await repository.find_by_time_range(
                start_time=start_time, end_time=end_time
            )

            earthquakes_data = {
                "type": "recent_earthquakes_update",
                "data": {
                    "earthquakes": [
                        {
                            "id": eq.id,
                            "magnitude": eq.magnitude.value,
                            "latitude": eq.location.latitude,
                            "longitude": eq.location.longitude,
                            "depth": eq.location.depth,
                            "occurred_at": eq.occurred_at.isoformat(),
                            "source": eq.source,
                            "alert_level": eq.magnitude.get_alert_level(),
                        }
                        for eq in recent_earthquakes
                    ],
                    "count": len(recent_earthquakes),
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

            await self._websocket_manager.broadcast_earthquake_update(earthquakes_data)

        except Exception as e:
            logger.error(f"Error sending recent earthquakes update: {e}")

    async def _send_high_magnitude_earthquakes_update(self) -> None:
        """Send high magnitude earthquakes list to WebSocket clients."""
        try:
            # Get high magnitude earthquakes from last 7 days
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=7)

            repository = await self._get_repository()
            high_magnitude_earthquakes = await repository.find_by_magnitude_range(
                min_magnitude=5.0, start_time=start_time, end_time=end_time, limit=20
            )

            alert_data = {
                "type": "high_magnitude_earthquakes_update",
                "data": {
                    "earthquakes": [
                        {
                            "id": eq.id,
                            "magnitude": eq.magnitude.value,
                            "latitude": eq.location.latitude,
                            "longitude": eq.location.longitude,
                            "depth": eq.location.depth,
                            "occurred_at": eq.occurred_at.isoformat(),
                            "source": eq.source,
                            "alert_level": eq.magnitude.get_alert_level(),
                            "affected_radius_km": eq.calculate_affected_radius_km(),
                            "requires_immediate_response": eq.requires_immediate_alert(),
                        }
                        for eq in high_magnitude_earthquakes
                    ],
                    "count": len(high_magnitude_earthquakes),
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                    },
                    "min_magnitude": 5.0,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

            await self._websocket_manager.broadcast_alert(alert_data)

        except Exception as e:
            logger.error(f"Error sending high magnitude earthquakes update: {e}")
