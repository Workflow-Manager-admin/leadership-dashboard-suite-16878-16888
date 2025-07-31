from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set, Any
import asyncio

# --- Real-time Data Streaming via WebSocket ---

router = APIRouter()

class ConnectionManager:
    """Manages active websocket clients, enables broadcasting."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.lock = asyncio.Lock()

    # PUBLIC_INTERFACE
    async def connect(self, websocket: WebSocket):
        """Accepts and adds a new websocket connection."""
        await websocket.accept()
        async with self.lock:
            self.active_connections.add(websocket)

    # PUBLIC_INTERFACE
    async def disconnect(self, websocket: WebSocket):
        """Removes a websocket connection on disconnect."""
        async with self.lock:
            self.active_connections.discard(websocket)

    # PUBLIC_INTERFACE
    async def send_personal_message(self, message: Any, websocket: WebSocket):
        """Send a message to a specific websocket client."""
        await websocket.send_json(message)

    # PUBLIC_INTERFACE
    async def broadcast(self, message: Any):
        """Send a message to all connected websocket clients."""
        async with self.lock:
            for conn in list(self.active_connections):
                try:
                    await conn.send_json(message)
                except Exception:
                    # Mark connection for removal if failed
                    self.active_connections.discard(conn)

manager = ConnectionManager()

# PUBLIC_INTERFACE
@router.websocket(
    "/ws/dashboards",
    name="dashboard_updates_ws",
)
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard/data updates.

    **Usage**:
    - Clients connect to ws://<backend>/ws/dashboards
    - On connection, they receive push notifications when dashboard data changes.
    - Messages are sent as JSON ({ event: ..., payload: ... }) when dashboards, KPIs, or other relevant data changes.
    - One-way push only (client -> server messages ignored except for heartbeat/ping support).
    """
    await manager.connect(websocket)
    try:
        while True:
            # Optionally handle pings/messages (here: simply await)
            data = await websocket.receive_text()
            # Only 'ping' or 'heartbeat' messages are recognized
            if data == "ping":
                await websocket.send_text("pong")
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)

# Convenience function for other routes/services to broadcast data changes.
# PUBLIC_INTERFACE
async def broadcast_dashboard_event(event_type: str, payload: dict = None):
    """
    Broadcast a structured event to all dashboard websocket clients.

    Args:
        event_type (str): Short event type identifier (e.g. 'dashboard_update', 'kpi_update').
        payload (dict, optional): Additional event payload.
    """
    msg = {"event": event_type}
    if payload is not None:
        msg["payload"] = payload
    await manager.broadcast(msg)
