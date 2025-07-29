"""
WebSocket endpoint for real-time dashboard/KPI/status push updates.
Supports FastAPI WebSocket interface and is documented as part of the OpenAPI schema.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List
from src.api.deps import get_db

router = APIRouter()

class ConnectionManager:
    """
    Manage active WebSocket connections for realtime dashboard updates.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    # PUBLIC_INTERFACE
    async def connect(self, websocket: WebSocket):
        """Add new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    # PUBLIC_INTERFACE
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    # PUBLIC_INTERFACE
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a particular WebSocket."""
        await websocket.send_json(message)

    # PUBLIC_INTERFACE
    async def broadcast(self, message: dict):
        """Broadcast a message to all active WebSocket connections."""
        inactive = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                inactive.append(connection)
        for ws in inactive:
            self.disconnect(ws)

manager = ConnectionManager()

# PUBLIC_INTERFACE
@router.websocket(
    "/ws/dashboard/updates",
)
async def websocket_dashboard_updates(
    websocket: WebSocket,
    db=Depends(get_db),
):
    """
    WebSocket endpoint for clients to receive real-time dashboard/KPI/status updates.

    Usage:
      - Connect via WebSocket to /ws/dashboard/updates
      - Receive JSON messages for push updates related to dashboards/KPIs/status changes
      - Sent messages comply with: {"event": "...", "data": ...}

    Security:
      - WebSocket authentication can be extended by requiring token in query params or headers.

    Docs:
      - See OpenAPI for usage information. Use this for live dashboard visualizations.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Wait for a ping/check-in from client (optional, frontend can send a "subscribe" message)
            data = await websocket.receive_json()
            # Logic for subscribing to specific dashboard IDs/filters may be extended here
            if data.get("event") == "subscribe" and data.get("dashboard_id"):
                # Optionally store subscription filters (stub; logic can be implemented as needed)
                await manager.send_personal_message(
                    {"event": "subscription_ack", "dashboard_id": data.get("dashboard_id")}, websocket
                )
            # Optionally handle "ping" or other events
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# PUBLIC_INTERFACE
async def push_dashboard_update(event: str, data: dict):
    """
    Broadcast a real-time event to all connected dashboard clients.
    """
    await manager.broadcast({"event": event, "data": data})

