"""Use case for ingesting earthquake data from external sources."""

import logging
from dataclasses import dataclass
from typing import List, Optional

from src.application.events.event_publisher import EventPublisher
from src.domain.entities.earthquake import Earthquake
from src.domain.events.earthquake_detected import EarthquakeDetected
from src.domain.events.high_magnitude_alert import HighMagnitudeAlert
from src.domain.repositories.earthquake_repository import EarthquakeRepository

logger = logging.getLogger(__name__)


@dataclass
class IngestionRequest:
    """Request for earthquake data ingestion."""

    source: str
    period: str = "day"
    magnitude_filter: str = "all"
    limit: Optional[int] = None


@dataclass
class IngestionResult:
    """Result of earthquake data ingestion."""

    total_fetched: int
    new_earthquakes: int
    updated_earthquakes: int
    errors: int
    earthquake_ids: List[str]


class IngestEarthquakeDataUseCase:
    """Use case for ingesting earthquake data from external sources."""

    def __init__(
        self, repository: EarthquakeRepository, event_publisher: EventPublisher
    ):
        self.repository = repository
        self.event_publisher = event_publisher

    async def execute(
        self, earthquakes: List[Earthquake], source: str = "USGS"
    ) -> IngestionResult:
        """
        Ingest a list of earthquakes into the system.

        Args:
            earthquakes: List of earthquake entities to ingest
            source: Source of the earthquake data

        Returns:
            IngestionResult with statistics
        """
        logger.info(
            f"Starting ingestion of {len(earthquakes)} earthquakes from {source}"
        )

        new_earthquakes = 0
        updated_earthquakes = 0
        errors = 0
        earthquake_ids = []

        for earthquake in earthquakes:
            try:
                # Check if earthquake already exists (by external_id if available)
                existing_earthquake = None
                if hasattr(earthquake, "external_id") and earthquake.external_id:
                    # For now, we'll check by ID since we don't have a find_by_external_id method
                    # This would be a good enhancement to add to the repository interface
                    existing_earthquake = await self.repository.find_by_id(
                        earthquake.id
                    )

                if existing_earthquake:
                    # Update existing earthquake (could implement update logic here)
                    updated_earthquakes += 1
                    logger.debug(f"Earthquake {earthquake.id} already exists, skipping")
                else:
                    # Save new earthquake
                    earthquake_id = await self.repository.save(earthquake)
                    earthquake_ids.append(earthquake_id)
                    new_earthquakes += 1

                    # Publish domain events
                    await self._publish_events(earthquake)

                    logger.debug(f"Successfully ingested earthquake {earthquake_id}")

            except Exception as e:
                errors += 1
                logger.error(f"Error ingesting earthquake {earthquake.id}: {e}")

        result = IngestionResult(
            total_fetched=len(earthquakes),
            new_earthquakes=new_earthquakes,
            updated_earthquakes=updated_earthquakes,
            errors=errors,
            earthquake_ids=earthquake_ids,
        )

        logger.info(
            f"Ingestion completed: {new_earthquakes} new, "
            f"{updated_earthquakes} updated, {errors} errors"
        )

        return result

    async def _publish_events(self, earthquake: Earthquake) -> None:
        """Publish domain events for an ingested earthquake."""
        try:
            # Always publish earthquake detected event
            earthquake_detected = EarthquakeDetected(
                earthquake_id=earthquake.id,
                magnitude=earthquake.magnitude.value,
                latitude=earthquake.location.latitude,
                longitude=earthquake.location.longitude,
                depth=earthquake.location.depth,
                occurred_at=earthquake.occurred_at,
                source=earthquake.source,
            )
            await self.event_publisher.publish(earthquake_detected)

            # Publish high magnitude alert if significant
            if earthquake.magnitude.is_significant():
                high_magnitude_alert = HighMagnitudeAlert(
                    earthquake_id=earthquake.id,
                    magnitude=earthquake.magnitude.value,
                    latitude=earthquake.location.latitude,
                    longitude=earthquake.location.longitude,
                    affected_radius_km=50.0,  # Default radius
                    alert_level=earthquake.magnitude.get_alert_level(),
                    requires_immediate_response=earthquake.requires_immediate_alert(),
                )
                await self.event_publisher.publish(high_magnitude_alert)

        except Exception as e:
            logger.error(f"Error publishing events for earthquake {earthquake.id}: {e}")


class ScheduledIngestionUseCase:
    """Use case for scheduled earthquake data ingestion."""

    def __init__(
        self,
        repository: EarthquakeRepository,
        event_publisher: EventPublisher,
        usgs_service,
    ):
        self.repository = repository
        self.event_publisher = event_publisher
        self.usgs_service = usgs_service
        self.ingest_use_case = IngestEarthquakeDataUseCase(repository, event_publisher)

    async def execute(self, request: IngestionRequest) -> IngestionResult:
        """
        Execute scheduled ingestion from external source.

        Args:
            request: Ingestion parameters

        Returns:
            IngestionResult with statistics
        """
        logger.info(f"Starting scheduled ingestion from {request.source}")

        try:
            if request.source.upper() == "USGS":
                earthquakes = await self.usgs_service.fetch_recent_earthquakes(
                    period=request.period, magnitude=request.magnitude_filter
                )

                if request.limit:
                    earthquakes = earthquakes[: request.limit]

                return await self.ingest_use_case.execute(earthquakes, "USGS")
            else:
                raise ValueError(f"Unsupported source: {request.source}")

        except Exception as e:
            logger.error(f"Error during scheduled ingestion: {e}")
            return IngestionResult(
                total_fetched=0,
                new_earthquakes=0,
                updated_earthquakes=0,
                errors=1,
                earthquake_ids=[],
            )
