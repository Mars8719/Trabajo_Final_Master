"""
WebSocket - HITL Queue real-time notifications.
/ws/hitl/queue - Notificaciones HITL en tiempo real
"""
import json
import asyncio
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set

logger = structlog.get_logger()
router = APIRouter()

# Connected HITL clients
hitl_connections: Set[WebSocket] = set()


@router.websocket("/hitl/queue")
async def hitl_queue_ws(websocket: WebSocket):
    """WebSocket for real-time HITL queue notifications."""
    await websocket.accept()
    hitl_connections.add(websocket)
    logger.info("HITL WebSocket client connected", total=len(hitl_connections))

    try:
        while True:
            data = await websocket.receive_text()
            # Handle client messages (e.g., acknowledge receipt)
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        hitl_connections.discard(websocket)
        logger.info("HITL WebSocket client disconnected", total=len(hitl_connections))


async def broadcast_hitl_update(update: dict):
    """Broadcast HITL update to all connected clients."""
    disconnected = set()
    for ws in hitl_connections:
        try:
            await ws.send_json(update)
        except Exception:
            disconnected.add(ws)
    hitl_connections.difference_update(disconnected)
