"""Pytest configuration for integration tests."""

import os

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Set testing environment at module level
os.environ["TESTING"] = "true"

from src.presentation.main import app

# Import test database fixtures
from .test_database_setup import (  # noqa: F401
    db_session,
    seed_test_data,
    test_db_manager,
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app with clean database state."""
    from src.infrastructure.database.config import SessionLocal
    from src.infrastructure.database.models import UserModel
    from src.presentation.auth.models import UserCreate
    from src.presentation.auth.repository import get_user_repository
    from src.presentation.auth.security import reset_security_service

    # Auto-detect database host and setup
    def _detect_db_host():
        import socket

        try:
            socket.gethostbyname("db")
            return "db"  # Running in Docker
        except (socket.gaierror, socket.herror):
            return "localhost"  # Running locally

    def _setup_local_test_db(db_host):
        """Ensure test database exists for local testing."""
        if db_host == "localhost":
            try:
                from sqlalchemy import create_engine, text

                # Connect to postgres database to create test database
                engine = create_engine(
                    "postgresql://postgres:password@localhost:5432/postgres",
                    isolation_level="AUTOCOMMIT",
                )
                with engine.connect() as conn:
                    # Check if test database exists
                    result = conn.execute(
                        text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                        {"db_name": "earthquake_monitor_dev"},
                    )
                    if not result.fetchone():
                        # Create test database
                        conn.execute(text("CREATE DATABASE earthquake_monitor_dev"))
                        print("✅ Created local test database: earthquake_monitor_dev")
                engine.dispose()
            except Exception as e:
                print(f"⚠️  Could not setup local test database: {e}")
                print(
                    "📝 Please create database 'earthquake_monitor_dev' manually or run PostgreSQL"
                )

    # Set testing environment to allow permissive CORS/hosts
    os.environ["TESTING"] = "true"

    # Respect existing REPOSITORY_TYPE (e.g., from GitHub Actions or Docker)
    # Default to postgresql for local development when not set
    repository_type = os.environ.get("REPOSITORY_TYPE", "postgresql")

    # Only setup database if using postgresql repository
    if repository_type == "postgresql":
        # Use auto-detected host for database connection
        db_host = _detect_db_host()

        # Setup local database if needed
        _setup_local_test_db(db_host)

        os.environ["DATABASE_URL"] = (
            f"postgresql://postgres:password@{db_host}:5432/earthquake_monitor_dev"
        )

    # Set the repository type (only override if not already set)
    os.environ["REPOSITORY_TYPE"] = repository_type

    # Reset the security service to ensure clean JWT state
    reset_security_service()

    # Clean up existing test users before creating new ones
    session = SessionLocal()
    try:
        # Delete existing test users to ensure clean state
        session.query(UserModel).filter(
            UserModel.email.in_(
                [
                    "admin@earthquake-monitor.com",
                    "test@earthquake-monitor.com",
                    "newuser@example.com",  # Common test email
                    "duplicate@example.com",  # Common test email
                ]
            )
        ).delete(synchronize_session=False)
        session.commit()

        user_repo = get_user_repository(session)

        # Create default admin user
        admin_user = UserCreate(
            email="admin@earthquake-monitor.com",
            username="admin",
            full_name="System Administrator",
            password="admin123",
            is_active=True,
        )
        user_repo.create_user(admin_user)

        # Create test user
        test_user = UserCreate(
            email="test@earthquake-monitor.com",
            username="testuser",
            full_name="Test User",
            password="testpass123",
            is_active=True,
        )
        user_repo.create_user(test_user)

    finally:
        session.close()

    return TestClient(app)


@pytest_asyncio.fixture
async def client_with_db(test_db_manager):  # noqa: F811
    """Create an async test client for the FastAPI app with real database."""
    # Set testing environment to allow permissive CORS/hosts
    os.environ["TESTING"] = "true"
    # Set environment to use test database
    os.environ["DATABASE_URL"] = test_db_manager.test_db_url
    os.environ["REPOSITORY_TYPE"] = "postgresql"

    # Override the database session dependency to use a fresh engine for each request
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    from src.infrastructure.database.config import (
        create_async_engine,
        get_async_session,
    )

    async def override_get_async_session():
        # Create a fresh engine and session for each request
        test_engine = create_async_engine(
            test_db_manager.test_db_url.replace(
                "postgresql://", "postgresql+asyncpg://"
            )
        )
        TestSessionLocal = sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with TestSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

        await test_engine.dispose()

    app.dependency_overrides[get_async_session] = override_get_async_session

    # Reset auth repository for clean test state
    from src.presentation.auth.repository import get_user_repository
    from src.presentation.auth.security import reset_security_service

    # Reset the security service to ensure clean JWT state
    reset_security_service()

    # Create test users in database for auth
    from src.infrastructure.database.config import SessionLocal
    from src.infrastructure.database.models import UserModel
    from src.presentation.auth.models import UserCreate

    session = SessionLocal()
    try:
        # Clean up existing test users
        session.query(UserModel).filter(
            UserModel.email.in_(
                [
                    "admin@earthquake-monitor.com",
                    "test@earthquake-monitor.com",
                    "newuser@example.com",
                    "duplicate@example.com",
                ]
            )
        ).delete(synchronize_session=False)
        session.commit()

        user_repo = get_user_repository(session)

        # Create default admin user
        admin_user = UserCreate(
            email="admin@earthquake-monitor.com",
            username="admin",
            full_name="System Administrator",
            password="admin123",
            is_active=True,
        )
        user_repo.create_user(admin_user)

        # Create test user
        test_user = UserCreate(
            email="test@earthquake-monitor.com",
            username="testuser",
            full_name="Test User",
            password="testpass123",
            is_active=True,
        )
        user_repo.create_user(test_user)

    finally:
        session.close()

    try:
        # Use AsyncClient for proper async support
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            yield client
    finally:
        # Clean up dependency override
        app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Get authentication headers with a valid token."""
    # Use the default test user that's already created
    login_data = {"email": "test@earthquake-monitor.com", "password": "testpass123"}
    response = client.post("/api/v1/auth/login", json=login_data)

    if response.status_code == 200:
        token_data = response.json()
        return {"Authorization": f"Bearer {token_data['access_token']}"}
    else:
        # Fallback: return empty headers for tests that expect auth failure
        return {}


@pytest.fixture
def sample_earthquake_data():
    """Sample earthquake data for testing."""
    return {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "depth": 10.0,
        "magnitude_value": 5.5,
        "magnitude_scale": "moment",
        "occurred_at": "2024-01-15T10:30:00Z",
        "source": "USGS",
    }
