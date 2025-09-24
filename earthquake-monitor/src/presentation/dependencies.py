from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.events.event_publisher import EventPublisher
from src.application.services.earthquake_event_orchestrator import (
    EarthquakeEventOrchestrator,
)
from src.application.use_cases.create_earthquake import CreateEarthquakeUseCase
from src.application.use_cases.get_earthquake_details import GetEarthquakeDetailsUseCase
from src.application.use_cases.get_earthquakes import GetEarthquakesUseCase
from src.domain.repositories.earthquake_reader import EarthquakeReader
from src.domain.repositories.earthquake_repository import EarthquakeRepository
from src.domain.repositories.earthquake_search import EarthquakeSearch
from src.domain.repositories.earthquake_writer import EarthquakeWriter
from src.domain.services.earthquake_factory_service import EarthquakeFactoryService
from src.domain.services.earthquake_validation_service import (
    EarthquakeValidationService,
)
from src.infrastructure.database.config import get_async_session


# For now, we'll use a mock repository for demonstration
# In a real application, this would be replaced with actual database implementation
class MockEarthquakeRepository(EarthquakeRepository):
    def __init__(self):
        self._earthquakes = {}

    async def save(self, earthquake) -> str:
        self._earthquakes[earthquake.id] = earthquake
        return earthquake.id

    async def find_by_id(self, earthquake_id: str):
        return self._earthquakes.get(earthquake_id)

    async def exists(self, earthquake_id: str) -> bool:
        return earthquake_id in self._earthquakes

    async def find_by_magnitude_range(self, min_magnitude: float, max_magnitude=None):
        results = []
        for earthquake in self._earthquakes.values():
            mag = earthquake.magnitude.value
            if mag >= min_magnitude:
                if max_magnitude is None or mag <= max_magnitude:
                    results.append(earthquake)
        return results

    async def find_by_time_range(self, start_time, end_time):
        results = []
        for earthquake in self._earthquakes.values():
            if start_time <= earthquake.occurred_at <= end_time:
                results.append(earthquake)
        return results

    async def find_by_location_radius(
        self, latitude: float, longitude: float, radius_km: float
    ):
        results = []
        for earthquake in self._earthquakes.values():
            distance = earthquake.location.distance_to(
                type(earthquake.location)(latitude, longitude, 0)
            )
            if distance <= radius_km:
                results.append(earthquake)
        return results

    async def find_unreviewed(self):
        return [eq for eq in self._earthquakes.values() if not eq.is_reviewed]

    async def find_with_filters(self, filters=None, limit=None, offset=None):
        results = list(self._earthquakes.values())

        if filters:
            if filters.get("min_magnitude"):
                results = [
                    eq
                    for eq in results
                    if eq.magnitude.value >= filters["min_magnitude"]
                ]
            if filters.get("max_magnitude"):
                results = [
                    eq
                    for eq in results
                    if eq.magnitude.value <= filters["max_magnitude"]
                ]
            if filters.get("start_time"):
                results = [
                    eq for eq in results if eq.occurred_at >= filters["start_time"]
                ]
            if filters.get("end_time"):
                results = [
                    eq for eq in results if eq.occurred_at <= filters["end_time"]
                ]
            if filters.get("is_reviewed") is not None:
                results = [
                    eq for eq in results if eq.is_reviewed == filters["is_reviewed"]
                ]
            if filters.get("source"):
                results = [eq for eq in results if eq.source == filters["source"]]

        # Sort by occurred_at descending (newest first)
        results.sort(key=lambda x: x.occurred_at, reverse=True)

        # Apply pagination
        if offset:
            results = results[offset:]
        if limit:
            results = results[:limit]

        return results

    async def count_with_filters(self, filters=None):
        results = list(self._earthquakes.values())

        if filters:
            if filters.get("min_magnitude"):
                results = [
                    eq
                    for eq in results
                    if eq.magnitude.value >= filters["min_magnitude"]
                ]
            if filters.get("max_magnitude"):
                results = [
                    eq
                    for eq in results
                    if eq.magnitude.value <= filters["max_magnitude"]
                ]
            if filters.get("start_time"):
                results = [
                    eq for eq in results if eq.occurred_at >= filters["start_time"]
                ]
            if filters.get("end_time"):
                results = [
                    eq for eq in results if eq.occurred_at <= filters["end_time"]
                ]
            if filters.get("is_reviewed") is not None:
                results = [
                    eq for eq in results if eq.is_reviewed == filters["is_reviewed"]
                ]
            if filters.get("source"):
                results = [eq for eq in results if eq.source == filters["source"]]

        return len(results)

    async def find_all(self):
        """Find all earthquakes."""
        results = list(self._earthquakes.values())
        # Sort by occurred_at descending (newest first)
        results.sort(key=lambda x: x.occurred_at, reverse=True)
        return results


# Import repository directly to avoid dependency function issues
def get_earthquake_repository(
    session: AsyncSession = Depends(get_async_session),
) -> EarthquakeRepository:
    """Get earthquake repository instance directly."""
    from src.infrastructure.repositories.postgresql_earthquake_repository import (
        PostgreSQLEarthquakeRepository,
    )

    return PostgreSQLEarthquakeRepository(session)


def get_event_publisher() -> EventPublisher:
    from .main import get_event_publisher

    return get_event_publisher()


def get_earthquake_validation_service() -> EarthquakeValidationService:
    """Get earthquake validation service."""
    return EarthquakeValidationService()


def get_earthquake_factory_service() -> EarthquakeFactoryService:
    """Get earthquake factory service."""
    return EarthquakeFactoryService()


def get_earthquake_event_orchestrator(
    event_publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
) -> EarthquakeEventOrchestrator:
    """Get earthquake event orchestrator."""
    return EarthquakeEventOrchestrator(event_publisher)


def get_create_earthquake_use_case(
    earthquake_writer: Annotated[EarthquakeWriter, Depends(get_earthquake_repository)],
    event_orchestrator: Annotated[
        EarthquakeEventOrchestrator, Depends(get_earthquake_event_orchestrator)
    ],
    validation_service: Annotated[
        EarthquakeValidationService, Depends(get_earthquake_validation_service)
    ],
    factory_service: Annotated[
        EarthquakeFactoryService, Depends(get_earthquake_factory_service)
    ],
) -> CreateEarthquakeUseCase:
    return CreateEarthquakeUseCase(
        earthquake_writer, event_orchestrator, validation_service, factory_service
    )


def get_get_earthquakes_use_case(
    earthquake_search: Annotated[EarthquakeSearch, Depends(get_earthquake_repository)],
) -> GetEarthquakesUseCase:
    return GetEarthquakesUseCase(earthquake_search)


def get_get_earthquake_details_use_case(
    earthquake_reader: Annotated[EarthquakeReader, Depends(get_earthquake_repository)],
) -> GetEarthquakeDetailsUseCase:
    return GetEarthquakeDetailsUseCase(earthquake_reader)
