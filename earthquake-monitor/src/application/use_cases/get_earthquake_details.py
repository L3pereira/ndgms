from src.domain.entities.earthquake import Earthquake
from src.domain.repositories.earthquake_repository import EarthquakeRepository


class GetEarthquakeDetailsUseCase:
    def __init__(self, earthquake_repository: EarthquakeRepository):
        self._earthquake_repository = earthquake_repository

    async def execute(self, earthquake_id: str) -> Earthquake | None:
        return await self._earthquake_repository.find_by_id(earthquake_id)
