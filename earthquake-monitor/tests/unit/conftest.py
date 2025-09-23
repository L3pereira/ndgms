"""Pytest configuration for unit tests."""

import os

import pytest
from fastapi.testclient import TestClient

# Set testing environment
os.environ["TESTING"] = "true"
# Use in-memory mock repository for unit tests
os.environ["REPOSITORY_TYPE"] = "in_memory"

from src.presentation.main import app


@pytest.fixture
def client():
    """Create a simple test client for unit tests without database dependencies."""
    return TestClient(app)


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "password123",
    }


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


@pytest.fixture
def mock_auth_headers():
    """Mock authentication headers for unit tests."""
    return {"Authorization": "Bearer mock_token_for_unit_tests"}
