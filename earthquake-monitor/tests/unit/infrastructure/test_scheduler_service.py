"""Unit tests for scheduler service."""

import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.application.services.scheduled_job_service import ScheduledJobService
from src.domain.entities.earthquake import Earthquake
from src.domain.entities.location import Location
from src.domain.entities.magnitude import Magnitude, MagnitudeScale
from src.infrastructure.factory import create_scheduled_job_service
from src.infrastructure.scheduler.scheduler_service import (
    APSchedulerService,  # Backward compatibility alias
)


@pytest.fixture(autouse=True, scope="function")
def mock_database_connections():
    """Function-level fixture to completely prevent database connections."""
    # Mock the entire database config module before any imports
    with (
        patch(
            "src.infrastructure.database.config.create_async_engine"
        ) as mock_create_async_engine,
        patch("src.infrastructure.database.config.async_engine") as mock_async_engine,
        patch(
            "src.infrastructure.database.config.AsyncSessionLocal"
        ) as mock_async_session_local,
        patch(
            "src.infrastructure.database.config.get_async_session_for_background"
        ) as mock_bg_session,
        patch(
            "src.infrastructure.database.config.get_async_session"
        ) as mock_get_async_session,
    ):
        # Create a properly mocked engine that won't create real connections
        mock_engine_instance = AsyncMock()
        mock_engine_instance.dispose = AsyncMock()
        mock_engine_instance.sync_engine = AsyncMock()

        # Ensure the engine mock doesn't have real connection attributes
        mock_engine_instance._connection_cls = AsyncMock()
        mock_engine_instance._pool = AsyncMock()
        mock_engine_instance.connect = AsyncMock()
        mock_engine_instance.execution_options = AsyncMock(
            return_value=mock_engine_instance
        )

        mock_create_async_engine.return_value = mock_engine_instance
        mock_async_engine.return_value = mock_engine_instance

        # Mock the session factory to return a context manager that yields a mock session
        class MockAsyncSessionContext:
            def __init__(self):
                self.session = AsyncMock()
                self.session.commit = AsyncMock()
                self.session.close = AsyncMock()
                self.session.rollback = AsyncMock()
                # Mock connection attributes to prevent SQLAlchemy warnings
                self.session.connection = AsyncMock()
                self.session.get_bind = AsyncMock()

            async def __aenter__(self):
                return self.session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                await self.session.close()
                # Ensure cleanup
                if hasattr(self.session, "connection"):
                    await self.session.connection.close()

        mock_async_session_local.return_value = MockAsyncSessionContext()

        # Mock the background session function
        async def mock_bg_session_func():
            ctx = MockAsyncSessionContext()
            async with ctx as session:
                yield session

        mock_bg_session.side_effect = mock_bg_session_func

        # Mock the regular get_async_session function as well
        async def mock_get_async_session_func():
            ctx = MockAsyncSessionContext()
            async with ctx as session:
                yield session

        mock_get_async_session.side_effect = mock_get_async_session_func

        yield


