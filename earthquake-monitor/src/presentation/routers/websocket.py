import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.infrastructure.external.websocket_manager import WebSocketManager

router = APIRouter()

websocket_manager = WebSocketManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(uuid.uuid4())
    await websocket_manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.handle_message(client_id, data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)


def get_websocket_manager() -> WebSocketManager:
    return websocket_manager
