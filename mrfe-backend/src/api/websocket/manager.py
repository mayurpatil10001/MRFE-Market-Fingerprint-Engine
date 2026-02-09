"""WebSocket connection manager."""

from __future__ import annotations

from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    """Manages websocket subscriptions by topic."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, topic: str) -> None:
        """Accept and register websocket."""
        await websocket.accept()
        self._connections[topic].add(websocket)

    def disconnect(self, websocket: WebSocket, topic: str) -> None:
        """Remove websocket from topic."""
        self._connections[topic].discard(websocket)

    async def broadcast(self, topic: str, payload: dict[str, object]) -> None:
        """Broadcast payload to all subscribers."""
        stale: list[WebSocket] = []
        for connection in self._connections[topic]:
            try:
                await connection.send_json(payload)
            except Exception:
                stale.append(connection)
        for conn in stale:
            self._connections[topic].discard(conn)
