#!/usr/bin/env python3
"""
Complete Scheduler → WebSocket Integration Test
Tests the full data flow: Scheduler (20s) → USGS → Database → Events → WebSocket
"""

import asyncio
import json
import time
from datetime import datetime

import httpx
import websockets


class IntegrationTester:
    def __init__(self):
        self.access_token = None
        self.received_events = []
        self.earthquake_ids_seen = set()

    async def authenticate(self):
        """Get authentication token"""
        print("🔐 Authenticating...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                json={"email": "admin@earthquake-monitor.com", "password": "admin123"},
            )

            if response.status_code != 200:
                raise Exception(f"Login failed: {response.text}")

            data = response.json()
            self.access_token = data["access_token"]
            print("✅ Authenticated successfully")

    async def check_scheduler_status(self):
        """Check if scheduler is running"""
        print("⏰ Checking scheduler status...")
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/test-scheduler")

            if response.status_code == 200:
                data = response.json()
                scheduler = data.get("scheduler", {})
                print(f"   Running: {scheduler.get('running', False)}")
                print(f"   Jobs: {scheduler.get('jobs', 0)}")

                job_details = scheduler.get("job_details", {})
                usgs_job = job_details.get("usgs_ingestion", {})
                if usgs_job:
                    print(f"   Next run: {usgs_job.get('next_run', 'N/A')}")
                    print(f"   Trigger: {usgs_job.get('trigger', 'N/A')}")

                return scheduler.get("running", False)
            else:
                print(f"❌ Failed to get scheduler status: {response.text}")
                return False

    async def get_current_earthquake_count(self):
        """Get current number of earthquakes in database"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/api/v1/earthquakes?limit=1",
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("pagination", {}).get("total", 0)
            return 0

    async def listen_to_websocket(self, duration_minutes=1.5):
        """Listen to WebSocket for specified duration"""
        print(
            f"📡 Starting WebSocket integration test for {duration_minutes} minutes..."
        )

        uri = "ws://localhost:8000/api/v1/ws"

        try:
            async with websockets.connect(uri) as websocket:
                print("✅ WebSocket connected!")

                # Subscribe to both earthquake events and alerts
                await websocket.send(json.dumps({"action": "subscribe_earthquakes"}))
                response = await websocket.recv()
                print(f"📧 Earthquake subscription: {response}")

                await websocket.send(json.dumps({"action": "subscribe_alerts"}))
                response = await websocket.recv()
                print(f"🚨 Alert subscription: {response}")

                start_time = time.time()
                end_time = start_time + (duration_minutes * 60)

                print("\\n👂 Listening for events...")
                print(
                    f"   Expected scheduler runs: ~{duration_minutes * 3} (every 20 seconds)"
                )
                print("   Looking for NEW earthquakes only (no duplicates)")
                print("   High magnitude alerts: magnitude ≥ 5.0")
                print(
                    "   Min magnitude for ingestion: 1.0 (should capture more events)"
                )
                print()

                while time.time() < end_time:
                    try:
                        # Wait for message with timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=25.0)
                        event_data = json.loads(message)

                        await self.process_event(event_data)

                    except TimeoutError:
                        remaining = int(end_time - time.time())
                        print(
                            f"⏳ No events in last 25s (waiting {remaining}s more...)"
                        )
                        continue

                print("\\n📊 Final Summary:")
                print(f"   Total events received: {len(self.received_events)}")
                print(f"   Unique earthquakes: {len(self.earthquake_ids_seen)}")
                print("   Event types breakdown:")

                event_types = {}
                for event in self.received_events:
                    event_type = event.get("type", "unknown")
                    event_types[event_type] = event_types.get(event_type, 0) + 1

                for event_type, count in event_types.items():
                    print(f"     {event_type}: {count}")

        except Exception as e:
            print(f"❌ WebSocket error: {e}")

    async def process_event(self, event_data):
        """Process received WebSocket event"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        event_type = event_data.get("type", "unknown")

        if event_type == "earthquake_detected":
            data = event_data.get("data", {})
            earthquake_id = data.get(
                "id", "unknown"
            )  # Note: using 'id' not 'earthquake_id'
            magnitude = data.get("magnitude", 0)
            latitude = data.get("latitude", 0)
            longitude = data.get("longitude", 0)

            # Check if this is a NEW earthquake
            is_new = earthquake_id not in self.earthquake_ids_seen
            self.earthquake_ids_seen.add(earthquake_id)

            status = "🆕 NEW" if is_new else "🔄 DUPLICATE"

            print(
                f"[{timestamp}] 🌍 {status} Earthquake: M{magnitude:.1f} at ({latitude:.2f}, {longitude:.2f})"
            )
            print(f"          ID: {earthquake_id}")

            if not is_new:
                print("          ⚠️  WARNING: Received duplicate earthquake event!")

        elif event_type == "high_magnitude_alert":
            data = event_data.get("data", {})
            magnitude = data.get("magnitude", 0)
            alert_level = data.get("alert_level", "unknown")

            print(
                f"[{timestamp}] 🚨 HIGH MAGNITUDE ALERT: M{magnitude:.1f} ({alert_level})"
            )

        elif event_type == "recent_earthquakes_update":
            data = event_data.get("data", {})
            count = data.get("count", 0)
            print(
                f"[{timestamp}] 📊 RECENT EARTHQUAKES UPDATE: {count} earthquakes in last 24h"
            )

        elif event_type == "high_magnitude_earthquakes_update":
            data = event_data.get("data", {})
            count = data.get("count", 0)
            print(
                f"[{timestamp}] 🚨 HIGH MAG UPDATE: {count} significant earthquakes in last 7 days"
            )

        else:
            print(f"[{timestamp}] ❓ Unknown event: {event_type}")

        # Store event
        self.received_events.append(
            {"timestamp": timestamp, "type": event_type, "data": event_data}
        )


