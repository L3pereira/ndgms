"""Integration tests for WebSocket + Database consistency."""

import asyncio

import pytest
from sqlalchemy import text


class TestWebSocketDatabaseIntegration:
    """Test WebSocket events with database persistence."""

    # @pytest.mark.asyncio
    # async def test_earthquake_websocket_database_consistency(
    #     self, client_with_db, async_auth_headers: dict, db_session
    # ):
    #     """Test that WebSocket events reflect actual database state."""
    #     if not async_auth_headers:
    #         pytest.skip("No valid auth headers available")

    #     # Clear database
    #     await db_session.execute(text("DELETE FROM earthquakes"))
    #     await db_session.commit()

    #     websocket_messages = []
    #     websocket_connected = False
    #     connection_error = None

    #     async def websocket_client():
    #         nonlocal websocket_connected, connection_error
    #         try:
    #             # Extract token from auth headers
    #             auth_header = async_auth_headers.get("Authorization", "")
    #             token = auth_header.replace("Bearer ", "") if auth_header else ""

    #             uri = f"ws://localhost:8000/ws?token={token}"
    #             async with websockets.connect(uri) as websocket:
    #                 websocket_connected = True

    #                 # Subscribe to earthquake updates
    #                 await websocket.send(json.dumps({
    #                     "type": "subscribe",
    #                     "channel": "earthquakes"
    #                 }))

    #                 # Listen for messages for 5 seconds
    #                 timeout = 5
    #                 try:
    #                     while timeout > 0:
    #                         message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
    #                         websocket_messages.append(json.loads(message))
    #                         timeout -= 1
    #                 except asyncio.TimeoutError:
    #                     pass  # Expected timeout after 5 seconds

    #         except Exception as e:
    #             connection_error = str(e)

    #     # Start WebSocket client
    #     websocket_task = asyncio.create_task(websocket_client())

    #     # Wait a moment for WebSocket to connect
    #     await asyncio.sleep(0.5)

    #     # Create earthquake via API
    #     earthquake_data = {
    #         "magnitude_value": 5.2,
    #         "magnitude_scale": "moment",
    #         "latitude": 37.7749,
    #         "longitude": -122.4194,
    #         "depth": 10.5,
    #         "occurred_at": "2024-01-01T12:00:00Z",
    #         "source": "TEST_API",
    #         "external_id": "test-ws-db-001"
    #     }

    #     response = await client_with_db.post(
    #         "/api/v1/earthquakes/",
    #         json=earthquake_data,
    #         headers=async_auth_headers
    #     )

    #     assert response.status_code == 201
    #     created_earthquake = response.json()
    #     earthquake_id = created_earthquake["id"]

    #     # Wait for WebSocket messages
    #     await asyncio.sleep(2)

    #     # Cancel WebSocket task
    #     websocket_task.cancel()
    #     try:
    #         await websocket_task
    #     except asyncio.CancelledError:
    #         pass

    #     # Verify database state
    #     result = await db_session.execute(
    #         text("SELECT id, magnitude_value, latitude, longitude FROM earthquakes WHERE id = :id"),
    #         {"id": earthquake_id}
    #     )
    #     db_earthquake = result.fetchone()

    #     assert db_earthquake is not None, "Earthquake should exist in database"
    #     assert db_earthquake.magnitude_value == 5.2
    #     assert db_earthquake.latitude == 37.7749
    #     assert db_earthquake.longitude == -122.4194

    #     # Verify WebSocket messages were received
    #     if connection_error:
    #         print(f"WebSocket connection error: {connection_error}")
    #         pytest.skip(f"WebSocket connection failed: {connection_error}")

    #     assert websocket_connected, "WebSocket should have connected successfully"
    #     assert len(websocket_messages) > 0, "Should have received WebSocket messages"

    #     # Find earthquake_detected message
    #     earthquake_detected_messages = [
    #         msg for msg in websocket_messages
    #         if msg.get("type") == "earthquake_detected"
    #     ]

    #     assert len(earthquake_detected_messages) > 0, "Should have received earthquake_detected message"

    #     # Verify message content matches database
    #     earthquake_message = earthquake_detected_messages[0]
    #     assert earthquake_message["data"]["id"] == earthquake_id
    #     assert earthquake_message["data"]["magnitude"] == 5.2
    #     assert earthquake_message["data"]["latitude"] == 37.7749
    #     assert earthquake_message["data"]["longitude"] == -122.4194

    # @pytest.mark.asyncio
    # async def test_high_magnitude_alert_websocket_database_consistency(
    #     self, client_with_db, async_auth_headers: dict, db_session
    # ):
    #     """Test high magnitude alerts with database consistency."""
    #     if not async_auth_headers:
    #         pytest.skip("No valid auth headers available")

    #     # Clear database
    #     await db_session.execute(text("DELETE FROM earthquakes"))
    #     await db_session.commit()

    #     websocket_messages = []
    #     websocket_connected = False
    #     connection_error = None

    #     async def websocket_client():
    #         nonlocal websocket_connected, connection_error
    #         try:
    #             auth_header = async_auth_headers.get("Authorization", "")
    #             token = auth_header.replace("Bearer ", "") if auth_header else ""

    #             uri = f"ws://localhost:8000/ws?token={token}"
    #             async with websockets.connect(uri) as websocket:
    #                 websocket_connected = True

    #                 # Subscribe to alerts
    #                 await websocket.send(json.dumps({
    #                     "type": "subscribe",
    #                     "channel": "alerts"
    #                 }))

    #                 # Listen for messages
    #                 timeout = 5
    #                 try:
    #                     while timeout > 0:
    #                         message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
    #                         websocket_messages.append(json.loads(message))
    #                         timeout -= 1
    #                 except asyncio.TimeoutError:
    #                     pass

    #         except Exception as e:
    #             connection_error = str(e)

    #     # Start WebSocket client
    #     websocket_task = asyncio.create_task(websocket_client())
    #     await asyncio.sleep(0.5)

    #     # Create high magnitude earthquake (magnitude 7.0 should trigger alert)
    #     earthquake_data = {
    #         "magnitude_value": 7.0,
    #         "magnitude_scale": "moment",
    #         "latitude": 35.6762,
    #         "longitude": 139.6503,  # Tokyo coordinates
    #         "depth": 15.0,
    #         "occurred_at": "2024-01-01T12:00:00Z",
    #         "source": "TEST_HIGH_MAG",
    #         "external_id": "test-high-mag-001"
    #     }

    #     response = await client_with_db.post(
    #         "/api/v1/earthquakes/",
    #         json=earthquake_data,
    #         headers=async_auth_headers
    #     )

    #     assert response.status_code == 201
    #     created_earthquake = response.json()
    #     earthquake_id = created_earthquake["id"]

    #     # Wait for WebSocket messages
    #     await asyncio.sleep(2)

    #     # Cancel WebSocket task
    #     websocket_task.cancel()
    #     try:
    #         await websocket_task
    #     except asyncio.CancelledError:
    #         pass

    #     # Verify database state
    #     result = await db_session.execute(
    #         text("SELECT id, magnitude_value FROM earthquakes WHERE id = :id"),
    #         {"id": earthquake_id}
    #     )
    #     db_earthquake = result.fetchone()

    #     assert db_earthquake is not None
    #     assert db_earthquake.magnitude_value == 7.0

    #     # Verify alert WebSocket messages
    #     if connection_error:
    #         pytest.skip(f"WebSocket connection failed: {connection_error}")

    #     assert websocket_connected, "WebSocket should have connected"

    #     # Find high magnitude alert message
    #     alert_messages = [
    #         msg for msg in websocket_messages
    #         if msg.get("type") == "high_magnitude_alert"
    #     ]

    #     if len(alert_messages) > 0:
    #         alert_message = alert_messages[0]
    #         assert alert_message["data"]["earthquake_id"] == earthquake_id
    #         assert alert_message["data"]["magnitude"] == 7.0
    #         assert alert_message["data"]["alert_level"] in ["HIGH", "CRITICAL"]

    @pytest.mark.asyncio
    async def test_database_count_consistency_after_events(
        self, client_with_db, async_auth_headers: dict, db_session
    ):
        """Test that database count matches after WebSocket events are sent."""
        if not async_auth_headers:
            pytest.skip("No valid auth headers available")

        # Clear database and get initial count
        await db_session.execute(text("DELETE FROM earthquakes"))
        await db_session.commit()

        initial_result = await db_session.execute(
            text("SELECT COUNT(*) FROM earthquakes")
        )
        initial_count = initial_result.scalar()

        assert initial_count == 0, "Database should start empty"

        # Create multiple earthquakes
        earthquake_ids = []
        for i in range(3):
            earthquake_data = {
                "magnitude_value": 2.0 + i * 0.5,
                "magnitude_scale": "moment",
                "latitude": 37.7749 + i * 0.01,
                "longitude": -122.4194 + i * 0.01,
                "depth": 10.0 + i,
                "occurred_at": "2024-01-01T12:00:00Z",
                "source": "TEST_COUNT",
                "external_id": f"test-count-{i:03d}",
            }

            response = await client_with_db.post(
                "/api/v1/earthquakes/", json=earthquake_data, headers=async_auth_headers
            )

            assert response.status_code == 201
            earthquake_ids.append(response.json()["id"])

        # Wait for all events to process
        await asyncio.sleep(1)

        # Verify database count
        final_result = await db_session.execute(
            text("SELECT COUNT(*) FROM earthquakes")
        )
        final_count = final_result.scalar()

        # Verify all earthquakes exist
        for earthquake_id in earthquake_ids:
            result = await db_session.execute(
                text("SELECT id FROM earthquakes WHERE id = :id"), {"id": earthquake_id}
            )
            assert (
                result.fetchone() is not None
            ), f"Earthquake {earthquake_id} should exist"

        assert final_count == 3, f"Expected 3 earthquakes, found {final_count}"

    # @pytest.mark.asyncio
    # async def test_websocket_receives_database_queried_data(
    #     self, client_with_db, async_auth_headers: dict, db_session
    # ):
    #     """Test that WebSocket events contain data queried from database, not just event data."""
    #     if not async_auth_headers:
    #         pytest.skip("No valid auth headers available")

    #     # This test verifies the fix for the transaction timing issue
    #     # Events should contain data from the database after commit

    #     websocket_messages = []
    #     connection_error = None

    #     async def websocket_client():
    #         nonlocal connection_error
    #         try:
    #             auth_header = async_auth_headers.get("Authorization", "")
    #             token = auth_header.replace("Bearer ", "") if auth_header else ""

    #             uri = f"ws://localhost:8000/ws?token={token}"
    #             async with websockets.connect(uri) as websocket:
    #                 await websocket.send(json.dumps({
    #                     "type": "subscribe",
    #                     "channel": "earthquakes"
    #                 }))

    #                 # Listen for exactly one message
    #                 message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
    #                 websocket_messages.append(json.loads(message))

    #         except Exception as e:
    #             connection_error = str(e)

    #     # Start WebSocket client
    #     websocket_task = asyncio.create_task(websocket_client())
    #     await asyncio.sleep(0.5)

    #     # Create earthquake
    #     earthquake_data = {
    #         "magnitude_value": 4.5,
    #         "magnitude_scale": "moment",
    #         "latitude": 40.7128,
    #         "longitude": -74.0060,  # NYC coordinates
    #         "depth": 8.0,
    #         "occurred_at": "2024-01-01T12:00:00Z",
    #         "source": "TEST_DB_QUERY",
    #         "external_id": "test-db-query-001"
    #     }

    #     response = await client_with_db.post(
    #         "/api/v1/earthquakes/",
    #         json=earthquake_data,
    #         headers=async_auth_headers
    #     )

    #     assert response.status_code == 201
    #     earthquake_id = response.json()["id"]

    #     # Wait for WebSocket message
    #     try:
    #         await asyncio.wait_for(websocket_task, timeout=5.0)
    #     except asyncio.TimeoutError:
    #         websocket_task.cancel()

    #     if connection_error:
    #         pytest.skip(f"WebSocket connection failed: {connection_error}")

    #     # Verify we received a message with database data
    #     assert len(websocket_messages) > 0, "Should have received WebSocket message"

    #     earthquake_message = None
    #     for msg in websocket_messages:
    #         if msg.get("type") == "earthquake_detected":
    #             earthquake_message = msg
    #             break

    #     assert earthquake_message is not None, "Should have received earthquake_detected message"

    #     # Verify the message contains database-consistent data
    #     message_data = earthquake_message["data"]
    #     assert message_data["id"] == earthquake_id
    #     assert message_data["magnitude"] == 4.5
    #     assert message_data["latitude"] == 40.7128
    #     assert message_data["longitude"] == -74.0060
    #     assert message_data["source"] == "TEST_DB_QUERY"

    #     # Verify this data matches what's actually in the database
    #     result = await db_session.execute(
    #         text("""
    #             SELECT id, magnitude_value, latitude, longitude, source
    #             FROM earthquakes WHERE id = :id
    #         """),
    #         {"id": earthquake_id}
    #     )
    #     db_row = result.fetchone()

    #     assert db_row is not None
    #     assert str(db_row.id) == earthquake_id
    #     assert db_row.magnitude_value == 4.5
    #     assert db_row.latitude == 40.7128
    #     assert db_row.longitude == -74.0060
    #     assert db_row.source == "TEST_DB_QUERY"
