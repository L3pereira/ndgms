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


@pytest.fixture(scope="session")
def test_client_session(test_db_manager):  # noqa: F811
    """Create a session-scoped test client with shared database engine."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    from src.infrastructure.database.config import (
        SessionLocal,
        create_async_engine,
        get_async_session,
    )
    from src.infrastructure.database.models import UserModel
    from src.presentation.auth.models import UserCreate
    from src.presentation.auth.repository import get_user_repository
    from src.presentation.auth.security import reset_security_service

    # Set testing environment to allow permissive CORS/hosts
    os.environ["TESTING"] = "true"
    # Force postgresql for all integration tests
    os.environ["REPOSITORY_TYPE"] = "postgresql"
    # Use test database from test_db_manager
    os.environ["DATABASE_URL"] = test_db_manager.test_db_url

    # Create a shared test engine for the entire session
    test_async_engine = create_async_engine(
        test_db_manager.test_db_url.replace("postgresql://", "postgresql+asyncpg://"),
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=False,
        echo=False,
    )

    TestAsyncSessionLocal = sessionmaker(
        test_async_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Override the async session dependency
    async def override_get_async_session():
        async with TestAsyncSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_async_session] = override_get_async_session

    # Reset the security service to ensure clean JWT state
    reset_security_service()

    # Setup database users using synchronous session (once per session)
    session = SessionLocal()
    try:
        # Delete existing test users to ensure clean state
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

    yield TestClient(app)

    # Clean up dependency override at end of session
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_client_session):
    """Function-scoped client that reuses the session-scoped client."""
    return test_client_session


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

    # Create a single engine for the entire test
    test_engine = create_async_engine(
        test_db_manager.test_db_url.replace("postgresql://", "postgresql+asyncpg://"),
        pool_size=1,
        max_overflow=0,
        echo=False,
    )
    TestSessionLocal = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_async_session():
        async with TestSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

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
        # Dispose the test engine
        await test_engine.dispose()


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


@pytest_asyncio.fixture
async def async_auth_headers(client_with_db):
    """Get authentication headers with a valid token for async client."""
    # Use the default test user that's already created
    login_data = {"email": "test@earthquake-monitor.com", "password": "testpass123"}
    response = await client_with_db.post("/api/v1/auth/login", json=login_data)

    if response.status_code == 200:
        token_data = response.json()
        return {"Authorization": f"Bearer {token_data['access_token']}"}
    else:
        # Fallback: return empty headers for tests that expect auth failure
        return {}


@pytest_asyncio.fixture(autouse=True)
async def cleanup_earthquake_data():
    """Clean up earthquake data after each test."""
    yield  # Run the test

    # Skip cleanup to avoid event loop conflicts for now
    # TODO: Implement proper async cleanup if needed
    pass


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
