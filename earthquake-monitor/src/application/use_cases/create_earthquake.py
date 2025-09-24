from src.application.dto.create_earthquake_request import CreateEarthquakeRequest
from src.application.services.earthquake_event_orchestrator import (
    EarthquakeEventOrchestrator,
)
from src.domain.repositories.earthquake_writer import EarthquakeWriter
from src.domain.services.earthquake_factory_service import EarthquakeFactoryService
from src.domain.services.earthquake_validation_service import (
    EarthquakeValidationService,
)


class CreateEarthquakeUseCase:
    def __init__(
        self,
        earthquake_writer: EarthquakeWriter,
        event_orchestrator: EarthquakeEventOrchestrator,
        validation_service: EarthquakeValidationService,
        factory_service: EarthquakeFactoryService,
    ):
        self._earthquake_writer = earthquake_writer
        self._event_orchestrator = event_orchestrator
        self._validation_service = validation_service
        self._factory_service = factory_service

    async def execute(self, request: CreateEarthquakeRequest) -> str:
        """Execute the create earthquake use case."""
        # Validate request data using domain service
        self._validation_service.validate_earthquake_data(
            magnitude_value=request.magnitude_value,
            magnitude_scale=request.magnitude_scale,
            latitude=request.latitude,
            longitude=request.longitude,
            depth=request.depth,
            occurred_at=request.occurred_at,
            source=request.source,
            external_id=request.external_id,
        )

        # Create earthquake entity using factory service
        earthquake = self._factory_service.create_earthquake(
            latitude=request.latitude,
            longitude=request.longitude,
            depth=request.depth,
            magnitude_value=request.magnitude_value,
            magnitude_scale=request.magnitude_scale,
            occurred_at=request.occurred_at,
            source=request.source,
            external_id=request.external_id,
            raw_data=request.raw_data,
            title=request.title,
        )

        # Save to repository (commit happens here)
        await self._earthquake_writer.save(earthquake)

        # Publish events AFTER database commit to ensure data consistency
        await self._event_orchestrator.publish_earthquake_events(earthquake)

        return earthquake.id
