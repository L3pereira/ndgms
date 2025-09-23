"""Integration tests for earthquake API endpoints."""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient


class TestEarthquakeAPI:
    """Test earthquake API endpoints."""

    @pytest.mark.asyncio
    async def test_create_earthquake_success(
        self, client_with_db: AsyncClient, sample_earthquake_data: dict
    ):
        """Test successful earthquake creation."""
        response = await client_with_db.post(
            "/api/v1/earthquakes/", json=sample_earthquake_data
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_create_earthquake_invalid_data(self, client_with_db: AsyncClient):
        """Test earthquake creation with invalid data fails."""
        # Missing required fields
        response = await client_with_db.post("/api/v1/earthquakes/", json={})
        assert response.status_code == 422

        # Invalid magnitude
        invalid_data = {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "depth": 10.0,
            "magnitude_value": -1.0,  # Invalid negative magnitude
            "magnitude_scale": "moment",
            "source": "USGS",
        }
        response = await client_with_db.post("/api/v1/earthquakes/", json=invalid_data)
        assert response.status_code == 422

        # Invalid latitude
        invalid_data["magnitude_value"] = 5.5
        invalid_data["latitude"] = 100.0  # Invalid latitude > 90
        response = await client_with_db.post("/api/v1/earthquakes/", json=invalid_data)
        assert response.status_code == 422

        # Invalid longitude
        invalid_data["latitude"] = 37.7749
        invalid_data["longitude"] = 200.0  # Invalid longitude > 180
        response = await client_with_db.post("/api/v1/earthquakes/", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_earthquake_future_date_returns_400(
        self, client_with_db: AsyncClient
    ):
        """Test that creating earthquake with future date returns 400 Bad Request with domain error."""
        future_date = (datetime.now() + timedelta(hours=1)).isoformat()

        future_earthquake_data = {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "depth": 10.0,
            "magnitude_value": 5.5,
            "magnitude_scale": "moment",
            "occurred_at": future_date,
            "source": "TEST_API",
        }

        response = await client_with_db.post(
            "/api/v1/earthquakes/", json=future_earthquake_data
        )

        # Should return 400 Bad Request (domain validation error)
        assert response.status_code == 400
        error_data = response.json()
        assert "detail" in error_data
        assert (
            "Earthquake occurrence time cannot be in the future" in error_data["detail"]
        )

    @pytest.mark.asyncio
    async def test_create_earthquake_past_date_succeeds(
        self, client_with_db: AsyncClient
    ):
        """Test that creating earthquake with past date succeeds."""
        past_date = (datetime.now() - timedelta(hours=1)).isoformat()

        past_earthquake_data = {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "depth": 10.0,
            "magnitude_value": 5.5,
            "magnitude_scale": "moment",
            "occurred_at": past_date,
            "source": "TEST_API",
        }

        response = await client_with_db.post(
            "/api/v1/earthquakes/", json=past_earthquake_data
        )

        # Should succeed with 201 Created
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_get_earthquakes_list_structure(self, client_with_db: AsyncClient):
        """Test getting earthquakes returns proper structure."""
        response = await client_with_db.get("/api/v1/earthquakes/")

        assert response.status_code == 200
        data = response.json()
        assert "earthquakes" in data
        assert "pagination" in data
        assert "total" in data["pagination"]
        assert "page" in data["pagination"]
        assert "size" in data["pagination"]
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["size"] == 50
        assert isinstance(data["earthquakes"], list)

    @pytest.mark.asyncio
    async def test_get_earthquakes_with_data(
        self, client_with_db: AsyncClient, sample_earthquake_data: dict
    ):
        """Test getting earthquakes when data exists."""
        # Create some test earthquakes
        earthquake1 = sample_earthquake_data.copy()
        earthquake1["magnitude_value"] = 4.5

        earthquake2 = sample_earthquake_data.copy()
        earthquake2["magnitude_value"] = 6.2
        earthquake2["latitude"] = 34.0522  # Los Angeles

        await client_with_db.post("/api/v1/earthquakes/", json=earthquake1)
        await client_with_db.post("/api/v1/earthquakes/", json=earthquake2)

        # Get all earthquakes
        response = await client_with_db.get("/api/v1/earthquakes/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["earthquakes"]) >= 2
        assert data["pagination"]["total"] >= 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["size"] == 50

    @pytest.mark.asyncio
    async def test_get_earthquakes_with_pagination(
        self, client_with_db: AsyncClient, sample_earthquake_data: dict
    ):
        """Test earthquake pagination."""
        # Create multiple earthquakes
        for i in range(5):
            earthquake = sample_earthquake_data.copy()
            earthquake["magnitude_value"] = 4.0 + i * 0.5
            earthquake["latitude"] = 37.0 + i * 0.1  # Vary location slightly
            await client_with_db.post("/api/v1/earthquakes/", json=earthquake)

        # Test pagination
        response = await client_with_db.get("/api/v1/earthquakes/?page=1&size=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["earthquakes"]) <= 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["size"] == 2
        assert data["pagination"]["total"] >= 5

        # Test second page
        response = await client_with_db.get("/api/v1/earthquakes/?page=2&size=2")
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 2

    @pytest.mark.asyncio
    async def test_get_earthquakes_with_magnitude_filter(
        self, client_with_db: AsyncClient, sample_earthquake_data: dict
    ):
        """Test filtering earthquakes by magnitude."""
        # Create earthquakes with different magnitudes
        low_mag = sample_earthquake_data.copy()
        low_mag["magnitude_value"] = 3.5

        high_mag = sample_earthquake_data.copy()
        high_mag["magnitude_value"] = 7.2
        high_mag["latitude"] = 36.0  # Different location

        await client_with_db.post("/api/v1/earthquakes/", json=low_mag)
        await client_with_db.post("/api/v1/earthquakes/", json=high_mag)

        # Filter by minimum magnitude
        response = await client_with_db.get("/api/v1/earthquakes/?min_magnitude=6.0")

        assert response.status_code == 200
        data = response.json()
        for earthquake in data["earthquakes"]:
            assert earthquake["magnitude_value"] >= 6.0

        # Filter by maximum magnitude
        response = await client_with_db.get("/api/v1/earthquakes/?max_magnitude=4.0")

        assert response.status_code == 200
        data = response.json()
        for earthquake in data["earthquakes"]:
            assert earthquake["magnitude_value"] <= 4.0

    @pytest.mark.asyncio
    async def test_get_earthquakes_with_source_filter(
        self, client_with_db: AsyncClient, sample_earthquake_data: dict
    ):
        """Test filtering earthquakes by source."""
        # Create earthquakes with different sources
        usgs_earthquake = sample_earthquake_data.copy()
        usgs_earthquake["source"] = "USGS"

        emsc_earthquake = sample_earthquake_data.copy()
        emsc_earthquake["source"] = "EMSC"
        emsc_earthquake["latitude"] = 36.0  # Different location

        await client_with_db.post("/api/v1/earthquakes/", json=usgs_earthquake)
        await client_with_db.post("/api/v1/earthquakes/", json=emsc_earthquake)

        # Filter by source
        response = await client_with_db.get("/api/v1/earthquakes/?source=USGS")

        assert response.status_code == 200
        data = response.json()
        for earthquake in data["earthquakes"]:
            assert earthquake["source"] == "USGS"

    @pytest.mark.asyncio
    async def test_get_earthquake_by_id_success(
        self, client_with_db: AsyncClient, sample_earthquake_data: dict
    ):
        """Test getting a specific earthquake by ID."""
        # Create earthquake
        create_response = await client_with_db.post(
            "/api/v1/earthquakes/", json=sample_earthquake_data
        )
        assert create_response.status_code == 201
        created_data = create_response.json()
        earthquake_id = created_data["id"]

        # Get earthquake by ID
        response = await client_with_db.get(f"/api/v1/earthquakes/{earthquake_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == earthquake_id

    @pytest.mark.asyncio
    async def test_get_earthquake_by_id_not_found(self, client_with_db: AsyncClient):
        """Test getting earthquake by non-existent ID."""
        import uuid

        non_existent_uuid = str(uuid.uuid4())
        response = await client_with_db.get(f"/api/v1/earthquakes/{non_existent_uuid}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_earthquakes_invalid_pagination(
        self, client_with_db: AsyncClient
    ):
        """Test invalid pagination parameters."""
        # Invalid page number
        response = await client_with_db.get("/api/v1/earthquakes/?page=0")
        assert response.status_code == 422

        # Invalid page size
        response = await client_with_db.get("/api/v1/earthquakes/?size=0")
        assert response.status_code == 422

        # Page size too large
        response = await client_with_db.get("/api/v1/earthquakes/?size=1001")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_earthquakes_invalid_magnitude_filter(
        self, client_with_db: AsyncClient
    ):
        """Test invalid magnitude filter parameters."""
        # Negative magnitude should be handled gracefully
        response = await client_with_db.get("/api/v1/earthquakes/?min_magnitude=-1")
        # This might be accepted as it's a filter parameter
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_earthquake_endpoints_comprehensive_flow(
        self, client_with_db: AsyncClient, sample_earthquake_data: dict
    ):
        """Test comprehensive flow of earthquake operations."""
        # 1. Initially get earthquakes
        response = await client_with_db.get("/api/v1/earthquakes/")
        initial_count = response.json()["pagination"]["total"]

        # 2. Create earthquake
        create_response = await client_with_db.post(
            "/api/v1/earthquakes/", json=sample_earthquake_data
        )
        assert create_response.status_code == 201
        earthquake_id = create_response.json()["id"]

        # 3. Verify count increased
        response = await client_with_db.get("/api/v1/earthquakes/")
        assert response.json()["pagination"]["total"] == initial_count + 1

        # 4. Get specific earthquake
        response = await client_with_db.get(f"/api/v1/earthquakes/{earthquake_id}")
        assert response.status_code == 200
        assert response.json()["id"] == earthquake_id

        # 5. Filter by magnitude
        response = await client_with_db.get(
            f"/api/v1/earthquakes/?min_magnitude={sample_earthquake_data['magnitude_value']}"
        )
        assert response.status_code == 200
        filtered_earthquakes = response.json()["earthquakes"]
        earthquake_ids = [eq["id"] for eq in filtered_earthquakes]
        assert earthquake_id in earthquake_ids
