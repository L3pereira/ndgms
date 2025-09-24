from src.domain.entities.earthquake import Earthquake
from src.domain.repositories.earthquake_reader import EarthquakeReader


class GetEarthquakeDetailsUseCase:
    def __init__(self, earthquake_reader: EarthquakeReader):
        self._earthquake_reader = earthquake_reader

    async def execute(self, earthquake_id: str) -> Earthquake | None:
        return await self._earthquake_reader.find_by_id(earthquake_id)
