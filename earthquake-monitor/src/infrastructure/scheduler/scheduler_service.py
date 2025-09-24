"""Async scheduler service for periodic tasks using AsyncIOScheduler."""

import logging
import os
from typing import Any

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.domain.repositories.earthquake_repository import EarthquakeRepository
from src.infrastructure.external.usgs_service import USGSService

logger = logging.getLogger(__name__)


async def ingest_usgs_data_async() -> None:
    """Async task to ingest earthquake data from USGS."""
    try:
        logger.info("Starting scheduled USGS data ingestion")

        # Initialize USGS service
        usgs_service = USGSService()

        # Configure based on environment variables
        period = os.getenv("USGS_INGESTION_PERIOD", "hour")
        magnitude = os.getenv("USGS_INGESTION_MIN_MAGNITUDE", "2.5")

        earthquakes = await usgs_service.fetch_recent_earthquakes(
            period=period, magnitude=magnitude
        )

        # Limit the number of earthquakes to prevent huge datasets
        max_earthquakes = int(os.getenv("USGS_INGESTION_MAX_EARTHQUAKES", "100"))
        if len(earthquakes) > max_earthquakes:
            logger.warning(
                f"USGS returned {len(earthquakes)} earthquakes, limiting to {max_earthquakes}"
            )
            earthquakes = earthquakes[:max_earthquakes]

        # Use proper application layer with event publishing
        from src.application.use_cases.ingest_earthquake_data import (
            IngestEarthquakeDataUseCase,
        )
        from src.infrastructure.database.config import get_async_session_for_background
        from src.infrastructure.factory import create_earthquake_repository
        from src.presentation.main import get_event_publisher

        processed_count = 0

        # ✅ Clean async context manager for DB session
        async with get_async_session_for_background() as session:
            earthquake_repo: EarthquakeRepository = await create_earthquake_repository(
                session
            )
            event_publisher = get_event_publisher()

            ingest_use_case = IngestEarthquakeDataUseCase(
                repository=earthquake_repo, event_publisher=event_publisher
            )

            # Execute ingestion with proper event publishing
            result = await ingest_use_case.execute(earthquakes)
            processed_count = result.new_earthquakes

            # Commit all changes
            await session.commit()

        logger.info(
            f"USGS ingestion completed: processed {processed_count} earthquakes"
        )

    except Exception as e:
        logger.error(f"USGS data ingestion failed: {e}")
        # Don't re-raise to prevent scheduler from stopping


class SchedulerService:
    """Manages async scheduled tasks using AsyncIOScheduler."""

    def __init__(self, scheduler: AsyncIOScheduler | None = None):
        """Initialize async scheduler service."""
        self.scheduler = scheduler or AsyncIOScheduler(
            executors={"default": AsyncIOExecutor()}, timezone="UTC"
        )
        self._jobs_added = False

    async def add_usgs_ingestion_job(self) -> None:
        """Add USGS ingestion job to the async scheduler."""
        if self._jobs_added:
            logger.warning("USGS ingestion job already added")
            return

        interval_minutes = float(os.getenv("USGS_INGESTION_INTERVAL_MINUTES", "30"))

        self.scheduler.add_job(
            ingest_usgs_data_async,
            "interval",
            minutes=interval_minutes,
            id="usgs_ingestion",
            name="USGS Earthquake Data Ingestion",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )
        self._jobs_added = True
        logger.info(f"Added USGS ingestion job with {interval_minutes}-minute interval")

    def start(self) -> None:
        """Start the scheduler service."""
        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return

        self.scheduler.start()
        logger.info("AsyncIO scheduler started with UTC timezone")

    async def stop(self) -> None:
        """Stop the scheduler service."""
        if not self.scheduler.running:
            return

        self.scheduler.shutdown(wait=False)

        import asyncio

        await asyncio.sleep(0.1)

        logger.info("AsyncIO scheduler stopped")

    async def restart(self) -> None:
        """Restart the scheduler and re-add jobs."""
        await self.stop()

        self.scheduler = AsyncIOScheduler(
            executors={"default": AsyncIOExecutor()}, timezone="UTC"
        )

        if self._jobs_added:
            self._jobs_added = False
            await self.add_usgs_ingestion_job()

        self.start()

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Get status of a specific job."""
        job = self.scheduler.get_job(job_id)
        if job is None:
            return None

        return {
            "id": job.id,
            "name": job.name,
            "next_run": str(getattr(job, "next_run_time", "N/A")),
            "trigger": str(job.trigger),
        }

    def list_jobs(self) -> dict[str, dict[str, Any]]:
        """List all scheduled jobs and their status."""
        jobs = {}
        for job in self.scheduler.get_jobs():
            jobs[job.id] = {
                "id": job.id,
                "name": job.name,
                "next_run": str(getattr(job, "next_run_time", "N/A")),
                "trigger": str(job.trigger),
            }
        return jobs

    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            return False


# Global scheduler instance for production use
_global_scheduler_service: SchedulerService | None = None


async def get_scheduler_service() -> SchedulerService:
    """Get or create the global scheduler service instance with async initialization."""
    global _global_scheduler_service

    if _global_scheduler_service is None:
        _global_scheduler_service = SchedulerService()
        await _global_scheduler_service.add_usgs_ingestion_job()

    return _global_scheduler_service


async def start_scheduler() -> None:
    """Start the global scheduler service."""
    scheduler_service = await get_scheduler_service()
    scheduler_service.start()


async def stop_scheduler() -> None:
    """Stop the global scheduler service."""
    global _global_scheduler_service

    if _global_scheduler_service is not None:
        await _global_scheduler_service.stop()
