"""
HITL Service - Human-in-the-Loop orchestration.
"""
import structlog
from datetime import datetime, UTC
from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database import async_session
from app.models.db.alert import Alert, HITLStatus
from app.models.db.hitl_decision import HITLDecision
from app.core.audit_module.hitl_controller import hitl_controller
from app.api.websocket.hitl_queue import broadcast_hitl_update

logger = structlog.get_logger()


class HITLService:
    """Orchestrates HITL operations."""

    async def get_queue_stats(self) -> dict:
        """Get HITL queue statistics."""
        async with async_session() as session:
            from sqlalchemy import func

            pending = await session.execute(
                select(func.count(Alert.id)).where(Alert.hitl_status == HITLStatus.PENDING)
            )

            by_level = {}
            for level in range(5):
                count = await session.execute(
                    select(func.count(Alert.id)).where(
                        Alert.hitl_status == HITLStatus.PENDING,
                        Alert.hitl_level == level,
                    )
                )
                by_level[f"L{level}"] = count.scalar() or 0

            return {
                "total_pending": pending.scalar() or 0,
                "by_level": by_level,
                "kill_switch_active": hitl_controller.kill_switch_active,
            }

    async def escalate(self, alert_id: UUID, new_level: int, reason: str):
        """Escalate an alert to a higher HITL level."""
        async with async_session() as session:
            result = await session.execute(select(Alert).where(Alert.id == alert_id))
            alert = result.scalar_one_or_none()
            if alert:
                alert.hitl_level = new_level
                alert.updated_at = datetime.now(UTC)
                await session.commit()

                await broadcast_hitl_update({
                    "type": "escalation",
                    "alert_id": str(alert_id),
                    "new_level": f"L{new_level}",
                    "reason": reason,
                })


hitl_service = HITLService()
