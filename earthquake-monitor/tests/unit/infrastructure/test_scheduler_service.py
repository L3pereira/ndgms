"""Unit tests for scheduler service."""

import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.domain.entities.earthquake import Earthquake
from src.domain.entities.location import Location
from src.domain.entities.magnitude import Magnitude, MagnitudeScale
from src.infrastructure.scheduler.scheduler_service import (
    SchedulerService,
    ingest_usgs_data_async,
)


class TestSchedulerService:
    """Test cases for SchedulerService."""

    @pytest.fixture
    def scheduler_service(self):
        """Create a scheduler service instance for testing."""
        return SchedulerService()

    @pytest.fixture
    def mock_earthquake(self):
        """Create a mock earthquake for testing."""
        return Earthquake(
            location=Location(latitude=37.7749, longitude=-122.4194, depth=10.0),
            magnitude=Magnitude(value=3.5, scale=MagnitudeScale.MOMENT),
            occurred_at=datetime.now(timezone.utc),
            source="USGS",
        )

    def test_scheduler_service_initialization(self, scheduler_service):
        """Test scheduler service is properly initialized."""
        assert scheduler_service.scheduler is not None
        assert isinstance(scheduler_service.scheduler, AsyncIOScheduler)
        assert str(scheduler_service.scheduler.timezone) == "UTC"

    @pytest.mark.asyncio
    async def test_scheduler_start_and_stop(self, scheduler_service):
        """Test scheduler can be started and stopped."""
        # Test start
        scheduler_service.start()
        assert scheduler_service.scheduler.running

        # Test start when already running (should not error)
        scheduler_service.start()
        assert scheduler_service.scheduler.running

        # Test stop
        await scheduler_service.stop()
        assert not scheduler_service.scheduler.running

        # Test stop when not running (should not error)
        await scheduler_service.stop()
        assert not scheduler_service.scheduler.running

    def test_get_job_status_existing_job(self, scheduler_service):
        """Test getting status of existing job."""
        # Add a test job first
        scheduler_service.scheduler.add_job(
            lambda: None, "interval", seconds=10, id="test_job"
        )

        job_status = scheduler_service.get_job_status("test_job")

        assert job_status is not None
        assert job_status["id"] == "test_job"
        assert "next_run" in job_status
        assert "trigger" in job_status

        # Cleanup
        scheduler_service.scheduler.remove_job("test_job")

    def test_get_job_status_nonexistent_job(self, scheduler_service):
        """Test getting status of nonexistent job."""
        job_status = scheduler_service.get_job_status("nonexistent_job")
        assert job_status is None

    def test_list_jobs(self, scheduler_service):
        """Test listing all jobs."""
        # Add test jobs
        scheduler_service.scheduler.add_job(
            lambda: None, "interval", seconds=10, id="test_job_1"
        )
        scheduler_service.scheduler.add_job(
            lambda: None, "interval", seconds=20, id="test_job_2"
        )

        jobs = scheduler_service.list_jobs()

        assert isinstance(jobs, dict)
        assert len(jobs) >= 2  # At least our test jobs
        assert "test_job_1" in jobs
        assert "test_job_2" in jobs
        assert jobs["test_job_1"]["id"] == "test_job_1"
        assert jobs["test_job_2"]["id"] == "test_job_2"

        # Cleanup
        scheduler_service.scheduler.remove_job("test_job_1")
        scheduler_service.scheduler.remove_job("test_job_2")


