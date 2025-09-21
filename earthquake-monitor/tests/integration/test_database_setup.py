"""Database setup utilities for integration tests."""

import asyncio
import os
from collections.abc import AsyncGenerator
from datetime import UTC

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseTestManager:
    """Manages test database creation and cleanup."""

    def __init__(self):
        self.test_db_name = "earthquake_monitor_test"
        self.main_db_url = "postgresql://postgres:password@localhost:5432/postgres"
        self.test_db_url = (
            f"postgresql://postgres:password@localhost:5432/{self.test_db_name}"
        )

    def create_test_database(self):
        """Create test database if it doesn't exist."""
        engine = create_engine(self.main_db_url, isolation_level="AUTOCOMMIT")

        try:
            with engine.connect() as conn:
                # Check if database exists
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": self.test_db_name},
                )

                if not result.fetchone():
                    # Create test database
                    conn.execute(text(f"CREATE DATABASE {self.test_db_name}"))
                    print(f"Created test database: {self.test_db_name}")
                else:
                    print(f"Test database already exists: {self.test_db_name}")

        except Exception as e:
            print(f"Error creating test database: {e}")
            raise
        finally:
            engine.dispose()

    def drop_test_database(self):
        """Drop test database."""
        engine = create_engine(self.main_db_url, isolation_level="AUTOCOMMIT")

        try:
            with engine.connect() as conn:
                # Terminate existing connections to the test database
                conn.execute(
                    text(
                        f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{self.test_db_name}' AND pid <> pg_backend_pid()
                """
                    )
                )

                # Drop test database
                conn.execute(text(f"DROP DATABASE IF EXISTS {self.test_db_name}"))
                print(f"Dropped test database: {self.test_db_name}")

        except Exception as e:
            print(f"Error dropping test database: {e}")
        finally:
            engine.dispose()

    def run_migrations(self):
        """Run Alembic migrations on test database."""
        import subprocess

        # Set environment variable for test database
        env = os.environ.copy()
        env["DATABASE_URL"] = self.test_db_url

        try:
            # Run migrations using the test configuration
            result = subprocess.run(
                ["alembic", "-c", "alembic_test.ini", "upgrade", "head"],
                env=env,
                capture_output=True,
                text=True,
                cwd=".",
            )

            if result.returncode != 0:
                print(f"Migration failed: {result.stderr}")
                raise Exception(f"Migration failed: {result.stderr}")
            else:
                print("Migrations completed successfully")

        except Exception as e:
            print(f"Error running migrations: {e}")
            raise


# Pytest fixtures for database testing


@pytest.fixture(scope="session")
def test_db_manager():
    """Create and manage test database for the session."""
    manager = DatabaseTestManager()

    # Setup
    manager.create_test_database()
    manager.run_migrations()

    yield manager

    # Cleanup
    manager.drop_test_database()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
async def db_session(test_db_manager) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    # Set environment to use test database
    os.environ["DATABASE_URL"] = test_db_manager.test_db_url
    os.environ["REPOSITORY_TYPE"] = "postgresql"

    # Create session with test database
    from sqlalchemy.ext.asyncio import AsyncSession as AsyncSessionClass

    from src.infrastructure.database.config import create_async_engine, sessionmaker

    test_engine = create_async_engine(
        f"postgresql+asyncpg://postgres:password@localhost:5432/{test_db_manager.test_db_name}"
    )
    TestSessionLocal = sessionmaker(
        test_engine, class_=AsyncSessionClass, expire_on_commit=False
    )

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()  # Rollback any changes after each test

    await test_engine.dispose()


@pytest.fixture
async def seed_test_data(db_session):
    """Seed the test database with initial data."""
    import uuid
    from datetime import datetime

    from src.infrastructure.database.models import EarthquakeModel

    # Create test earthquakes
    test_earthquakes = [
        EarthquakeModel(
            id=uuid.uuid4(),
            latitude=37.7749,
            longitude=-122.4194,
            depth=10.0,
            magnitude_value=5.5,
            magnitude_scale="moment",
            occurred_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
            source="TEST",
            is_reviewed=False,
        ),
        EarthquakeModel(
            id=uuid.uuid4(),
            latitude=35.6762,
            longitude=139.6503,
            depth=35.0,
            magnitude_value=6.8,
            magnitude_scale="moment",
            occurred_at=datetime(2024, 1, 16, 14, 45, 0, tzinfo=UTC),
            source="TEST",
            is_reviewed=True,
        ),
    ]

    for earthquake in test_earthquakes:
        db_session.add(earthquake)

    await db_session.commit()

    return test_earthquakes
