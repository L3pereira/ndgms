from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

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
    def use_case(self, mock_repository):
        return CreateEarthquakeUseCase(mock_repository)

    @pytest.mark.asyncio
    async def test_create_earthquake_success(self, use_case, mock_repository):
        # Arrange
        request = CreateEarthquakeRequest(
            latitude=37.7749,
            longitude=-122.4194,
            depth=10.5,
            magnitude_value=5.5,
            magnitude_scale="moment",
            occurred_at=datetime(2024, 1, 1, 12, 0, 0),
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
    async def test_create_earthquake_with_defaults(self, use_case, mock_repository):
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
