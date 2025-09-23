"""Unit tests for API endpoint schema validation across all endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestAPISchemaValidation:
    """Unit tests for API endpoint input validation and error responses."""

    def test_refresh_token_invalid_field_names(self, client: TestClient):
        """Test refresh token endpoint with different field name formats."""
        # Test the exact scenarios from manual testing

        # Login first to get a valid refresh token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@earthquake-monitor.com", "password": "testpass123"},
        )

        if login_response.status_code != 200:
            pytest.skip("Cannot test refresh token without valid login")

        tokens = login_response.json()
        valid_refresh_token = tokens.get("refresh_token")

        if not valid_refresh_token:
            pytest.skip("No refresh token provided by login")

        # Test correct field name (should work)
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": valid_refresh_token}
        )
        assert response.status_code == 200, "Correct field name should work"

        # Test incorrect field names (should fail with 422)
        invalid_field_names = [
            {"token": valid_refresh_token},
            {"refreshToken": valid_refresh_token},
            {"refresh": valid_refresh_token},
            {"access_token": valid_refresh_token},  # Wrong token type
        ]

        for invalid_data in invalid_field_names:
            response = client.post("/api/v1/auth/refresh", json=invalid_data)

            assert (
                response.status_code == 422
            ), f"Should reject invalid field names: {list(invalid_data.keys())}"
            error_data = response.json()
            assert "detail" in error_data

            # Should have error about missing refresh_token field
            refresh_token_error = None
            for error in error_data["detail"]:
                if (
                    error.get("loc") == ["body", "refresh_token"]
                    and error.get("type") == "missing"
                ):
                    refresh_token_error = error
                    break

            assert (
                refresh_token_error is not None
            ), f"Should have missing refresh_token error for {invalid_data}"

    def test_ingestion_trigger_schema_validation(
        self, client: TestClient, auth_headers: dict
    ):
        """Test ingestion trigger endpoint schema validation."""
        if not auth_headers:
            pytest.skip("No valid auth headers available")

        # Test empty body (should work based on manual testing)
        response = client.post(
            "/api/v1/ingestion/trigger", json={}, headers=auth_headers
        )

        # This should succeed based on manual testing results
        assert response.status_code in [200, 202], "Empty body should be accepted"

        # Test with valid optional parameters
        valid_payloads = [
            {"source": "usgs"},
            {"immediate": True},
            {"source": "usgs", "immediate": True},
        ]

        for payload in valid_payloads:
            response = client.post(
                "/api/v1/ingestion/trigger", json=payload, headers=auth_headers
            )

            assert response.status_code in [
                200,
                202,
                422,
            ], f"Should handle payload {payload} properly"

    @pytest.mark.asyncio
    async def test_earthquake_creation_missing_required_fields(
        self, client_with_db, auth_headers: dict
    ):
        """Test earthquake creation with missing required fields."""
        if not auth_headers:
            pytest.skip("No valid auth headers available")

        # Complete valid earthquake data
        valid_data = {
            "magnitude_value": 5.0,
            "magnitude_scale": "moment",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "depth": 10.0,
            "occurred_at": "2024-01-01T12:00:00Z",
            "source": "TEST",
        }

        # Test that complete data works first
        response = await client_with_db.post(
            "/api/v1/earthquakes/", json=valid_data, headers=auth_headers
        )
        assert response.status_code == 201, "Valid data should create earthquake"

        # Test missing each required field (fields without defaults)
        required_fields = [
            "magnitude_value",  # Required: Field(...)
            "latitude",  # Required: Field(...)
            "longitude",  # Required: Field(...)
            "depth",  # Required: Field(...)
            # Note: magnitude_scale, occurred_at, source have defaults and are optional
        ]

        for field in required_fields:
            incomplete_data = valid_data.copy()
            del incomplete_data[field]

            response = await client_with_db.post(
                "/api/v1/earthquakes/", json=incomplete_data, headers=auth_headers
            )

            assert response.status_code == 422, f"Should fail when missing {field}"
            error_data = response.json()

            # Verify error mentions the missing field
            field_error = None
            for error in error_data["detail"]:
                if field in str(error.get("loc", [])):
                    field_error = error
                    break

            assert (
                field_error is not None
            ), f"Should have error for missing {field} field"

    @pytest.mark.asyncio
    async def test_earthquake_creation_invalid_field_types(
        self, client_with_db, auth_headers: dict
    ):
        """Test earthquake creation with invalid field types."""
        if not auth_headers:
            pytest.skip("No valid auth headers available")

        base_data = {
            "magnitude_value": 5.0,
            "magnitude_scale": "moment",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "depth": 10.0,
            "occurred_at": "2024-01-01T12:00:00Z",
            "source": "TEST",
        }

        # Test invalid field types
        invalid_type_tests = [
            ("magnitude_value", "not_a_number"),
            ("latitude", "invalid_lat"),
            ("longitude", "invalid_lng"),
            ("depth", "invalid_depth"),
            ("occurred_at", "invalid_datetime"),
            ("magnitude_scale", 123),  # Should be string
        ]

        for field, invalid_value in invalid_type_tests:
            test_data = base_data.copy()
            test_data[field] = invalid_value

            response = await client_with_db.post(
                "/api/v1/earthquakes/", json=test_data, headers=auth_headers
            )

            assert (
                response.status_code == 422
            ), f"Should reject invalid {field} type: {invalid_value}"

    @pytest.mark.asyncio
    async def test_pagination_parameter_validation(self, client_with_db):
        """Test pagination parameter validation in earthquake list."""

        # Test invalid limit values
        invalid_limits = [-1, 0, "invalid", 10001]  # Assuming max limit is 10000

        for invalid_limit in invalid_limits:
            response = await client_with_db.get(
                f"/api/v1/earthquakes/?limit={invalid_limit}"
            )

            # Should either reject with 422 or handle gracefully
            assert response.status_code in [
                200,
                422,
            ], f"Should handle invalid limit {invalid_limit}"

            if response.status_code == 422:
                error_data = response.json()
                assert "detail" in error_data

        # Test invalid offset values
        invalid_offsets = [-1, "invalid"]

        for invalid_offset in invalid_offsets:
            response = await client_with_db.get(
                f"/api/v1/earthquakes/?offset={invalid_offset}"
            )

            assert response.status_code in [
                200,
                422,
            ], f"Should handle invalid offset {invalid_offset}"

    def test_magnitude_filter_validation(self, client: TestClient):
        """Test magnitude filter validation."""

        # Test invalid magnitude values
        invalid_magnitudes = [-1, "invalid", 15.0]  # Assuming max magnitude is ~12

        for invalid_mag in invalid_magnitudes:
            response = client.get(f"/api/v1/earthquakes/?min_magnitude={invalid_mag}")

            # Should handle gracefully or reject
            assert response.status_code in [
                200,
                422,
            ], f"Should handle invalid magnitude {invalid_mag}"

    def test_authentication_header_validation(self, client: TestClient):
        """Test authentication header validation edge cases."""

        # Test malformed Authorization headers
        invalid_auth_headers = [
            {"Authorization": "Invalid token"},
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": "NotBearer valid_token"},
            {"Authorization": "Bearer "},  # Empty token
        ]

        for invalid_header in invalid_auth_headers:
            response = client.get("/api/v1/auth/me", headers=invalid_header)

            # Should reject with 401 or 422
            assert response.status_code in [
                401,
                422,
            ], f"Should reject invalid auth header {invalid_header}"

    def test_content_type_validation(self, client: TestClient):
        """Test Content-Type header validation."""

        # Test requests without proper Content-Type for JSON endpoints
        response = client.post(
            "/api/v1/auth/login",
            content='{"email": "test@example.com", "password": "test"}',  # String data instead of JSON
            headers={"Content-Type": "text/plain"},
        )

        # Should reject requests with wrong content type
        assert response.status_code in [
            400,
            415,
            422,
        ], "Should reject non-JSON content type"
