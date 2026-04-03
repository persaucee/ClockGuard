import asyncio
from collections import defaultdict
from uuid import UUID
from fastapi import WebSocket

class OrgWebSocketManager:
    def __init__(self):
        # Maps organization_id (UUID) -> set of active WebSocket connections
        self._connections: dict[UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, organization_id: UUID):
        await websocket.accept()
        async with self._lock:
            self._connections[organization_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, organization_id: UUID):
        async with self._lock:
            self._connections[organization_id].discard(websocket)
            if not self._connections[organization_id]:
                del self._connections[organization_id]

    async def broadcast_to_org(self, organization_id: UUID, payload: dict):
        """Send payload to all admin sockets listening on this org."""
        async with self._lock:
            sockets = set(self._connections.get(organization_id, set()))

        if not sockets:
            return

        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)

        # Clean up any broken connections found during broadcast
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections[organization_id].discard(ws)


# Singleton — import this everywhere you need it
org_ws_manager = OrgWebSocketManager()