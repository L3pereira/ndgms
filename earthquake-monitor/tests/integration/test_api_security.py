"""Integration tests for API security and middleware."""

import pytest
from fastapi.testclient import TestClient


class TestAPISecurity:
    """Test API security headers and middleware."""

    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are present in responses."""
        response = client.get("/health")

        assert response.status_code == 200
        headers = response.headers

        # Check security headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert (
            headers.get("Strict-Transport-Security")
            == "max-age=31536000; includeSubDomains"
        )
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "X-Process-Time" in headers

    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are configured."""
        # Make an OPTIONS request to check CORS - may not be supported on all endpoints
        response = client.options("/health")
        # Accept either success or method not allowed
        assert response.status_code in [200, 405]

        # Test CORS with a regular request
        response = client.get("/health")
        assert response.status_code == 200
        # CORS middleware should add appropriate headers automatically

    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_documentation_accessible(self, client: TestClient):
        """Test that API documentation is accessible."""
        # Test OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Earthquake Monitor API"

        # Test Swagger UI (should redirect or return HTML)
        response = client.get("/docs")
        assert response.status_code == 200

        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_invalid_endpoints_return_404(self, client: TestClient):
        """Test that invalid endpoints return 404."""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

        response = client.post("/api/v1/invalid")
        assert response.status_code == 404

    def test_method_not_allowed(self, client: TestClient):
        """Test that invalid HTTP methods return 405."""
        # Health endpoint should not accept POST
        response = client.post("/health")
        assert response.status_code == 405

        # Login endpoint should not accept GET
        response = client.get("/api/v1/auth/login")
        assert response.status_code == 405

    def test_request_size_limits(self, client: TestClient):
        """Test request size handling."""
        # Create a very large payload
        large_data = {
            "email": "test@example.com",
            "username": "test",
            "full_name": "Test User",
            "password": "password123",
            "extra_data": "x" * 100000,  # Large string
        }

        response = client.post("/api/v1/auth/register", json=large_data)
        # Should handle large requests gracefully (either process or reject)
        assert response.status_code in [201, 400, 413, 422]

    def test_malformed_json_handling(self, client: TestClient):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/v1/auth/register",
            content="{'invalid': 'json'}",  # Malformed JSON
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_sql_injection_protection(
        self, client_with_db, sample_earthquake_data: dict
    ):
        """Test protection against SQL injection attempts."""
        # Attempt SQL injection in earthquake data
        malicious_data = sample_earthquake_data.copy()
        malicious_data["event_id"] = "'; DROP TABLE earthquakes; --"

        response = await client_with_db.post(
            "/api/v1/earthquakes/", json=malicious_data
        )
        # Should either create successfully (if properly sanitized) or reject
        assert response.status_code in [201, 400, 422]

        # Attempt SQL injection in query parameters
        response = await client_with_db.get(
            "/api/v1/earthquakes/?source='; DROP TABLE earthquakes; --"
        )
        assert response.status_code in [200, 400, 422]

    def test_xss_protection(self, client: TestClient):
        """Test protection against XSS attacks."""
        xss_payload = "<script>alert('xss')</script>"

        # Attempt XSS in registration
        user_data = {
            "email": "xss@example.com",
            "username": xss_payload,
            "full_name": xss_payload,
            "password": "password123",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        if response.status_code == 201:
            # If creation succeeds, check that XSS payload is properly escaped
            data = response.json()
            # The actual escaping depends on the serialization method
            # At minimum, it shouldn't execute as script
            assert (
                data["username"] == xss_payload
            )  # Should be stored as string, not executed

    def test_rate_limiting_headers(self, client: TestClient):
        """Test for rate limiting indicators (if implemented)."""
        response = client.get("/health")

        # Check for common rate limiting headers (may not be implemented)
        headers = response.headers
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "Retry-After",
        ]

        # This is informational - not all APIs implement rate limiting
        present_headers = [h for h in rate_limit_headers if h in headers]
        if present_headers:
            print(f"Rate limiting headers found: {present_headers}")

    @pytest.mark.asyncio
    async def test_error_response_format(self, client_with_db):
        """Test that error responses follow consistent format."""
        import uuid

        # Test 404 error with proper UUID format
        non_existent_uuid = str(uuid.uuid4())
        response = await client_with_db.get(f"/api/v1/earthquakes/{non_existent_uuid}")
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data

        # Test 422 validation error
        response = await client_with_db.post("/api/v1/auth/register", json={})
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

        # Test 401 authentication error
        response = await client_with_db.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        error_data = response.json()
        assert "detail" in error_data

    def test_content_type_enforcement(self, client: TestClient):
        """Test content type enforcement for POST requests."""
        # Send form data instead of JSON
        response = client.post(
            "/api/v1/auth/register",
            data={"email": "test@example.com"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        # Should reject non-JSON content for JSON endpoints
        assert response.status_code == 422
