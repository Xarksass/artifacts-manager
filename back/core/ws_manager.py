# core/ws_manager.py
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket

from core.logger import get_logger

logger = get_logger(__name__, "ws")

class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info(f"Client connecté ({len(self._connections)} actifs)")

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.info(f"Client déconnecté ({len(self._connections)} actifs)")

    async def broadcast(self, message: dict[str, Any]) -> None:
        if not self._connections:
            return
        async with self._lock:
            connections = list(self._connections)

        dead: list[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)  # client déconnecté sans passage propre par disconnect()

        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)

manager = ConnectionManager()