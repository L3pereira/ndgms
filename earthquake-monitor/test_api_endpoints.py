#!/usr/bin/env python3
"""
Comprehensive API Endpoints Test
Tests all available API endpoints for functionality
"""

import asyncio
import json
from datetime import datetime

import httpx


class APIEndpointTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.access_token = None
        self.refresh_token = None
        self.test_results = {}

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
                return True
            else:
                print(
                    f"❌ Authentication failed: {response.status_code} - {response.text}"
                )
                return False

    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.access_token}"}

    async def test_endpoint(
        self, method, path, description, requires_auth=True, json_data=None
    ):
        """Test a single endpoint"""
        url = f"{self.base_url}{path}"
        print(f"🧪 Testing {method.upper()} {path} - {description}")

        try:
            headers = self.get_auth_headers() if requires_auth else {}

            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=json_data)
                else:
                    response = await client.request(
                        method, url, headers=headers, json=json_data
                    )

                # Record result
                result = {
                    "status_code": response.status_code,
                    "success": 200 <= response.status_code < 300,
                    "response_size": len(response.content),
                    "headers": dict(response.headers),
                }

                if response.status_code < 400:
                    try:
                        result["data"] = response.json()
                    except:
                        result["text"] = (
                            response.text[:200] + "..."
                            if len(response.text) > 200
                            else response.text
                        )

                self.test_results[f"{method.upper()} {path}"] = result

                # Print result
                status_icon = "✅" if result["success"] else "❌"
                print(
                    f"   {status_icon} {response.status_code} - {len(response.content)} bytes"
                )

                if result["success"] and "data" in result:
                    if isinstance(result["data"], dict):
                        if "total" in str(result["data"]):
                            print(f"      📊 Response contains data counts")
                        if "earthquakes" in str(result["data"]):
                            print(f"      🌍 Contains earthquake data")
                    elif isinstance(result["data"], list):
                        print(f"      📋 List with {len(result['data'])} items")

                return result

        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.test_results[f"{method.upper()} {path}"] = {
                "error": str(e),
                "success": False,
            }
            return False

    async def test_all_endpoints(self):
        """Test all available endpoints"""
        print("🚀 Starting comprehensive API endpoint testing...\n")

        # 1. Health endpoint (no auth required)
        await self.test_endpoint("GET", "/health", "Health check", requires_auth=False)

        # 2. Scheduler test endpoint (no auth required)
        await self.test_endpoint(
            "GET", "/test-scheduler", "Scheduler status", requires_auth=False
        )

        # 3. Authentication endpoints
        print("\n📝 Testing Authentication Endpoints:")
        timestamp = int(datetime.now().timestamp())
        await self.test_endpoint(
            "POST",
            "/api/v1/auth/register",
            "User registration",
            requires_auth=False,
            json_data={
                "email": f"test-{timestamp}@example.com",
                "username": f"test-{timestamp}",
                "password": "testpass123",
                "full_name": "Test User",
            },
        )

        await self.test_endpoint("GET", "/api/v1/auth/me", "Get current user info")
        await self.test_endpoint(
            "POST",
            "/api/v1/auth/refresh",
            "Refresh token",
            json_data=(
                {"refresh_token": self.refresh_token} if self.refresh_token else {}
            ),
        )
        await self.test_endpoint("GET", "/api/v1/auth/verify", "Verify token")
        await self.test_endpoint("POST", "/api/v1/auth/logout", "Logout")

        # 4. Earthquake endpoints
        print("\n🌍 Testing Earthquake Endpoints:")
        await self.test_endpoint("GET", "/api/v1/earthquakes/", "Get earthquakes list")
        await self.test_endpoint(
            "GET", "/api/v1/earthquakes/?limit=5", "Get earthquakes with limit"
        )
        await self.test_endpoint(
            "GET",
            "/api/v1/earthquakes/?min_magnitude=2.0",
            "Get earthquakes by magnitude",
        )

        # Test creating an earthquake
        await self.test_endpoint(
            "POST",
            "/api/v1/earthquakes/",
            "Create earthquake",
            json_data={
                "magnitude_value": 3.5,
                "magnitude_scale": "moment",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "depth": 10.0,
                "occurred_at": datetime.now().isoformat(),
                "source": "TEST_API",
            },
        )

        # Try to get a specific earthquake (this might fail if no earthquakes exist)
        earthquakes_response = self.test_results.get("GET /api/v1/earthquakes/")
        if (
            earthquakes_response
            and earthquakes_response.get("success")
            and earthquakes_response.get("data")
        ):
            data = earthquakes_response["data"]
            if isinstance(data, dict) and "earthquakes" in data and data["earthquakes"]:
                earthquake_id = data["earthquakes"][0]["id"]
                await self.test_endpoint(
                    "GET",
                    f"/api/v1/earthquakes/{earthquake_id}",
                    "Get specific earthquake",
                )

        # 5. Ingestion endpoints
        print("\n📥 Testing Ingestion Endpoints:")
        await self.test_endpoint(
            "GET", "/api/v1/ingestion/sources", "Get ingestion sources"
        )
        await self.test_endpoint(
            "GET", "/api/v1/ingestion/status", "Get ingestion status"
        )
        await self.test_endpoint(
            "POST",
            "/api/v1/ingestion/trigger",
            "Trigger manual ingestion",
            json_data={
                "source": "USGS",
                "period": "hour",
                "magnitude_filter": "2.5",
                "limit": 50,
            },
        )

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 API ENDPOINT TEST SUMMARY")
        print("=" * 60)

        total_tests = len(self.test_results)
        successful_tests = sum(
            1 for result in self.test_results.values() if result.get("success", False)
        )
        failed_tests = total_tests - successful_tests

        print(f"Total endpoints tested: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")

        print("\n📋 Detailed Results:")
        for endpoint, result in self.test_results.items():
            status_icon = "✅" if result.get("success", False) else "❌"
            status_code = result.get("status_code", "ERR")
            print(f"  {status_icon} {endpoint:40} - {status_code}")

        print("\n❌ Failed Endpoints:")
        for endpoint, result in self.test_results.items():
            if not result.get("success", False):
                error = result.get(
                    "error", f"HTTP {result.get('status_code', 'Unknown')}"
                )
                print(f"  • {endpoint}: {error}")


async def main():
    tester = APIEndpointTester()

    # Authenticate first
    if not await tester.authenticate():
        print("❌ Cannot proceed without authentication")
        return

    # Test all endpoints
    await tester.test_all_endpoints()

    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
