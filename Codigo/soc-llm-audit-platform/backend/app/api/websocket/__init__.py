"""
WebSocket Router - Real-time endpoints.
"""
from fastapi import APIRouter

from app.api.websocket.hitl_queue import router as hitl_ws_router
from app.api.websocket.alerts_stream import router as alerts_ws_router
from app.api.websocket.compliance_live import router as compliance_ws_router

router = APIRouter()

router.include_router(hitl_ws_router)
router.include_router(alerts_ws_router)
router.include_router(compliance_ws_router)
