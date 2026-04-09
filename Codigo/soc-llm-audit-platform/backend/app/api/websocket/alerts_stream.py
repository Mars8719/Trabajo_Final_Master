"""
WebSocket - Alerts stream in real-time.
/ws/alerts/stream - Stream de alertas procesadas
"""
import json
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set

logger = structlog.get_logger()
router = APIRouter()

alert_connections: Set[WebSocket] = set()


@router.websocket("/alerts/stream")
async def alerts_stream_ws(websocket: WebSocket):
    """WebSocket for real-time alert streaming."""
    await websocket.accept()
    alert_connections.add(websocket)
    logger.info("Alerts WebSocket client connected", total=len(alert_connections))

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        alert_connections.discard(websocket)
        logger.info("Alerts WebSocket client disconnected", total=len(alert_connections))


async def broadcast_alert(alert_data: dict):
    """Broadcast new alert to all connected clients."""
    disconnected = set()
    for ws in alert_connections:
        try:
            await ws.send_json(alert_data)
        except Exception:
            disconnected.add(ws)
    alert_connections.difference_update(disconnected)
