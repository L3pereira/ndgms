from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.application.events.event_publisher import EventPublisher
from src.application.use_cases.create_earthquake import (
    CreateEarthquakeRequest,
    CreateEarthquakeUseCase,
)
from src.domain.repositories.earthquake_repository import EarthquakeRepository


class TestCreateEarthquakeUseCase:
    @pytest.fixture
    def mock_repository(self):
        repository = Mock(spec=EarthquakeRepository)
        repository.save = AsyncMock()
        return repository

    @pytest.fixture
    def mock_event_publisher(self):
        publisher = Mock(spec=EventPublisher)
        publisher.publish = AsyncMock()
        return publisher

    @pytest.fixture
    def use_case(self, mock_repository, mock_event_publisher):
        return CreateEarthquakeUseCase(mock_repository, mock_event_publisher)

    @pytest.mark.asyncio
    async def test_create_earthquake_success(
        self, use_case, mock_repository, mock_event_publisher
    ):
        # Arrange
        request = CreateEarthquakeRequest(
            latitude=37.7749,
            longitude=-122.4194,
            depth=10.5,
            magnitude_value=5.5,
            magnitude_scale="moment",
            occurred_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            source="USGS",
        )

        # Act
        earthquake_id = await use_case.execute(request)

        # Assert
        assert earthquake_id is not None
        assert isinstance(earthquake_id, str)
        mock_repository.save.assert_called_once()

        # Verify the earthquake passed to save has correct properties
        saved_earthquake = mock_repository.save.call_args[0][0]
        assert saved_earthquake.location.latitude == 37.7749
        assert saved_earthquake.location.longitude == -122.4194
        assert saved_earthquake.magnitude.value == 5.5
        assert saved_earthquake.source == "USGS"

    @pytest.mark.asyncio
    async def test_create_earthquake_with_defaults(
        self, use_case, mock_repository, mock_event_publisher
    ):
        # Arrange
        request = CreateEarthquakeRequest(
            latitude=37.7749,
            longitude=-122.4194,
            depth=10.5,
            magnitude_value=5.5,
        )

        # Act
        earthquake_id = await use_case.execute(request)

        # Assert
        assert earthquake_id is not None
        mock_repository.save.assert_called_once()

        saved_earthquake = mock_repository.save.call_args[0][0]
        assert saved_earthquake.source == "USGS"
        assert saved_earthquake.magnitude.scale.value == "moment"

    @pytest.mark.asyncio
    async def test_create_earthquake_publishes_events(
        self, use_case, mock_repository, mock_event_publisher
    ):
        # Arrange
        request = CreateEarthquakeRequest(
            latitude=37.7749,
            longitude=-122.4194,
            depth=10.5,
            magnitude_value=6.0,  # High magnitude to trigger alert
            magnitude_scale="moment",
            occurred_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            source="USGS",
        )

        # Act
        await use_case.execute(request)

        # Assert
        # Should publish 2 events: EarthquakeDetected + HighMagnitudeAlert (for magnitude 6.0)
        assert mock_event_publisher.publish.call_count == 2

        # Check first event (EarthquakeDetected)
        first_event = mock_event_publisher.publish.call_args_list[0][0][0]
        assert first_event.__class__.__name__ == "EarthquakeDetected"
        assert first_event.magnitude == 6.0
        assert first_event.latitude == 37.7749

        # Check second event (HighMagnitudeAlert)
        second_event = mock_event_publisher.publish.call_args_list[1][0][0]
        assert second_event.__class__.__name__ == "HighMagnitudeAlert"
        assert second_event.magnitude == 6.0
        assert second_event.alert_level == "HIGH"
