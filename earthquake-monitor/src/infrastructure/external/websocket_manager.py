import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}
        self._earthquake_subscribers: set[str] = set()
        self._alert_subscribers: set[str] = set()

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

    async def broadcast_earthquake_update(self, message: dict) -> None:
        await self._broadcast_to_subscribers(self._earthquake_subscribers, message)

    async def broadcast_alert(self, message: dict) -> None:
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

    async def _send_to_client(self, client_id: str, message: dict) -> None:
        if client_id in self._connections:
            websocket = self._connections[client_id]
            await websocket.send_text(json.dumps(message))

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
