"""
WebSocket endpoints for real-time dashboard streaming.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

router = APIRouter()

active_connections: List[WebSocket] = []

# PUBLIC_INTERFACE
@router.websocket("/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """
    Real-time dashboard update WebSocket endpoint.
    - Send dashboard_id in first message (after accept)
    - Server streams updates as JSON objects.
    - Standard OpenAPI docs will include notes for frontend usage.
    """
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Parse client messages for subscription config, etc.
            response = {"event": "dashboard_update", "payload": {"message": f"Echo: {data}"}}
            await websocket.send_text(json.dumps(response))
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# Add usage note for docs
@router.get("/docs", tags=["realtime"])
def websocket_docs():
    return {
        "websocket_endpoint": "/ws/dashboard",
        "usage": "Connect via WebSocket and send dashboard_id. Listen to dashboard_update events."
    }