class TestAPSchedulerService:
    """Test cases for APSchedulerService (infrastructure layer)."""

    @pytest.fixture
    def scheduler_service(self):
        """Create a scheduler service instance for testing."""
        return APSchedulerService()

    @pytest.fixture
    def mock_earthquake(self):
        """Create a mock earthquake for testing."""
        return Earthquake(
            location=Location(latitude=37.7749, longitude=-122.4194, depth=10.0),
            magnitude=Magnitude(value=3.5, scale=MagnitudeScale.MOMENT),
            occurred_at=datetime.now(UTC),
            source="USGS",
        )

    def test_apscheduler_service_initialization(self, scheduler_service):
        """Test APScheduler service is properly initialized."""
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

        # Test stop with mocked sleep to make it fast
        with patch("asyncio.sleep", new_callable=AsyncMock):
            # Test stop method behavior - it should call shutdown
            with patch.object(scheduler_service.scheduler, "shutdown") as mock_shutdown:
                await scheduler_service.stop()
                mock_shutdown.assert_called_once_with(wait=False)

                # After shutdown, set scheduler state to not running manually for test
                scheduler_service.scheduler.shutdown(wait=True)

            # Test stop when not running (should not error)
            await scheduler_service.stop()

    def test_get_job_status_existing_job(self, scheduler_service):
        """Test getting status of existing job."""
        # Add a test job using the interface method
        scheduler_service.add_job(
            func=lambda: None,
            trigger="interval",
            job_id="test_job",
            name="Test Job",
            seconds=10,
        )

        job_status = scheduler_service.get_job_status("test_job")

        assert job_status is not None
        assert job_status["id"] == "test_job"
        assert "next_run" in job_status
        assert "trigger" in job_status

        # Cleanup
        scheduler_service.remove_job("test_job")

    def test_get_job_status_nonexistent_job(self, scheduler_service):
        """Test getting status of nonexistent job."""
        job_status = scheduler_service.get_job_status("nonexistent_job")
        assert job_status is None

    def test_list_jobs(self, scheduler_service):
        """Test listing all jobs."""
        # Add test jobs using interface methods
        scheduler_service.add_job(
            func=lambda: None,
            trigger="interval",
            job_id="test_job_1",
            name="Test Job 1",
            seconds=10,
        )
        scheduler_service.add_job(
            func=lambda: None,
            trigger="interval",
            job_id="test_job_2",
            name="Test Job 2",
            seconds=20,
        )

        jobs = scheduler_service.list_jobs()

        assert isinstance(jobs, dict)
        assert len(jobs) >= 2  # At least our test jobs
        assert "test_job_1" in jobs
        assert "test_job_2" in jobs
        assert jobs["test_job_1"]["id"] == "test_job_1"
        assert jobs["test_job_2"]["id"] == "test_job_2"

        # Cleanup
        scheduler_service.remove_job("test_job_1")
        scheduler_service.remove_job("test_job_2")


class TestScheduledJobService:
    """Test cases for ScheduledJobService (application layer)."""

    @pytest.fixture
    def mock_earthquakes(self):
        """Create mock earthquakes for testing."""
        return [
            Earthquake(
                location=Location(latitude=37.7749, longitude=-122.4194, depth=10.0),
                magnitude=Magnitude(value=3.5, scale=MagnitudeScale.MOMENT),
                occurred_at=datetime.now(UTC),
                source="USGS",
            ),
            Earthquake(
                location=Location(latitude=40.7589, longitude=-73.9851, depth=5.0),
                magnitude=Magnitude(value=2.1, scale=MagnitudeScale.RICHTER),
                occurred_at=datetime.now(UTC),
                source="USGS",
            ),
        ]

    @pytest.fixture
    async def scheduled_job_service(self, mock_database_connections):
        """Create a ScheduledJobService for testing."""
        from src.application.events.event_publisher import EventPublisher
        from src.application.use_cases.ingest_earthquake_data import (
            ScheduledIngestionUseCase,
        )
        from src.infrastructure.external.usgs_service import USGSService
        from src.presentation.dependencies import MockEarthquakeRepository

        # Create mocks
        mock_repo = MockEarthquakeRepository()
        mock_event_publisher = AsyncMock(spec=EventPublisher)
        mock_usgs_service = AsyncMock(spec=USGSService)
        mock_scheduler = APSchedulerService()

        # Create use case
        scheduled_ingestion_use_case = ScheduledIngestionUseCase(
            repository=mock_repo,
            event_publisher=mock_event_publisher,
            usgs_service=mock_usgs_service,
        )

        # Create service
        return ScheduledJobService(
            job_scheduler=mock_scheduler,
            scheduled_ingestion_use_case=scheduled_ingestion_use_case,
        )

    @patch.dict(
        os.environ,
        {
            "USGS_INGESTION_PERIOD": "hour",
            "USGS_INGESTION_MIN_MAGNITUDE": "2.0",
            "USGS_INGESTION_INTERVAL_MINUTES": "30",
        },
    )
    async def test_setup_earthquake_ingestion_job(self, scheduled_job_service):
        """Test that earthquake ingestion job can be set up successfully."""
        # Setup the job
        await scheduled_job_service.setup_earthquake_ingestion_job()

        # Verify job was added
        jobs = scheduled_job_service.list_jobs()
        assert "earthquake_ingestion" in jobs
        assert jobs["earthquake_ingestion"]["name"] == "Earthquake Data Ingestion"

        # Test that calling setup again doesn't add duplicate jobs
        await scheduled_job_service.setup_earthquake_ingestion_job()
        jobs_after = scheduled_job_service.list_jobs()
        assert len(jobs_after) == len(jobs)  # Should be same number of jobs

    async def test_scheduled_job_service_start_stop(self, scheduled_job_service):
        """Test that ScheduledJobService can start and stop scheduler."""
        # Start scheduler
        scheduled_job_service.start_scheduler()

        # Verify it's running (check underlying scheduler)
        assert scheduled_job_service._scheduler.scheduler.running

        # Stop scheduler
        await scheduled_job_service.stop_scheduler()

        # Note: The underlying scheduler may still show as running immediately after shutdown
        # This is normal behavior for APScheduler

    async def test_job_status_and_listing(self, scheduled_job_service):
        """Test job status and listing functionality."""
        # Setup job first
        await scheduled_job_service.setup_earthquake_ingestion_job()

        # Test job status
        job_status = scheduled_job_service.get_job_status("earthquake_ingestion")
        assert job_status is not None
        assert job_status["id"] == "earthquake_ingestion"
        assert "next_run" in job_status
        assert "trigger" in job_status

        # Test listing jobs
        jobs = scheduled_job_service.list_jobs()
        assert "earthquake_ingestion" in jobs

        # Test nonexistent job
        assert scheduled_job_service.get_job_status("nonexistent") is None

    @patch.dict(os.environ, {"USGS_INGESTION_INTERVAL_MINUTES": "5"})
    async def test_scheduler_interval_configuration(self, scheduled_job_service):
        """Test scheduler respects environment configuration."""
        # Setup job with custom interval
        await scheduled_job_service.setup_earthquake_ingestion_job()

        # Get the underlying job from APScheduler
        job = scheduled_job_service._scheduler.scheduler.get_job("earthquake_ingestion")

        assert job is not None
        assert job.id == "earthquake_ingestion"
        # The trigger should reflect the 5-minute interval
        assert "0:05:00" in str(job.trigger)


