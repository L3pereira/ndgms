"""Application service for managing scheduled jobs."""

import logging
import os
from collections.abc import Callable
from typing import Any

from src.application.interfaces.job_scheduler import JobScheduler
from src.application.use_cases.ingest_earthquake_data import (
    IngestionRequest,
    ScheduledIngestionUseCase,
)

logger = logging.getLogger(__name__)


class ScheduledJobService:
    """Application service for managing scheduled earthquake ingestion jobs."""

    def __init__(
        self,
        job_scheduler: JobScheduler,
        scheduled_ingestion_use_case: ScheduledIngestionUseCase,
    ):
        """Initialize the scheduled job service.

        Args:
            job_scheduler: The scheduler implementation to use
            scheduled_ingestion_use_case: Use case for scheduled ingestion
        """
        self._scheduler = job_scheduler
        self._ingestion_use_case = scheduled_ingestion_use_case
        self._jobs_added = False

    async def setup_earthquake_ingestion_job(self) -> None:
        """Set up the scheduled earthquake ingestion job."""
        if self._jobs_added:
            logger.warning("Earthquake ingestion job already added")
            return

        interval_minutes = float(os.getenv("USGS_INGESTION_INTERVAL_MINUTES", "30"))

        # Create the job function with proper dependency injection
        job_func = self._create_ingestion_job_func()

        self._scheduler.add_job(
            func=job_func,
            trigger="interval",
            job_id="earthquake_ingestion",
            name="Earthquake Data Ingestion",
            minutes=interval_minutes,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )

        self._jobs_added = True
        logger.info(
            f"Added earthquake ingestion job with {interval_minutes}-minute interval"
        )

    def _create_ingestion_job_func(self) -> Callable:
        """Create the ingestion job function with injected dependencies."""

        async def earthquake_ingestion_job() -> None:
            """Scheduled job for earthquake data ingestion."""
            try:
                logger.info("Starting scheduled earthquake data ingestion")

                # Get configuration from environment
                period = os.getenv("USGS_INGESTION_PERIOD", "hour")
                magnitude = os.getenv("USGS_INGESTION_MIN_MAGNITUDE", "2.5")
                max_earthquakes = int(
                    os.getenv("USGS_INGESTION_MAX_EARTHQUAKES", "100")
                )

                # Create ingestion request
                request = IngestionRequest(
                    source="USGS",
                    period=period,
                    magnitude_filter=magnitude,
                    limit=max_earthquakes,
                )

                # Execute via application layer
                result = await self._ingestion_use_case.execute(request)

                logger.info(
                    f"Earthquake ingestion completed: {result.new_earthquakes} new, "
                    f"{result.updated_earthquakes} updated, {result.errors} errors"
                )

            except Exception as e:
                logger.error(f"Earthquake data ingestion failed: {e}")
                # Don't re-raise to prevent scheduler from stopping

        return earthquake_ingestion_job

    def start_scheduler(self) -> None:
        """Start the job scheduler."""
        self._scheduler.start()

    async def stop_scheduler(self) -> None:
        """Stop the job scheduler."""
        await self._scheduler.stop()

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Get status of a specific job."""
        return self._scheduler.get_job_status(job_id)

    def list_jobs(self) -> dict[str, dict[str, Any]]:
        """List all scheduled jobs."""
        return self._scheduler.list_jobs()

    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler."""
        return self._scheduler.remove_job(job_id)
