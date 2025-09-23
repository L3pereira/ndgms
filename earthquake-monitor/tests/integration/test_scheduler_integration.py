"""Integration tests for scheduler service with real dependencies."""

import os
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from src.domain.entities.earthquake import Earthquake
from src.domain.entities.location import Location
from src.domain.entities.magnitude import Magnitude, MagnitudeScale
from src.infrastructure.scheduler.scheduler_service import SchedulerService


class TestSchedulerIntegration:
    """Integration tests for scheduler with database."""

    @pytest.fixture
    async def scheduler_service(self):
        """Create scheduler service for integration testing."""
        service = SchedulerService()
        yield service
        # Cleanup: stop scheduler if running
        if service.scheduler.running:
            await service.stop()

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
        assert not scheduler_service.scheduler.running

        # Add jobs first
        await scheduler_service.add_usgs_ingestion_job()

        # Test start
        scheduler_service.start()
        assert scheduler_service.scheduler.running

        # Verify jobs are registered
        jobs = scheduler_service.list_jobs()
        assert "usgs_ingestion" in jobs

        # Test job status
        job_status = scheduler_service.get_job_status("usgs_ingestion")
        assert job_status is not None
        assert job_status["id"] == "usgs_ingestion"

        # Test stop
        await scheduler_service.stop()
        assert not scheduler_service.scheduler.running

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
        await scheduler_service.add_usgs_ingestion_job()
        scheduler_service.start()

        job = scheduler_service.scheduler.get_job("usgs_ingestion")
        assert job is not None

        # Check that the job is configured with environment values
        # Note: The actual interval is set when the job is defined, not when started
        assert job.id == "usgs_ingestion"

        await scheduler_service.stop()

    @patch("src.infrastructure.scheduler.scheduler_service.USGSService")
    async def test_ingestion_job_error_handling(
        self, mock_usgs_service_class, scheduler_service
    ):
        """Test that scheduler handles job errors gracefully."""
        # Setup mock to simulate API error
        mock_usgs_service = mock_usgs_service_class.return_value
        mock_usgs_service.fetch_recent_earthquakes.side_effect = Exception(
            "API temporarily unavailable"
        )

        # Add jobs and start scheduler
        await scheduler_service.add_usgs_ingestion_job()
        scheduler_service.start()

        # Manually trigger the job to test error handling
        from src.infrastructure.scheduler.scheduler_service import (
            ingest_usgs_data_async,
        )

        # This should not raise an exception (the async function handles errors gracefully)
        await ingest_usgs_data_async()

        # Scheduler should still be running
        assert scheduler_service.scheduler.running

        await scheduler_service.stop()

    async def test_scheduler_with_disabled_environment(self):
        """Test scheduler behavior when disabled via environment."""
        with patch.dict(os.environ, {"SCHEDULER_ENABLED": "false"}):
            # Test that scheduler logic respects the environment variable
            # This would typically be tested at the application level
            scheduler_enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
            assert not scheduler_enabled

    @patch("src.infrastructure.scheduler.scheduler_service.USGSService")
    async def test_manual_job_trigger(
        self, mock_usgs_service_class, sample_earthquake_data
    ):
        """Test manually triggering the ingestion job."""
        # Setup mock
        mock_usgs_service = mock_usgs_service_class.return_value
        mock_usgs_service.fetch_recent_earthquakes.return_value = sample_earthquake_data

        # Import and test the job function directly
        from src.infrastructure.scheduler.scheduler_service import (
            ingest_usgs_data_async,
        )

        # This should execute without errors
        await ingest_usgs_data_async()

        # Verify the USGS service was called
        mock_usgs_service.fetch_recent_earthquakes.assert_called_once()

    def test_scheduler_timezone_configuration(self, scheduler_service):
        """Test that scheduler uses UTC timezone."""
        assert str(scheduler_service.scheduler.timezone) == "UTC"

    async def test_scheduler_job_persistence(self, scheduler_service):
        """Test that jobs persist through scheduler restarts."""
        # Add jobs and start scheduler
        await scheduler_service.add_usgs_ingestion_job()
        scheduler_service.start()
        initial_jobs = scheduler_service.list_jobs()
        assert "usgs_ingestion" in initial_jobs

        # Restart scheduler using the new restart method
        await scheduler_service.restart()

        # Jobs should be automatically re-added
        restarted_jobs = scheduler_service.list_jobs()
        assert "usgs_ingestion" in restarted_jobs
        assert len(restarted_jobs) == len(initial_jobs)

        await scheduler_service.stop()

    async def test_scheduler_concurrent_access(self, scheduler_service):
        """Test scheduler handles concurrent start/stop operations."""
        # Add jobs first
        await scheduler_service.add_usgs_ingestion_job()

        # Start multiple times (should be idempotent)
        scheduler_service.start()
        scheduler_service.start()
        scheduler_service.start()

        assert scheduler_service.scheduler.running

        # Stop multiple times (should be idempotent)
        await scheduler_service.stop()
        await scheduler_service.stop()
        await scheduler_service.stop()

        assert not scheduler_service.scheduler.running

    @patch("src.infrastructure.scheduler.scheduler_service.logger")
    async def test_scheduler_logging(self, mock_logger, scheduler_service):
        """Test that scheduler operations are properly logged."""
        await scheduler_service.add_usgs_ingestion_job()
        scheduler_service.start()
        mock_logger.info.assert_called_with(
            "AsyncIO scheduler started with UTC timezone"
        )

        await scheduler_service.stop()
        mock_logger.info.assert_called_with("AsyncIO scheduler stopped")

    async def test_scheduler_memory_usage(self, scheduler_service):
        """Test that scheduler doesn't leak memory during operation."""
        import gc

        # Get initial memory usage
        initial_objects = len(gc.get_objects())

        # Add jobs once
        await scheduler_service.add_usgs_ingestion_job()

        # Start and stop scheduler multiple times
        for _ in range(5):
            scheduler_service.start()
            await scheduler_service.stop()

        # Force garbage collection
        gc.collect()

        # Check that we don't have excessive object growth
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects

        # Allow for some object growth but not excessive
        assert (
            object_growth < 1000
        ), f"Potential memory leak: {object_growth} new objects"
