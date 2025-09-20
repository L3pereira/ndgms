from unittest.mock import AsyncMock

import pytest

from src.application.events.event_publisher import InMemoryEventPublisher
from src.domain.events.earthquake_detected import EarthquakeDetected


class TestInMemoryEventPublisher:
    def test_subscribe_handler(self):
        publisher = InMemoryEventPublisher()
        handler = AsyncMock()

        publisher.subscribe(EarthquakeDetected, handler)

        assert EarthquakeDetected in publisher._handlers
        assert handler in publisher._handlers[EarthquakeDetected]

    @pytest.mark.asyncio
    async def test_publish_event_calls_handler(self):
        publisher = InMemoryEventPublisher()
        handler = AsyncMock()
        publisher.subscribe(EarthquakeDetected, handler)

        event = EarthquakeDetected(
            earthquake_id="test-123",
            occurred_at=None,
            magnitude=5.5,
            latitude=37.7749,
            longitude=-122.4194,
            depth=10.5,
            source="USGS",
        )

        await publisher.publish(event)

        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_event_no_handlers(self):
        publisher = InMemoryEventPublisher()

        event = EarthquakeDetected(
            earthquake_id="test-123",
            occurred_at=None,
            magnitude=5.5,
            latitude=37.7749,
            longitude=-122.4194,
            depth=10.5,
            source="USGS",
        )

        # Should not raise an exception
        await publisher.publish(event)

    @pytest.mark.asyncio
    async def test_multiple_handlers_for_same_event(self):
        publisher = InMemoryEventPublisher()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        publisher.subscribe(EarthquakeDetected, handler1)
        publisher.subscribe(EarthquakeDetected, handler2)

        event = EarthquakeDetected(
            earthquake_id="test-123",
            occurred_at=None,
            magnitude=5.5,
            latitude=37.7749,
            longitude=-122.4194,
            depth=10.5,
            source="USGS",
        )

        await publisher.publish(event)

        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)
