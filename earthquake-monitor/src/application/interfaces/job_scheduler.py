"""Job scheduler interface for the application layer."""

from abc import ABC, abstractmethod
from typing import Any


class JobScheduler(ABC):
    """Interface for job scheduling operations."""

    @abstractmethod
    def add_job(
        self, func: Any, trigger: str, job_id: str, name: str, **kwargs: Any
    ) -> None:
        """Add a job to the scheduler."""
        pass

    @abstractmethod
    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler."""
        pass

    @abstractmethod
    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Get the status of a specific job."""
        pass

    @abstractmethod
    def list_jobs(self) -> dict[str, dict[str, Any]]:
        """List all jobs and their status."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Start the scheduler."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the scheduler."""
        pass
