"""Pytest configuration for integration tests."""

import pytest
from fastapi.testclient import TestClient

from src.presentation.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Reset auth repository for clean test state
    from src.presentation.auth.repository import get_user_repository
    from src.presentation.auth.security import reset_security_service

    # Reset the security service to ensure clean JWT state
    reset_security_service()

    # Reset auth repository
    user_repo = get_user_repository()
    user_repo._users.clear()
    user_repo._users_by_email.clear()
    user_repo._create_default_users()

    return TestClient(app)


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
