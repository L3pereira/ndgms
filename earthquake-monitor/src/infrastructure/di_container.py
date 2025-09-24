"""Dependency injection container for the earthquake monitoring system."""

from typing import Protocol, runtime_checkable

from src.application.events.event_publisher import (
    EventPublisher,
    InMemoryEventPublisher,
)
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


@runtime_checkable
class DIContainer(Protocol):
    """Protocol for dependency injection container."""

    def get_earthquake_writer(self) -> EarthquakeWriter:
        """Get earthquake writer instance."""
        ...

    def get_earthquake_reader(self) -> EarthquakeReader:
        """Get earthquake reader instance."""
        ...

    def get_earthquake_search(self) -> EarthquakeSearch:
        """Get earthquake search instance."""
        ...

    def get_earthquake_repository(self) -> EarthquakeRepository:
        """Get full earthquake repository instance."""
        ...

    def get_event_publisher(self) -> EventPublisher:
        """Get event publisher instance."""
        ...

    def get_validation_service(self) -> EarthquakeValidationService:
        """Get validation service instance."""
        ...

    def get_factory_service(self) -> EarthquakeFactoryService:
        """Get factory service instance."""
        ...

    def get_event_orchestrator(self) -> EarthquakeEventOrchestrator:
        """Get event orchestrator instance."""
        ...

    def get_create_earthquake_use_case(self) -> CreateEarthquakeUseCase:
        """Get create earthquake use case instance."""
        ...

    def get_get_earthquakes_use_case(self) -> GetEarthquakesUseCase:
        """Get list earthquakes use case instance."""
        ...

    def get_get_earthquake_details_use_case(self) -> GetEarthquakeDetailsUseCase:
        """Get earthquake details use case instance."""
        ...


class ApplicationDIContainer:
    """Dependency injection container for the application."""

    def __init__(self, earthquake_repository: EarthquakeRepository):
        """Initialize container with repository instance."""
        self._earthquake_repository = earthquake_repository
        self._singletons = {}

    def _get_singleton(self, key: str, factory_func):
        """Get or create singleton instance."""
        if key not in self._singletons:
            self._singletons[key] = factory_func()
        return self._singletons[key]

    def get_earthquake_writer(self) -> EarthquakeWriter:
        """Get earthquake writer instance."""
        return self._earthquake_repository

    def get_earthquake_reader(self) -> EarthquakeReader:
        """Get earthquake reader instance."""
        return self._earthquake_repository

    def get_earthquake_search(self) -> EarthquakeSearch:
        """Get earthquake search instance."""
        return self._earthquake_repository

    def get_earthquake_repository(self) -> EarthquakeRepository:
        """Get full earthquake repository instance."""
        return self._earthquake_repository

    def get_event_publisher(self) -> EventPublisher:
        """Get event publisher instance."""
        return self._get_singleton("event_publisher", InMemoryEventPublisher)

    def get_validation_service(self) -> EarthquakeValidationService:
        """Get validation service instance."""
        return self._get_singleton("validation_service", EarthquakeValidationService)

    def get_factory_service(self) -> EarthquakeFactoryService:
        """Get factory service instance."""
        return self._get_singleton("factory_service", EarthquakeFactoryService)

    def get_event_orchestrator(self) -> EarthquakeEventOrchestrator:
        """Get event orchestrator instance."""
        return self._get_singleton(
            "event_orchestrator",
            lambda: EarthquakeEventOrchestrator(self.get_event_publisher()),
        )

    def get_create_earthquake_use_case(self) -> CreateEarthquakeUseCase:
        """Get create earthquake use case instance."""
        return CreateEarthquakeUseCase(
            earthquake_writer=self.get_earthquake_writer(),
            event_orchestrator=self.get_event_orchestrator(),
            validation_service=self.get_validation_service(),
            factory_service=self.get_factory_service(),
        )

    def get_get_earthquakes_use_case(self) -> GetEarthquakesUseCase:
        """Get list earthquakes use case instance."""
        return GetEarthquakesUseCase(self.get_earthquake_search())

    def get_get_earthquake_details_use_case(self) -> GetEarthquakeDetailsUseCase:
        """Get earthquake details use case instance."""
        return GetEarthquakeDetailsUseCase(self.get_earthquake_reader())
