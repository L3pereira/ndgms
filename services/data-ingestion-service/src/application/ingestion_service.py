"""Data ingestion orchestration service."""

import asyncio
import logging
from dataclasses import dataclass
from typing import List

from prometheus_client import Counter, Gauge, Histogram

from ..domain.disaster_event import DisasterType, ProcessedDisasterEvent, RawDisasterData
from ..infrastructure.kafka_producer import DisasterEventProducer
from ..infrastructure.usgs_service import USGSIngestionService

logger = logging.getLogger(__name__)

# Prometheus metrics
ingestion_jobs_total = Counter(
    'ingestion_jobs_total',
    'Total ingestion jobs run',
    ['source', 'disaster_type', 'status']
)

ingestion_duration = Histogram(
    'ingestion_job_duration_seconds',
    'Time spent on ingestion jobs',
    ['source', 'disaster_type']
)

events_processed = Counter(
    'disaster_events_processed_total',
    'Total disaster events processed',
    ['source', 'disaster_type', 'processing_stage']
)

active_ingestion_jobs = Gauge(
    'active_ingestion_jobs',
    'Number of currently running ingestion jobs'
)


@dataclass
class IngestionResult:
    """Result of an ingestion job."""
    total_fetched: int
    raw_published: int
    processed_published: int
    errors: int
    source: str
    disaster_type: DisasterType


class DataIngestionOrchestrator:
    """Orchestrates data ingestion from multiple sources."""

    def __init__(self):
        self.usgs_service = USGSIngestionService()
        self.kafka_producer = DisasterEventProducer()

    async def start(self):
        """Start the ingestion orchestrator."""
        await self.kafka_producer.start()
        await self.kafka_producer.create_topics_if_needed([DisasterType.EARTHQUAKE])
        logger.info("Data ingestion orchestrator started")

    async def stop(self):
        """Stop the ingestion orchestrator."""
        await self.kafka_producer.stop()
        await self.usgs_service.close()
        logger.info("Data ingestion orchestrator stopped")

    async def ingest_usgs_earthquakes(
        self, period: str = "day", magnitude: str = "all"
    ) -> IngestionResult:
        """Ingest earthquake data from USGS."""
        active_ingestion_jobs.inc()

        with ingestion_duration.labels(source="USGS", disaster_type="earthquake").time():
            try:
                logger.info(f"Starting USGS earthquake ingestion: {magnitude}_{period}")

                # Fetch raw data
                raw_data_list = await self.usgs_service.fetch_raw_earthquake_data(
                    period=period, magnitude=magnitude
                )

                events_processed.labels(
                    source="USGS",
                    disaster_type="earthquake",
                    processing_stage="fetched"
                ).inc(len(raw_data_list))

                # Process and publish data
                result = await self._process_and_publish_data(raw_data_list, "USGS")

                ingestion_jobs_total.labels(
                    source="USGS",
                    disaster_type="earthquake",
                    status="success"
                ).inc()

                logger.info(
                    f"USGS ingestion completed: {result.total_fetched} fetched, "
                    f"{result.processed_published} processed, {result.errors} errors"
                )

                return result

            except Exception as e:
                ingestion_jobs_total.labels(
                    source="USGS",
                    disaster_type="earthquake",
                    status="error"
                ).inc()
                logger.error(f"USGS ingestion failed: {e}")
                raise
            finally:
                active_ingestion_jobs.dec()

    async def _process_and_publish_data(
        self, raw_data_list: List[RawDisasterData], source: str
    ) -> IngestionResult:
        """Process raw data and publish to Kafka."""
        total_fetched = len(raw_data_list)
        raw_published = 0
        processed_published = 0
        errors = 0
        disaster_type = None

        for raw_data in raw_data_list:
            disaster_type = raw_data.disaster_type

            try:
                # Publish raw data to Kafka
                await self.kafka_producer.publish_raw_data(raw_data)
                raw_published += 1

                events_processed.labels(
                    source=source,
                    disaster_type=disaster_type.value,
                    processing_stage="raw_published"
                ).inc()

                # Process the data based on disaster type
                processed_event = None

                if disaster_type == DisasterType.EARTHQUAKE:
                    processed_event = self.usgs_service.process_earthquake_feature(raw_data)

                if processed_event:
                    # Publish processed event to Kafka
                    await self.kafka_producer.publish_processed_event(processed_event)
                    processed_published += 1

                    events_processed.labels(
                        source=source,
                        disaster_type=disaster_type.value,
                        processing_stage="processed_published"
                    ).inc()

                    logger.debug(
                        f"Published processed event: {processed_event.event_id} "
                        f"(external: {processed_event.external_id})"
                    )
                else:
                    errors += 1
                    logger.warning(f"Failed to process raw data: {raw_data.external_id}")

            except Exception as e:
                errors += 1
                logger.error(f"Error processing {raw_data.external_id}: {e}")

        return IngestionResult(
            total_fetched=total_fetched,
            raw_published=raw_published,
            processed_published=processed_published,
            errors=errors,
            source=source,
            disaster_type=disaster_type or DisasterType.EARTHQUAKE
        )

    async def health_check(self) -> dict:
        """Check health of ingestion services."""
        health = {
            "status": "healthy",
            "services": {}
        }

        # Check USGS service
        try:
            feeds = await self.usgs_service.get_available_feeds()
            health["services"]["usgs"] = {
                "status": "healthy",
                "feeds_available": len(feeds.get("real_time", {}))
            }
        except Exception as e:
            health["services"]["usgs"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"

        # Check Kafka producer
        if self.kafka_producer.producer:
            health["services"]["kafka"] = {"status": "healthy"}
        else:
            health["services"]["kafka"] = {"status": "unhealthy", "error": "Producer not started"}
            health["status"] = "degraded"

        return health
