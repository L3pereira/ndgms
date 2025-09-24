import json
import logging
from typing import Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._earthquake_subscribers: set[str] = set()
        self._alert_subscribers: set[str] = set()
        # For filtering support
        self._filter_service: Optional = None

    def set_filter_service(self, filter_service) -> None:
        """Set the WebSocket filtering service."""
        self._filter_service = filter_service
        logger.info("WebSocket filtering service configured")

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self._connections[client_id] = websocket
        logger.info(f"WebSocket client {client_id} connected")

    def disconnect(self, client_id: str) -> None:
        if client_id in self._connections:
            del self._connections[client_id]
        self._earthquake_subscribers.discard(client_id)
        self._alert_subscribers.discard(client_id)
        logger.info(f"WebSocket client {client_id} disconnected")

    async def subscribe_to_earthquakes(self, client_id: str) -> None:
        if client_id in self._connections:
            self._earthquake_subscribers.add(client_id)
            await self._send_to_client(
                client_id,
                {"type": "subscription_confirmed", "subscription": "earthquakes"},
            )

    async def subscribe_to_alerts(self, client_id: str) -> None:
        if client_id in self._connections:
            self._alert_subscribers.add(client_id)
            await self._send_to_client(
                client_id, {"type": "subscription_confirmed", "subscription": "alerts"}
            )

    async def broadcast_earthquake_update(self, message: dict, earthquake=None) -> None:
        """Broadcast earthquake update with optional filtering."""
        if earthquake and self._filter_service:
            # Filter per client
            filtered_subscribers = []
            for client_id in self._earthquake_subscribers:
                if self._filter_service.should_broadcast_earthquake(
                    earthquake, client_id
                ):
                    filtered_subscribers.append(client_id)

            if filtered_subscribers:
                logger.debug(
                    f"Broadcasting earthquake {earthquake.id} to {len(filtered_subscribers)}/{len(self._earthquake_subscribers)} clients"
                )
                await self._broadcast_to_specific_clients(filtered_subscribers, message)
            else:
                logger.debug(f"Earthquake {earthquake.id} filtered out for all clients")
        else:
            # No filtering, broadcast to all
            await self._broadcast_to_subscribers(self._earthquake_subscribers, message)

    async def broadcast_alert(self, message: dict, earthquake=None) -> None:
        """Broadcast alert with optional filtering."""
        if earthquake and self._filter_service:
            # Filter per client for alerts
            filtered_subscribers = []
            for client_id in self._alert_subscribers:
                if self._filter_service.should_broadcast_alert(earthquake, client_id):
                    filtered_subscribers.append(client_id)

            if filtered_subscribers:
                logger.info(
                    f"Broadcasting alert for earthquake {earthquake.id} to {len(filtered_subscribers)}/{len(self._alert_subscribers)} clients"
                )
                await self._broadcast_to_specific_clients(filtered_subscribers, message)
            else:
                logger.debug(
                    f"Alert for earthquake {earthquake.id} filtered out for all clients"
                )
        else:
            # No filtering, broadcast to all
            await self._broadcast_to_subscribers(self._alert_subscribers, message)

    async def _broadcast_to_subscribers(
        self, subscribers: set[str], message: dict
    ) -> None:
        if not subscribers:
            return

        disconnected_clients = []
        for client_id in subscribers:
            try:
                await self._send_to_client(client_id, message)
            except Exception as e:
                logger.error(f"Failed to send message to client {client_id}: {e}")
                disconnected_clients.append(client_id)

        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def _broadcast_to_specific_clients(
        self, client_ids: list[str], message: dict
    ) -> None:
        """Broadcast to specific list of client IDs."""
        if not client_ids:
            return

        disconnected_clients = []
        for client_id in client_ids:
            try:
                await self._send_to_client(client_id, message)
            except Exception as e:
                logger.error(f"Failed to send message to client {client_id}: {e}")
                disconnected_clients.append(client_id)

        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def _send_to_client(self, client_id: str, message: dict) -> None:
        if client_id in self._connections:
            websocket = self._connections[client_id]
            message_text = json.dumps(message)

            # Check message size (1MB = 1,048,576 bytes, use conservative 100KB limit for safety)
            max_size = (
                100 * 1024
            )  # 100KB - very conservative for individual earthquake events
            message_size = len(message_text.encode("utf-8"))

            if message_size > max_size:
                logger.warning(
                    f"Message too large for client {client_id}: {message_size} bytes, type: {message.get('type', 'unknown')}"
                )
                # Log part of the message for debugging
                logger.warning(f"Message preview: {message_text[:500]}...")

                # Send error message instead
                error_message = {
                    "type": "error",
                    "message": f"Data payload too large ({message_size} bytes) - using reduced dataset",
                    "timestamp": message.get("data", {}).get("timestamp", ""),
                }
                await websocket.send_text(json.dumps(error_message))
            else:
                logger.debug(
                    f"Sending message to client {client_id}: {message_size} bytes, type: {message.get('type', 'unknown')}"
                )
                await websocket.send_text(message_text)

    async def handle_message(self, client_id: str, message: str) -> None:
        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "subscribe_earthquakes":
                await self.subscribe_to_earthquakes(client_id)
            elif action == "subscribe_alerts":
                await self.subscribe_to_alerts(client_id)
            else:
                await self._send_to_client(
                    client_id, {"type": "error", "message": f"Unknown action: {action}"}
                )
        except json.JSONDecodeError:
            await self._send_to_client(
                client_id, {"type": "error", "message": "Invalid JSON message"}
            )
        except Exception as e:
            logger.error(f"Error handling message from client {client_id}: {e}")
            await self._send_to_client(
                client_id, {"type": "error", "message": "Internal server error"}
            )
