"""Pytest configuration for integration tests."""

import os

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from src.presentation.main import app

# Import test database fixtures
from .test_database_setup import (  # noqa: F401
    db_session,
    seed_test_data,
    test_db_manager,
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app with mock repository."""
    # Reset auth repository for clean test state
    from src.presentation.auth.repository import get_user_repository
    from src.presentation.auth.security import reset_security_service

    # Ensure we use mock repository for regular integration tests
    os.environ["REPOSITORY_TYPE"] = "mock"

    # Reset the security service to ensure clean JWT state
    reset_security_service()

    # Reset auth repository
    user_repo = get_user_repository()
    user_repo._users.clear()
    user_repo._users_by_email.clear()
    user_repo._create_default_users()

    return TestClient(app)


@pytest_asyncio.fixture
async def client_with_db(test_db_manager):  # noqa: F811
    """Create an async test client for the FastAPI app with real database."""
    # Set environment to use test database
    os.environ["DATABASE_URL"] = test_db_manager.test_db_url
    os.environ["REPOSITORY_TYPE"] = "postgresql"

    # Reset auth repository for clean test state
    from src.presentation.auth.repository import get_user_repository
    from src.presentation.auth.security import reset_security_service

    # Reset the security service to ensure clean JWT state
    reset_security_service()

    # Reset auth repository (still using in-memory for auth)
    user_repo = get_user_repository()
    user_repo._users.clear()
    user_repo._users_by_email.clear()
    user_repo._create_default_users()

    # Use AsyncClient for proper async support
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


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
