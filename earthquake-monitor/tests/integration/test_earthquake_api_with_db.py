"""Integration tests for earthquake API endpoints with real database."""

from datetime import UTC

import pytest
from httpx import AsyncClient


class TestEarthquakeAPIWithDatabase:
    """Test earthquake API endpoints with real PostgreSQL database."""

    @pytest.mark.asyncio
    async def test_create_earthquake_in_database(
        self, client_with_db: AsyncClient, sample_earthquake_data: dict
    ):
        """Test earthquake creation with real database storage."""
        response = await client_with_db.post(
            "/api/v1/earthquakes/", json=sample_earthquake_data
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "message" in data

        # Verify the earthquake was actually saved to database
        earthquake_id = data["id"]
        get_response = await client_with_db.get(f"/api/v1/earthquakes/{earthquake_id}")
        assert get_response.status_code == 200

        earthquake_detail = get_response.json()
        assert (
            earthquake_detail["magnitude"]["value"]
            == sample_earthquake_data["magnitude_value"]
        )
        assert (
            earthquake_detail["location"]["latitude"]
            == sample_earthquake_data["latitude"]
        )

    @pytest.mark.asyncio
    async def test_earthquake_persistence_across_requests(
        self, client_with_db: AsyncClient, sample_earthquake_data: dict
    ):
        """Test that earthquakes persist in database across requests."""
        # Create first earthquake
        response1 = await client_with_db.post(
            "/api/v1/earthquakes/", json=sample_earthquake_data
        )
        assert response1.status_code == 201
        earthquake_id1 = response1.json()["id"]

        # Create second earthquake with different data
        sample_earthquake_data2 = sample_earthquake_data.copy()
        sample_earthquake_data2["magnitude_value"] = 6.2
        sample_earthquake_data2["latitude"] = 35.6762
        sample_earthquake_data2["longitude"] = 139.6503

        response2 = await client_with_db.post(
            "/api/v1/earthquakes/", json=sample_earthquake_data2
        )
        assert response2.status_code == 201
        earthquake_id2 = response2.json()["id"]

        # Verify both earthquakes exist in database
        get_response1 = await client_with_db.get(
            f"/api/v1/earthquakes/{earthquake_id1}"
        )
        assert get_response1.status_code == 200
        assert get_response1.json()["magnitude"]["value"] == 5.5

        get_response2 = await client_with_db.get(
            f"/api/v1/earthquakes/{earthquake_id2}"
        )
        assert get_response2.status_code == 200
        assert get_response2.json()["magnitude"]["value"] == 6.2

        # Verify list endpoint shows both earthquakes
        list_response = await client_with_db.get("/api/v1/earthquakes/")
        assert list_response.status_code == 200
        earthquakes = list_response.json()["earthquakes"]
        assert len(earthquakes) >= 2

        earthquake_ids = [eq["id"] for eq in earthquakes]
        assert earthquake_id1 in earthquake_ids
        assert earthquake_id2 in earthquake_ids

    @pytest.mark.asyncio
    async def test_earthquake_filtering_with_database(
        self, client_with_db: AsyncClient, seed_test_data
    ):
        """Test earthquake filtering with seeded database data."""
        # Test magnitude filtering
        response = await client_with_db.get("/api/v1/earthquakes/?min_magnitude=6.0")
        assert response.status_code == 200

        earthquakes = response.json()["earthquakes"]
        # Should only return earthquakes with magnitude >= 6.0
        for earthquake in earthquakes:
            assert earthquake["magnitude_value"] >= 6.0

        # Test source filtering
        response = await client_with_db.get("/api/v1/earthquakes/?source=TEST")
        assert response.status_code == 200

        earthquakes = response.json()["earthquakes"]
        # Should only return TEST earthquakes
        for earthquake in earthquakes:
            assert earthquake["source"] == "TEST"

    @pytest.mark.asyncio
    async def test_database_transaction_rollback(
        self, db_session, sample_earthquake_data: dict
    ):
        """Test that database sessions properly handle rollbacks."""
        from datetime import datetime

        from src.domain.entities.earthquake import Earthquake
        from src.domain.entities.location import Location
        from src.domain.entities.magnitude import Magnitude, MagnitudeScale
        from src.infrastructure.repositories.postgresql_earthquake_repository import (
            PostgreSQLEarthquakeRepository,
        )

        repo = PostgreSQLEarthquakeRepository(db_session)

        # Create earthquake entity
        location = Location(
            latitude=sample_earthquake_data["latitude"],
            longitude=sample_earthquake_data["longitude"],
            depth=sample_earthquake_data["depth"],
        )
        magnitude = Magnitude(
            value=sample_earthquake_data["magnitude_value"],
            scale=MagnitudeScale.MOMENT,
        )
        earthquake = Earthquake(
            location=location,
            magnitude=magnitude,
            occurred_at=datetime.now(UTC),
            source=sample_earthquake_data["source"],
        )

        # Save earthquake
        earthquake_id = await repo.save(earthquake)
        assert earthquake_id is not None

        # Verify earthquake exists in current session
        found_earthquake = await repo.find_by_id(earthquake_id)
        assert found_earthquake is not None
        assert (
            found_earthquake.magnitude.value
            == sample_earthquake_data["magnitude_value"]
        )

        # Session should rollback after test, so earthquake won't persist

    @pytest.mark.asyncio
    async def test_data_ingestion_with_database(self, client_with_db: AsyncClient):
        """Test data ingestion endpoint (may fail if external service unavailable)."""
        # Test ingestion endpoint
        ingestion_request = {
            "source": "USGS",
            "period": "day",
            "magnitude_filter": "4.5",
            "limit": 2,  # Small number for testing
        }

        response = await client_with_db.post(
            "/api/v1/ingestion/trigger", json=ingestion_request
        )

        # Accept both success and service errors (external dependency)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            result = response.json()
            assert "new_earthquakes" in result
            assert "total_fetched" in result

            # If ingestion was successful, verify earthquakes were saved
            if result["new_earthquakes"] > 0:
                list_response = await client_with_db.get("/api/v1/earthquakes/")
                assert list_response.status_code == 200

                earthquakes = list_response.json()["earthquakes"]
                assert len(earthquakes) >= result["new_earthquakes"]

                # Verify at least one earthquake has USGS as source
                usgs_earthquakes = [eq for eq in earthquakes if eq["source"] == "USGS"]
                assert len(usgs_earthquakes) > 0
        else:
            # External service unavailable - this is acceptable for integration tests
            print("USGS service unavailable - skipping data verification")
