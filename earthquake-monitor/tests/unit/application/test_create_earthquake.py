from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.application.dto.create_earthquake_request import CreateEarthquakeRequest
from src.application.services.earthquake_event_orchestrator import (
    EarthquakeEventOrchestrator,
)
from src.application.use_cases.create_earthquake import CreateEarthquakeUseCase
from src.domain.repositories.earthquake_writer import EarthquakeWriter
from src.domain.services.earthquake_factory_service import EarthquakeFactoryService
from src.domain.services.earthquake_validation_service import (
    EarthquakeValidationService,
)


class TestCreateEarthquakeUseCase:
    @pytest.fixture
    def mock_writer(self):
        writer = Mock(spec=EarthquakeWriter)
        writer.save = AsyncMock()
        return writer

    @pytest.fixture
    def mock_event_orchestrator(self):
        orchestrator = Mock(spec=EarthquakeEventOrchestrator)
        orchestrator.publish_earthquake_events = AsyncMock()
        return orchestrator

    @pytest.fixture
    def mock_validation_service(self):
        service = Mock(spec=EarthquakeValidationService)
        service.validate_earthquake_data = Mock()
        return service

    @pytest.fixture
    def mock_factory_service(self):
        return EarthquakeFactoryService()  # Use real factory service

    @pytest.fixture
    def use_case(
        self,
        mock_writer,
        mock_event_orchestrator,
        mock_validation_service,
        mock_factory_service,
    ):
        return CreateEarthquakeUseCase(
            mock_writer,
            mock_event_orchestrator,
            mock_validation_service,
            mock_factory_service,
        )

    @pytest.mark.asyncio
    async def test_create_earthquake_success(
        self, use_case, mock_writer, mock_event_orchestrator, mock_validation_service
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
        mock_validation_service.validate_earthquake_data.assert_called_once()
        mock_writer.save.assert_called_once()
        mock_event_orchestrator.publish_earthquake_events.assert_called_once()

        # Verify the earthquake passed to save has correct properties
        saved_earthquake = mock_writer.save.call_args[0][0]
        assert saved_earthquake.location.latitude == 37.7749
        assert saved_earthquake.location.longitude == -122.4194
        assert saved_earthquake.magnitude.value == 5.5
        assert saved_earthquake.source == "USGS"

    @pytest.mark.asyncio
    async def test_create_earthquake_with_defaults(
        self, use_case, mock_writer, mock_event_orchestrator
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
        mock_writer.save.assert_called_once()

        saved_earthquake = mock_writer.save.call_args[0][0]
        assert saved_earthquake.source == "USGS"
        assert saved_earthquake.magnitude.scale.value == "moment"

    @pytest.mark.asyncio
    async def test_create_earthquake_publishes_events(
        self, use_case, mock_writer, mock_event_orchestrator
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
        # Event orchestrator should be called once (it handles all event publishing internally)
        mock_event_orchestrator.publish_earthquake_events.assert_called_once()

        # Verify the earthquake passed to the event orchestrator has the correct properties
        published_earthquake = (
            mock_event_orchestrator.publish_earthquake_events.call_args[0][0]
        )
        assert published_earthquake.magnitude.value == 6.0
        assert published_earthquake.location.latitude == 37.7749
