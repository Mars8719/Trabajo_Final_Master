"""
WebSocket - Compliance score live updates.
/ws/compliance/live - CS updates en tiempo real
"""
import json
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set

logger = structlog.get_logger()
router = APIRouter()

compliance_connections: Set[WebSocket] = set()


@router.websocket("/compliance/live")
async def compliance_live_ws(websocket: WebSocket):
    """WebSocket for real-time compliance score updates."""
    await websocket.accept()
    compliance_connections.add(websocket)
    logger.info("Compliance WebSocket client connected", total=len(compliance_connections))

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        compliance_connections.discard(websocket)
        logger.info("Compliance WebSocket client disconnected", total=len(compliance_connections))


async def broadcast_compliance_update(update: dict):
    """Broadcast compliance score update to all connected clients."""
    disconnected = set()
    for ws in compliance_connections:
        try:
            await ws.send_json(update)
        except Exception:
            disconnected.add(ws)
    compliance_connections.difference_update(disconnected)