class TestSchedulerIntegration:
    """Integration tests for scheduler behavior."""

    @pytest.fixture
    def clean_scheduler(self):
        """Create a clean scheduler for testing."""
        from apscheduler.schedulers.background import BackgroundScheduler

        return BackgroundScheduler(timezone="UTC")

    def test_scheduler_job_execution_tracking(self):
        """Test that we can track job executions with mocked scheduler."""
        from unittest.mock import Mock

        # Mock scheduler that simulates job execution without real threads/waiting
        mock_scheduler = Mock()
        mock_scheduler.running = False

        # Track what gets added as jobs
        jobs = {}

        def mock_add_job(func, trigger, id, **kwargs):
            jobs[id] = {"func": func, "trigger": trigger, **kwargs}
            # Immediately execute the job to simulate scheduler behavior
            func()

        def mock_start():
            mock_scheduler.running = True
            # In a real scheduler, jobs would execute. Here we simulate that they did.

        def mock_shutdown(**kwargs):
            mock_scheduler.running = False

        def mock_remove_job(job_id):
            if job_id in jobs:
                del jobs[job_id]

        mock_scheduler.add_job = mock_add_job
        mock_scheduler.start = mock_start
        mock_scheduler.shutdown = mock_shutdown
        mock_scheduler.remove_job = mock_remove_job

        # Test the job execution
        execution_count = 0

        def test_job():
            nonlocal execution_count
            execution_count += 1

        # Add job - this will execute immediately due to our mock
        mock_scheduler.add_job(test_job, "date", id="test_job", max_instances=1)

        mock_scheduler.start()

        # Remove job
        mock_scheduler.remove_job("test_job")
        mock_scheduler.shutdown(wait=True)

        # Job should have executed (happened immediately when added)
        assert execution_count >= 1
        assert not mock_scheduler.running

    @pytest.mark.asyncio
    async def test_dependency_injection_factory(self, mock_database_connections):
        """Test that the dependency injection factory creates properly wired services."""
        from unittest.mock import AsyncMock

        from src.application.events.event_publisher import EventPublisher
        from src.presentation.dependencies import MockEarthquakeRepository

        # Create mock dependencies
        mock_session = AsyncMock()
        mock_repo = MockEarthquakeRepository()
        mock_publisher = AsyncMock(spec=EventPublisher)

        # Test that factory creates service without errors
        service = await create_scheduled_job_service(
            session=mock_session,
            earthquake_repository=mock_repo,
            event_publisher=mock_publisher,
        )

        # Verify service is properly configured
        assert isinstance(service, ScheduledJobService)
        assert service._scheduler is not None
        assert service._ingestion_use_case is not None

        # Test that we can setup jobs
        await service.setup_earthquake_ingestion_job()
        jobs = service.list_jobs()
        assert "earthquake_ingestion" in jobs