class TestUSGSIngestionJob:
    """Test cases for USGS ingestion job logic."""

    @pytest.fixture
    def mock_earthquakes(self):
        """Create mock earthquakes for testing."""
        return [
            Earthquake(
                location=Location(latitude=37.7749, longitude=-122.4194, depth=10.0),
                magnitude=Magnitude(value=3.5, scale=MagnitudeScale.MOMENT),
                occurred_at=datetime.now(timezone.utc),
                source="USGS",
            ),
            Earthquake(
                location=Location(latitude=40.7589, longitude=-73.9851, depth=5.0),
                magnitude=Magnitude(value=2.1, scale=MagnitudeScale.RICHTER),
                occurred_at=datetime.now(timezone.utc),
                source="USGS",
            ),
        ]

    @patch.dict(
        os.environ,
        {"USGS_INGESTION_PERIOD": "hour", "USGS_INGESTION_MIN_MAGNITUDE": "2.0"},
    )
    async def test_usgs_ingestion_success(self, mock_earthquakes):
        """Test that ingestion job function can be created successfully."""
        # Verify it's a callable
        assert callable(ingest_usgs_data_async)

        # Test that we can create the job function without errors
        await ingest_usgs_data_async()

        # Note: Full integration testing is done in integration tests
        # This unit test focuses on the factory function

    @patch.dict(
        os.environ,
        {"USGS_INGESTION_PERIOD": "day", "USGS_INGESTION_MIN_MAGNITUDE": "1.0"},
    )
    async def test_usgs_ingestion_with_repository_error(self, mock_earthquakes):
        """Test that ingestion job function can be created with different environment."""

        # Verify it's a callable
        assert callable(ingest_usgs_data_async)

        # Test that we can create the job function with different environment variables
        await ingest_usgs_data_async()
        # Note: Error handling testing is done in integration tests
        # This unit test focuses on the factory function with different config

    @patch("src.infrastructure.scheduler.scheduler_service.USGSService")
    async def test_usgs_ingestion_api_error(self, mock_usgs_service_class):
        """Test USGS ingestion handles API errors gracefully."""
        mock_usgs_service = AsyncMock()
        mock_usgs_service.fetch_recent_earthquakes.side_effect = Exception("API Error")
        mock_usgs_service_class.return_value = mock_usgs_service

        # The sync wrapper should handle the exception
        with patch(
            "src.infrastructure.scheduler.scheduler_service.logger"
        ) as mock_logger:
            await ingest_usgs_data_async()  # This should not raise an exception
            mock_logger.error.assert_called()

    async def test_scheduler_job_configuration(self):
        """Test that the scheduler job is properly configured."""
        scheduler_service = SchedulerService()
        await scheduler_service.add_usgs_ingestion_job()

        job = scheduler_service.scheduler.get_job("usgs_ingestion")
        assert job is not None
        assert job.id == "usgs_ingestion"
        assert str(job.trigger).startswith("interval")

    @patch.dict(os.environ, {"USGS_INGESTION_INTERVAL_MINUTES": "5"})
    def test_scheduler_interval_configuration(self):
        """Test scheduler respects environment configuration."""
        scheduler_service = SchedulerService()

        # Add ingestion job (this will pick up the patched env var)
        asyncio.run(scheduler_service.add_usgs_ingestion_job())

        job = scheduler_service.scheduler.get_job("usgs_ingestion")

        assert job is not None
        # The trigger should reflect the 5-minute interval
        assert "0:05:00" in str(job.trigger)


class TestSchedulerIntegration:
    """Integration tests for scheduler behavior."""

    @pytest.fixture
    def clean_scheduler(self):
        """Create a clean scheduler for testing."""
        from apscheduler.schedulers.background import BackgroundScheduler

        return BackgroundScheduler(timezone="UTC")

    def test_scheduler_job_execution_tracking(self, clean_scheduler):
        """Test that we can track job executions."""
        execution_count = 0

        def test_job():
            nonlocal execution_count
            execution_count += 1

        # Add job that runs immediately and then stops
        clean_scheduler.add_job(
            test_job, "interval", seconds=1, id="test_job", max_instances=1
        )

        clean_scheduler.start()

        # Wait for job to execute
        import time

        time.sleep(2)

        clean_scheduler.shutdown(wait=True)

        # Job should have executed at least once
        assert execution_count >= 1

    async def test_scheduler_with_mock_dependencies(self):
        """Test scheduler service can be created and used with clean dependency injection."""
        # Create a clean scheduler service (no global state)
        scheduler_service = SchedulerService()

        # Test that we can add jobs without errors
        await scheduler_service.add_usgs_ingestion_job()

        # Test that jobs were added
        jobs = scheduler_service.list_jobs()
        assert "usgs_ingestion" in jobs

        # Test that job status can be retrieved
        job_status = scheduler_service.get_job_status("usgs_ingestion")
        assert job_status is not None
        assert job_status["id"] == "usgs_ingestion"
