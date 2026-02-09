"""WebSocket routes."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.websocket.manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/{topic}")
async def stream_topic(websocket: WebSocket, topic: str) -> None:
    """Subscribe websocket client to a topic."""
    await manager.connect(websocket, topic)
    try:
        while True:
            message = await websocket.receive_text()
            await manager.broadcast(topic, {"topic": topic, "message": message})
    except WebSocketDisconnect:
        manager.disconnect(websocket, topic)


@router.websocket("/ws/realtime")
async def stream_realtime(websocket: WebSocket) -> None:
    """Compatibility websocket endpoint for realtime event streams."""
    topic = "realtime"
    await manager.connect(websocket, topic)
    try:
        while True:
            message = await websocket.receive_text()
            await manager.broadcast(topic, {"topic": topic, "message": message})
    except WebSocketDisconnect:
        manager.disconnect(websocket, topic)
