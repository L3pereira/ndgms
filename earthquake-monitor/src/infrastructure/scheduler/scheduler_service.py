"""Infrastructure scheduler service implementing APScheduler."""

import logging
from typing import Any

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.application.interfaces.job_scheduler import JobScheduler

logger = logging.getLogger(__name__)


class APSchedulerService(JobScheduler):
    """Infrastructure implementation of JobScheduler using APScheduler."""

    def __init__(self, scheduler: AsyncIOScheduler | None = None):
        """Initialize APScheduler service."""
        self.scheduler = scheduler or AsyncIOScheduler(
            executors={"default": AsyncIOExecutor()}, timezone="UTC"
        )

    def add_job(
        self, func: Any, trigger: str, job_id: str, name: str, **kwargs: Any
    ) -> None:
        """Add a job to the scheduler."""
        self.scheduler.add_job(
            func=func, trigger=trigger, id=job_id, name=name, **kwargs
        )
        logger.info(f"Added job: {name} ({job_id})")

    def start(self) -> None:
        """Start the scheduler service."""
        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return

        self.scheduler.start()
        logger.info("APScheduler started with UTC timezone")

    async def stop(self) -> None:
        """Stop the scheduler service."""
        if not self.scheduler.running:
            return

        self.scheduler.shutdown(wait=False)

        import asyncio

        await asyncio.sleep(0.1)

        logger.info("APScheduler stopped")

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


# Maintain backward compatibility alias
SchedulerService = APSchedulerService
