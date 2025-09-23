#!/usr/bin/env python3
"""
Test specific failing endpoints with proper data formats
"""

import asyncio
import json
from datetime import datetime

import httpx


class SpecificEndpointTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.access_token = None
        self.refresh_token = None

    async def authenticate(self):
        """Get authentication token"""
        print("🔐 Authenticating...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": "admin@earthquake-monitor.com", "password": "admin123"},
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data.get("refresh_token")
                print(f"✅ Authentication successful")
                print(f"   Access token: {self.access_token[:20]}...")
                if self.refresh_token:
                    print(f"   Refresh token: {self.refresh_token[:20]}...")
                return True
            else:
                print(
                    f"❌ Authentication failed: {response.status_code} - {response.text}"
                )
                return False

    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.access_token}"}

    async def test_user_registration(self):
        """Test user registration with different user"""
        print("\n👤 Testing User Registration:")

        # Generate unique email
        timestamp = str(int(datetime.now().timestamp()))
        test_user = {
            "email": f"testuser{timestamp}@example.com",
            "username": f"testuser{timestamp}",
            "password": "SecurePass123!",
            "full_name": f"Test User {timestamp}",
        }

        print(f"   Attempting to register: {test_user['email']}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/auth/register", json=test_user
            )

            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")

            if response.status_code == 200 or response.status_code == 201:
                print("   ✅ Registration successful!")
                return True
            else:
                print("   ❌ Registration failed")
                try:
                    error_data = response.json()
                    print(f"   Error details: {json.dumps(error_data, indent=2)}")
                except:
                    pass
                return False

    async def test_refresh_token(self):
        """Test refresh token endpoint"""
        print("\n🔄 Testing Refresh Token:")

        if not self.refresh_token:
            print("   ❌ No refresh token available from login")
            return False

        print(f"   Using refresh token: {self.refresh_token[:20]}...")

        async with httpx.AsyncClient() as client:
            # Try different request formats
            test_formats = [
                {"refresh_token": self.refresh_token},
                {"token": self.refresh_token},
                {"refreshToken": self.refresh_token},
            ]

            for i, data in enumerate(test_formats, 1):
                print(f"   Attempt {i}: {list(data.keys())[0]}")
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/refresh", json=data
                )

                print(f"     Status: {response.status_code}")
                if response.status_code == 200:
                    print("     ✅ Refresh successful!")
                    return True
                else:
                    print(f"     Response: {response.text[:100]}...")

        print("   ❌ All refresh attempts failed")
        return False

    async def test_ingestion_trigger(self):
        """Test ingestion trigger endpoint"""
        print("\n📥 Testing Ingestion Trigger:")

        headers = self.get_auth_headers()

        # Try different request formats
        test_formats = [
            {},  # Empty body
            {"source": "usgs"},  # With source
            {"immediate": True},  # With immediate flag
            {"source": "usgs", "immediate": True},  # Both
            {"period": "hour", "magnitude": "2.5"},  # With parameters
        ]

        async with httpx.AsyncClient() as client:
            for i, data in enumerate(test_formats, 1):
                print(f"   Attempt {i}: {data if data else 'empty body'}")
                response = await client.post(
                    f"{self.base_url}/api/v1/ingestion/trigger",
                    json=data,
                    headers=headers,
                )

                print(f"     Status: {response.status_code}")
                print(f"     Response: {response.text}")

                if response.status_code == 200:
                    print("     ✅ Ingestion trigger successful!")
                    return True
                elif response.status_code == 422:
                    try:
                        error_data = response.json()
                        print(
                            f"     Validation error: {json.dumps(error_data, indent=4)}"
                        )
                    except:
                        pass

        print("   ❌ All ingestion trigger attempts failed")
        return False

    async def check_ingestion_endpoint_details(self):
        """Check what the ingestion trigger endpoint expects"""
        print("\n🔍 Checking Ingestion Endpoint Details:")

        # Check OpenAPI spec for this endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/openapi.json")
            if response.status_code == 200:
                openapi_spec = response.json()

                # Look for ingestion trigger endpoint
                paths = openapi_spec.get("paths", {})
                trigger_path = paths.get("/api/v1/ingestion/trigger", {})
                post_method = trigger_path.get("post", {})

                if post_method:
                    print("   📋 Found endpoint specification:")

                    # Check request body
                    request_body = post_method.get("requestBody", {})
                    if request_body:
                        content = request_body.get("content", {})
                        json_schema = content.get("application/json", {})
                        schema = json_schema.get("schema", {})
                        print(f"   Request schema: {json.dumps(schema, indent=2)}")

                    # Check parameters
                    parameters = post_method.get("parameters", [])
                    if parameters:
                        print("   Parameters:")
                        for param in parameters:
                            print(
                                f"     - {param.get('name')}: {param.get('schema', {}).get('type')} ({param.get('required', False)})"
                            )

                    # Check responses
                    responses = post_method.get("responses", {})
                    print(f"   Expected responses: {list(responses.keys())}")

                else:
                    print("   ❌ Endpoint not found in OpenAPI spec")
            else:
                print(f"   ❌ Could not fetch OpenAPI spec: {response.status_code}")


async def main():
    tester = SpecificEndpointTester()

    # Authenticate first
    if not await tester.authenticate():
        print("❌ Cannot proceed without authentication")
        return

    # Test each specific endpoint
    await tester.test_user_registration()
    await tester.test_refresh_token()
    await tester.check_ingestion_endpoint_details()
    await tester.test_ingestion_trigger()


if __name__ == "__main__":
    asyncio.run(main())
