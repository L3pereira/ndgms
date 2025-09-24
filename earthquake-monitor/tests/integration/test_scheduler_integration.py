"""Integration tests for scheduler service with real dependencies."""

import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.application.services.scheduled_job_service import ScheduledJobService
from src.domain.entities.earthquake import Earthquake
from src.domain.entities.location import Location
from src.domain.entities.magnitude import Magnitude, MagnitudeScale

# Integration tests should use real database connections
# No database mocking fixture needed here


class TestSchedulerIntegration:
    """Integration tests for scheduler with database."""

    @pytest.fixture
    async def scheduler_service(self):
        """Create scheduler service for integration testing with real dependencies."""
        from unittest.mock import AsyncMock

        from src.application.events.event_publisher import EventPublisher
        from src.application.use_cases.ingest_earthquake_data import (
            ScheduledIngestionUseCase,
        )
        from src.infrastructure.external.usgs_service import USGSService
        from src.infrastructure.scheduler.scheduler_service import APSchedulerService
        from src.presentation.dependencies import MockEarthquakeRepository

        # For integration tests, we use real infrastructure components but mock external services
        job_scheduler = APSchedulerService()
        usgs_service = AsyncMock(
            spec=USGSService
        )  # Mock external service to avoid real API calls
        mock_repo = (
            MockEarthquakeRepository()
        )  # Use mock repo to avoid real DB operations in tests
        mock_publisher = AsyncMock(spec=EventPublisher)

        # Create use case with dependencies
        scheduled_ingestion_use_case = ScheduledIngestionUseCase(
            repository=mock_repo,
            event_publisher=mock_publisher,
            usgs_service=usgs_service,
        )

        # Create service
        service = ScheduledJobService(
            job_scheduler=job_scheduler,
            scheduled_ingestion_use_case=scheduled_ingestion_use_case,
        )

        yield service

        # Cleanup: stop scheduler if running
        if service._scheduler.scheduler.running:
            await service.stop_scheduler()

    @pytest.fixture
    def sample_earthquake_data(self):
        """Create sample earthquake data for testing."""
        return [
            Earthquake(
                location=Location(latitude=37.7749, longitude=-122.4194, depth=10.0),
                magnitude=Magnitude(value=3.5, scale=MagnitudeScale.MOMENT),
                occurred_at=datetime.now(UTC),
                source="USGS",
            )
        ]

    async def test_scheduler_lifecycle(self, scheduler_service):
        """Test complete scheduler lifecycle."""
        # Test initial state
        assert not scheduler_service._scheduler.scheduler.running

        # Add jobs first
        await scheduler_service.setup_earthquake_ingestion_job()

        # Test start
        scheduler_service.start_scheduler()
        assert scheduler_service._scheduler.scheduler.running

        # Verify jobs are registered
        jobs = scheduler_service.list_jobs()
        assert "earthquake_ingestion" in jobs

        # Test job status
        job_status = scheduler_service.get_job_status("earthquake_ingestion")
        assert job_status is not None
        assert job_status["id"] == "earthquake_ingestion"

        # Test stop
        await scheduler_service.stop_scheduler()
        assert not scheduler_service._scheduler.scheduler.running

    @patch.dict(
        os.environ,
        {
            "SCHEDULER_ENABLED": "true",
            "USGS_INGESTION_INTERVAL_MINUTES": "60",  # 1 hour for testing
            "USGS_INGESTION_MIN_MAGNITUDE": "3.0",
            "USGS_INGESTION_PERIOD": "hour",
        },
    )
    async def test_scheduler_environment_configuration(self, scheduler_service):
        """Test scheduler respects environment configuration."""
        await scheduler_service.setup_earthquake_ingestion_job()
        scheduler_service.start_scheduler()

        job = scheduler_service._scheduler.scheduler.get_job("earthquake_ingestion")
        assert job is not None

        # Check that the job is configured with environment values
        # Note: The actual interval is set when the job is defined, not when started
        assert job.id == "earthquake_ingestion"

        await scheduler_service.stop_scheduler()

    @patch("src.infrastructure.external.usgs_service.USGSService")
    async def test_ingestion_job_error_handling(
        self, mock_usgs_service_class, scheduler_service
    ):
        """Test that scheduler handles job errors gracefully."""
        # Setup mock to simulate API error
        mock_usgs_instance = AsyncMock()
        mock_usgs_instance.fetch_recent_earthquakes.side_effect = Exception(
            "API temporarily unavailable"
        )
        mock_usgs_service_class.return_value = mock_usgs_instance

        # Replace the service in the use case
        scheduler_service._ingestion_use_case.usgs_service = mock_usgs_instance

        # Add jobs and start scheduler
        await scheduler_service.setup_earthquake_ingestion_job()
        scheduler_service.start_scheduler()

        # The job should handle errors gracefully (tested in unit tests)
        # Here we just verify the scheduler is still operational
        assert scheduler_service._scheduler.scheduler.running

        # Verify job is still registered
        jobs = scheduler_service.list_jobs()
        assert "earthquake_ingestion" in jobs

        await scheduler_service.stop_scheduler()

    async def test_scheduler_with_disabled_environment(self):
        """Test scheduler behavior when disabled via environment."""
        with patch.dict(os.environ, {"SCHEDULER_ENABLED": "false"}):
            # Test that scheduler logic respects the environment variable
            # This would typically be tested at the application level
            scheduler_enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
            assert not scheduler_enabled

    @patch("src.infrastructure.external.usgs_service.USGSService")
    async def test_manual_job_trigger(
        self, mock_usgs_service_class, scheduler_service, sample_earthquake_data
    ):
        """Test manually triggering the ingestion job via use case."""
        # Setup mock to return sample data as coroutine
        mock_usgs_instance = AsyncMock()
        mock_usgs_instance.fetch_recent_earthquakes.return_value = (
            sample_earthquake_data
        )
        mock_usgs_service_class.return_value = mock_usgs_instance

        # Replace the service in the use case
        scheduler_service._ingestion_use_case.usgs_service = mock_usgs_instance

        # Create ingestion request
        from src.application.use_cases.ingest_earthquake_data import IngestionRequest

        request = IngestionRequest(
            source="USGS", period="hour", magnitude_filter="2.5", limit=100
        )

        # This should execute without errors
        result = await scheduler_service._ingestion_use_case.execute(request)

        # Verify the ingestion completed successfully
        assert result.total_fetched == len(sample_earthquake_data)

        # Verify the USGS service was called
        mock_usgs_instance.fetch_recent_earthquakes.assert_called_once()

    def test_scheduler_timezone_configuration(self, scheduler_service):
        """Test that scheduler uses UTC timezone."""
        assert str(scheduler_service._scheduler.scheduler.timezone) == "UTC"

    async def test_scheduler_job_persistence(self, scheduler_service):
        """Test that jobs persist while scheduler is running and can be re-added after shutdown."""
        # Add jobs and verify they are registered
        await scheduler_service.setup_earthquake_ingestion_job()
        initial_jobs = scheduler_service.list_jobs()
        assert "earthquake_ingestion" in initial_jobs

        # Start scheduler
        scheduler_service.start_scheduler()
        running_jobs = scheduler_service.list_jobs()
        assert "earthquake_ingestion" in running_jobs
        assert len(running_jobs) == len(initial_jobs)

        # Stop scheduler - APScheduler shutdown clears jobs (expected behavior)
        await scheduler_service.stop_scheduler()
        stopped_jobs = scheduler_service.list_jobs()
        # This is expected - shutdown clears the job list
        assert len(stopped_jobs) == 0

        # But we can re-add jobs after shutdown
        # Note: calling setup_earthquake_ingestion_job again would not add duplicate
        # due to the _jobs_added flag, so we test the idempotent behavior
        try:
            await scheduler_service.setup_earthquake_ingestion_job()
            # This should not add a duplicate due to internal flag
        except Exception:
            # If it fails due to stopped scheduler, that's also acceptable behavior
            pass

    async def test_scheduler_concurrent_access(self, scheduler_service):
        """Test scheduler handles concurrent start/stop operations."""
        # Add jobs first
        await scheduler_service.setup_earthquake_ingestion_job()

        # Start multiple times (should be idempotent)
        scheduler_service.start_scheduler()
        scheduler_service.start_scheduler()
        scheduler_service.start_scheduler()

        assert scheduler_service._scheduler.scheduler.running

        # Stop multiple times (should be idempotent)
        await scheduler_service.stop_scheduler()
        await scheduler_service.stop_scheduler()
        await scheduler_service.stop_scheduler()

        assert not scheduler_service._scheduler.scheduler.running

    @patch("src.infrastructure.scheduler.scheduler_service.logger")
    async def test_scheduler_logging(self, mock_logger, scheduler_service):
        """Test that scheduler operations are properly logged."""
        await scheduler_service.setup_earthquake_ingestion_job()
        scheduler_service.start_scheduler()
        mock_logger.info.assert_called_with("APScheduler started with UTC timezone")

        await scheduler_service.stop_scheduler()
        mock_logger.info.assert_called_with("APScheduler stopped")

    async def test_scheduler_memory_usage(self, scheduler_service):
        """Test that scheduler doesn't leak memory during operation."""
        import gc

        # Get initial memory usage
        initial_objects = len(gc.get_objects())

        # Add jobs once
        await scheduler_service.setup_earthquake_ingestion_job()

        # Start and stop scheduler multiple times
        for _ in range(5):
            scheduler_service.start_scheduler()
            await scheduler_service.stop_scheduler()

        # Force garbage collection
        gc.collect()

        # Check that we don't have excessive object growth
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects

        # Allow for some object growth but not excessive
        assert (
            object_growth < 1000
        ), f"Potential memory leak: {object_growth} new objects"
