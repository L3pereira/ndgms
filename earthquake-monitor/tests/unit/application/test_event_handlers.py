from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.application.events.event_handlers import EarthquakeEventHandlers
from src.domain.events.earthquake_detected import EarthquakeDetected
from src.domain.events.high_magnitude_alert import HighMagnitudeAlert


class TestEarthquakeEventHandlers:
    @pytest.fixture
    def mock_websocket_manager(self):
        manager = Mock()
        manager.broadcast_earthquake_update = AsyncMock()
        manager.broadcast_alert = AsyncMock()
        return manager

    @pytest.fixture
    def event_handlers(self, mock_websocket_manager):
        return EarthquakeEventHandlers(mock_websocket_manager)

    @pytest.mark.asyncio
    async def test_handle_earthquake_detected(
        self, event_handlers, mock_websocket_manager
    ):
        event = EarthquakeDetected(
            earthquake_id="test-123",
            occurred_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            magnitude=5.5,
            latitude=37.7749,
            longitude=-122.4194,
            depth=10.5,
            source="USGS",
        )

        await event_handlers.handle_earthquake_detected(event)

        mock_websocket_manager.broadcast_earthquake_update.assert_called_once()
        call_args = mock_websocket_manager.broadcast_earthquake_update.call_args[0][0]

        assert call_args["type"] == "earthquake_detected"
        assert call_args["data"]["id"] == "test-123"
        assert call_args["data"]["magnitude"] == 5.5
        assert call_args["data"]["latitude"] == 37.7749
        assert call_args["data"]["longitude"] == -122.4194
        assert call_args["data"]["depth"] == 10.5
        assert call_args["data"]["source"] == "USGS"

    @pytest.mark.asyncio
    async def test_handle_high_magnitude_alert(
        self, event_handlers, mock_websocket_manager
    ):
        event = HighMagnitudeAlert(
            earthquake_id="test-456",
            magnitude=7.2,
            alert_level="CRITICAL",
            latitude=35.0,
            longitude=-118.0,
            affected_radius_km=150.0,
            requires_immediate_response=True,
        )

        await event_handlers.handle_high_magnitude_alert(event)

        mock_websocket_manager.broadcast_alert.assert_called_once()
        call_args = mock_websocket_manager.broadcast_alert.call_args[0][0]

        assert call_args["type"] == "high_magnitude_alert"
        assert call_args["data"]["earthquake_id"] == "test-456"
        assert call_args["data"]["magnitude"] == 7.2
        assert call_args["data"]["alert_level"] == "CRITICAL"
        assert call_args["data"]["latitude"] == 35.0
        assert call_args["data"]["longitude"] == -118.0
        assert call_args["data"]["affected_radius_km"] == 150.0
        assert call_args["data"]["requires_immediate_response"] is True
