"""Integration tests for authentication API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestAuthAPI:
    """Test authentication API endpoints."""

    def test_register_user_success(self, client: TestClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "password123",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["full_name"] == user_data["full_name"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "hashed_password" not in data  # Should not expose password

    def test_register_user_duplicate_email(self, client: TestClient):
        """Test registration with duplicate email fails."""
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "full_name": "User One",
            "password": "password123",
        }

        # Register first user
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201

        # Try to register with same email
        user_data["username"] = "user2"
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_register_user_invalid_data(self, client: TestClient):
        """Test registration with invalid data fails."""
        # Missing required fields
        response = client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422

        # Invalid email format
        invalid_data = {
            "email": "invalid-email",
            "username": "user",
            "full_name": "User",
            "password": "password123",
        }
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422

    def test_register_user_missing_username(self, client: TestClient):
        """Test registration fails when username field is missing."""
        # This test catches the exact issue found in manual testing
        user_data = {
            "email": "test-missing-username@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User Missing Username",
            # Intentionally missing "username" field
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422
        error_data = response.json()

        # Verify the error specifically mentions missing username
        assert "detail" in error_data
        username_error = None
        for error in error_data["detail"]:
            if (
                error.get("loc") == ["body", "username"]
                and error.get("type") == "missing"
            ):
                username_error = error
                break

        assert (
            username_error is not None
        ), "Should have error for missing username field"
        assert "required" in username_error["msg"].lower()

    def test_register_user_missing_individual_required_fields(self, client: TestClient):
        """Test registration fails for each missing required field."""
        base_data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "password123",
        }

        required_fields = ["email", "username", "full_name", "password"]

        for field in required_fields:
            # Create data missing one required field
            incomplete_data = base_data.copy()
            del incomplete_data[field]

            response = client.post("/api/v1/auth/register", json=incomplete_data)

            assert response.status_code == 422, f"Should fail when missing {field}"
            error_data = response.json()

            # Verify error mentions the missing field
            field_error = None
            for error in error_data["detail"]:
                if (
                    error.get("loc") == ["body", field]
                    and error.get("type") == "missing"
                ):
                    field_error = error
                    break

            assert (
                field_error is not None
            ), f"Should have error for missing {field} field"

    def test_login_success(self, client: TestClient):
        """Test successful user login."""
        # Register user first
        user_data = {
            "email": "loginuser@example.com",
            "username": "loginuser",
            "full_name": "Login User",
            "password": "password123",
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Login
        login_data = {"email": "loginuser@example.com", "password": "password123"}
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 86400

    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials fails."""
        login_data = {"email": "nonexistent@example.com", "password": "wrongpassword"}
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_invalid_data(self, client: TestClient):
        """Test login with invalid data fails."""
        # Missing password
        response = client.post("/api/v1/auth/login", json={"email": "test@example.com"})
        assert response.status_code == 422

        # Invalid email format
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "invalid-email", "password": "password"},
        )
        assert response.status_code == 422

    def test_get_current_user_with_valid_token(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting current user info with valid token."""
        if not auth_headers:
            pytest.skip("No valid auth headers available")

        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@earthquake-monitor.com"
        assert data["username"] == "testuser"
        assert data["is_active"] is True
        assert "id" in data

    def test_get_current_user_without_token(self, client: TestClient):
        """Test getting current user info without token fails."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_with_invalid_token(self, client: TestClient):
        """Test getting current user info with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 422

    def test_refresh_token_success(self, client: TestClient):
        """Test successful token refresh."""
        # Use existing test user
        login_data = {"email": "test@earthquake-monitor.com", "password": "testpass123"}
        login_response = client.post("/api/v1/auth/login", json=login_data)

        assert login_response.status_code == 200
        tokens = login_response.json()
        # Refresh token
        refresh_data = {"refresh_token": tokens["refresh_token"]}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token fails."""
        refresh_data = {"refresh_token": "invalid_refresh_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    def test_verify_token_success(self, client: TestClient, auth_headers: dict):
        """Test successful token verification."""
        if not auth_headers:
            pytest.skip("No valid auth headers available")

        response = client.get("/api/v1/auth/verify", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "user_id" in data

    def test_verify_token_invalid(self, client: TestClient):
        """Test verification with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/verify", headers=headers)
        assert response.status_code == 422

    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """Test successful logout."""
        if not auth_headers:
            pytest.skip("No valid auth headers available")

        response = client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_logout_without_token(self, client: TestClient):
        """Test logout without token fails."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401