async def main():
    print("🧪 COMPLETE SCHEDULER + WEBSOCKET INTEGRATION TEST")
    print("=" * 60)
    print("Testing:")
    print("• 20-second scheduler interval (USGS_INGESTION_INTERVAL_MINUTES=0.33)")
    print("• Database-driven WebSocket events (no duplicate data)")
    print("• Clean Architecture flow: Scheduler → Use Cases → Events → WebSocket")
    print("• Magnitude-based filtering and alerts")
    print()

    tester = IntegrationTester()

    try:
        # Step 1: Authenticate
        await tester.authenticate()

        # Step 2: Check scheduler
        scheduler_running = await tester.check_scheduler_status()
        if not scheduler_running:
            print("❌ Scheduler is not running! Please check the container.")
            return

        # Step 3: Get baseline earthquake count
        initial_count = await tester.get_current_earthquake_count()
        print(f"📊 Current earthquakes in database: {initial_count}")
        print()

        # Step 4: Listen to WebSocket for 1.5 minutes (should see ~4-5 scheduler runs)
        await tester.listen_to_websocket(duration_minutes=1.5)

        # Step 5: Final check
        final_count = await tester.get_current_earthquake_count()
        new_earthquakes = final_count - initial_count

        print("\\n📈 Database changes:")
        print(f"   Initial count: {initial_count}")
        print(f"   Final count: {final_count}")
        print(f"   New earthquakes: {new_earthquakes}")

        # Results analysis
        if new_earthquakes > 0 and len(tester.received_events) > 0:
            print("\\n✅ SUCCESS: Complete data flow working!")
            print("   • Scheduler running ✓")
            print("   • Database updates ✓")
            print("   • WebSocket events ✓")
        elif len(tester.received_events) == 0:
            print(
                "\\n⚠️  No WebSocket events received (might be no new earthquake data)"
            )
            print("   This is normal if USGS has no new earthquakes during test period")
        else:
            print("\\n❓ Mixed results - check logs for details")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
