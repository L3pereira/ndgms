from typing import Annotated

from fastapi import Depends

from src.application.use_cases.create_earthquake import CreateEarthquakeUseCase
from src.domain.repositories.earthquake_repository import EarthquakeRepository


# For now, we'll use a mock repository for demonstration
# In a real application, this would be replaced with actual database implementation
class MockEarthquakeRepository(EarthquakeRepository):
    def __init__(self):
        self._earthquakes = {}

    async def save(self, earthquake) -> None:
        self._earthquakes[earthquake.id] = earthquake

    async def find_by_id(self, earthquake_id: str):
        return self._earthquakes.get(earthquake_id)

    async def exists(self, earthquake_id: str) -> bool:
        return earthquake_id in self._earthquakes

    async def find_by_magnitude_range(self, min_magnitude: float, max_magnitude=None):
        return []

    async def find_by_time_range(self, start_time, end_time):
        return []

    async def find_by_location_radius(
        self, latitude: float, longitude: float, radius_km: float
    ):
        return []

    async def find_unreviewed(self):
        return []


def get_earthquake_repository() -> EarthquakeRepository:
    return MockEarthquakeRepository()


def get_create_earthquake_use_case(
    repository: Annotated[EarthquakeRepository, Depends(get_earthquake_repository)],
) -> CreateEarthquakeUseCase:
    return CreateEarthquakeUseCase(repository)
