import asyncio
import logging
from datetime import UTC, datetime
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
        filter_service=None,
    ):
        self._websocket_manager = websocket_manager
        self._earthquake_repository = earthquake_repository

        # Set up filtering if provided
        if filter_service:
            self._websocket_manager.set_filter_service(filter_service)

    async def _get_repository(self):
        """Get earthquake repository instance."""
        if self._earthquake_repository is None:
            # Dynamic import to get repository factory
            from src.infrastructure.database.config import (
                get_async_session_for_background,
            )
            from src.infrastructure.factory import create_earthquake_repository

            async with get_async_session_for_background() as session:
                self._earthquake_repository = await create_earthquake_repository(
                    session
                )

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
                        "title": earthquake.title,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "alert_level": earthquake.magnitude.get_alert_level(),
                    },
                }

                await self._websocket_manager.broadcast_earthquake_update(
                    earthquake_data, earthquake
                )
                # Add small delay to prevent burst sending when multiple earthquakes are processed
                await asyncio.sleep(0.15)  # 150ms delay between earthquake broadcasts

                # Only send recent earthquakes update occasionally to avoid message size issues
                # This prevents sending large lists with every single earthquake

            else:
                logger.warning(
                    f"Earthquake {event.earthquake_id} not found in database"
                )
                # Fallback to event data if not found in database
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
                            "title": event.title,
                            "timestamp": event.timestamp.isoformat(),
                        },
                    }
                )
                # Add small delay to prevent burst sending when multiple earthquakes are processed
                await asyncio.sleep(0.15)  # 150ms delay between earthquake broadcasts

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
                        "title": event.title,
                        "timestamp": event.timestamp.isoformat(),
                    },
                }
            )
            # Add small delay to prevent burst sending when multiple earthquakes are processed
            await asyncio.sleep(0.15)  # 150ms delay between earthquake broadcasts

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
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }

                await self._websocket_manager.broadcast_alert(alert_data, earthquake)

                # Only send high magnitude earthquakes update occasionally to avoid message size issues
                # This prevents sending large lists with every alert

            else:
                logger.warning(
                    f"High magnitude earthquake {event.earthquake_id} not found or not significant"
                )
                # Fallback to event data if not found in database
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
        # Temporarily disabled to prevent message size issues
        logger.info(
            "Recent earthquakes update disabled to prevent WebSocket message size issues"
        )
        return

    async def _send_high_magnitude_earthquakes_update(self) -> None:
        """Send high magnitude earthquakes list to WebSocket clients."""
        # Temporarily disabled to prevent message size issues
        logger.info(
            "High magnitude earthquakes update disabled to prevent WebSocket message size issues"
        )
        return
