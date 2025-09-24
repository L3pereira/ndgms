"""WebSocket filtering service for intelligent earthquake broadcast filtering."""

import logging
import os
import time
from datetime import UTC, datetime, timedelta

from src.domain.entities.earthquake import Earthquake

logger = logging.getLogger(__name__)


class WebSocketFilterService:
    """Service for filtering earthquake events before WebSocket broadcast."""

    def __init__(self):
        # Configuration from environment variables
        self.min_magnitude_threshold = float(
            os.getenv("WEBSOCKET_MIN_MAGNITUDE", "2.0")
        )
        self.max_earthquakes_per_minute = int(
            os.getenv("WEBSOCKET_MAX_PER_MINUTE", "10")
        )
        self.throttle_interval_seconds = float(
            os.getenv("WEBSOCKET_THROTTLE_SECONDS", "5.0")
        )
        self.max_age_minutes = int(os.getenv("WEBSOCKET_MAX_AGE_MINUTES", "60"))

        # Client tracking
        self._client_last_broadcast: dict[str, float] = {}
        self._client_earthquake_count: dict[
            str, dict[str, int]
        ] = {}  # client_id -> {minute_key: count}

        logger.info(
            f"WebSocket filter initialized - min_magnitude: {self.min_magnitude_threshold}, "
            f"max_per_minute: {self.max_earthquakes_per_minute}, "
            f"throttle_seconds: {self.throttle_interval_seconds}"
        )

    def clear_cache(self) -> None:
        """Clear all cached filter state - useful for testing."""
        self._client_last_broadcast.clear()
        self._client_earthquake_count.clear()
        logger.info("WebSocket filter cache cleared")

    def should_broadcast_earthquake(
        self, earthquake: Earthquake, client_id: str = "default"
    ) -> bool:
        """
        Determine if an earthquake should be broadcasted to a specific client.

        Args:
            earthquake: Earthquake entity to evaluate
            client_id: WebSocket client identifier

        Returns:
            True if earthquake should be broadcasted, False otherwise
        """
        current_time = time.time()

        # 1. Magnitude filtering
        if not self._passes_magnitude_filter(earthquake):
            logger.debug(
                f"Earthquake {earthquake.id} filtered out: magnitude {earthquake.magnitude.value} < {self.min_magnitude_threshold}"
            )
            return False

        # 2. Age filtering - only recent earthquakes
        if not self._passes_age_filter(earthquake):
            logger.debug(f"Earthquake {earthquake.id} filtered out: too old")
            return False

        # 3. Time-based throttling per client
        if not self._passes_throttle_filter(client_id, current_time):
            logger.debug(
                f"Earthquake {earthquake.id} filtered out: client {client_id} throttled"
            )
            return False

        # 4. Rate limiting per client
        if not self._passes_rate_limit_filter(client_id, current_time):
            logger.debug(
                f"Earthquake {earthquake.id} filtered out: client {client_id} rate limited"
            )
            return False

        # If passes all filters, update client tracking
        self._update_client_tracking(client_id, current_time)
        logger.debug(
            f"Earthquake {earthquake.id} approved for broadcast to client {client_id}"
        )
        return True

    def should_broadcast_alert(
        self, earthquake: Earthquake, client_id: str = "default"
    ) -> bool:
        """
        Determine if a high magnitude alert should be broadcasted.
        Alerts have more relaxed filtering rules.

        Args:
            earthquake: Earthquake entity to evaluate
            client_id: WebSocket client identifier

        Returns:
            True if alert should be broadcasted, False otherwise
        """
        # Only filter by minimum significant magnitude for alerts
        if earthquake.magnitude.value < 4.0:  # Lower threshold for alerts
            logger.debug(
                f"Alert for earthquake {earthquake.id} filtered out: magnitude {earthquake.magnitude.value} < 4.0"
            )
            return False

        self._update_client_tracking(client_id, time.time())
        logger.info(
            f"High magnitude alert approved for earthquake {earthquake.id} to client {client_id}"
        )
        return True

    def _passes_magnitude_filter(self, earthquake: Earthquake) -> bool:
        """Check if earthquake meets minimum magnitude threshold."""
        return earthquake.magnitude.value >= self.min_magnitude_threshold

    def _passes_age_filter(self, earthquake: Earthquake) -> bool:
        """Check if earthquake is recent enough to be relevant."""
        max_age = timedelta(minutes=self.max_age_minutes)
        age = datetime.now(UTC) - earthquake.occurred_at.replace(tzinfo=UTC)
        return age <= max_age

    def _passes_throttle_filter(self, client_id: str, current_time: float) -> bool:
        """Check if enough time has passed since last broadcast to this client."""
        last_broadcast = self._client_last_broadcast.get(client_id, 0)
        return (current_time - last_broadcast) >= self.throttle_interval_seconds

    def _passes_rate_limit_filter(self, client_id: str, current_time: float) -> bool:
        """Check if client hasn't exceeded rate limit for this minute."""
        minute_key = str(int(current_time // 60))  # Current minute as key

        # Initialize client tracking if needed
        if client_id not in self._client_earthquake_count:
            self._client_earthquake_count[client_id] = {}

        client_counts = self._client_earthquake_count[client_id]

        # Clean old minute entries
        current_minute = int(current_time // 60)
        old_minutes = [k for k in client_counts.keys() if int(k) < current_minute - 2]
        for old_minute in old_minutes:
            del client_counts[old_minute]

        # Check current minute count
        current_count = client_counts.get(minute_key, 0)
        return current_count < self.max_earthquakes_per_minute

    def _update_client_tracking(self, client_id: str, current_time: float) -> None:
        """Update client tracking for rate limiting and throttling."""
        # Update client last broadcast time
        self._client_last_broadcast[client_id] = current_time

        # Update client rate limit counter
        minute_key = str(int(current_time // 60))
        if client_id not in self._client_earthquake_count:
            self._client_earthquake_count[client_id] = {}
        self._client_earthquake_count[client_id][minute_key] = (
            self._client_earthquake_count[client_id].get(minute_key, 0) + 1
        )

    def get_filter_stats(self) -> dict:
        """Get current filter statistics for monitoring."""
        return {
            "config": {
                "min_magnitude_threshold": self.min_magnitude_threshold,
                "max_earthquakes_per_minute": self.max_earthquakes_per_minute,
                "throttle_interval_seconds": self.throttle_interval_seconds,
                "max_age_minutes": self.max_age_minutes,
            },
            "stats": {
                "active_clients": len(self._client_last_broadcast),
                "client_rate_limit_entries": sum(
                    len(counts) for counts in self._client_earthquake_count.values()
                ),
            },
        }
