"""
Compliance Service - Orchestrates compliance scoring and reporting.
"""
import structlog
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.infrastructure.database import async_session
from app.models.db.compliance_score import ComplianceScore, RiskLevel
from app.core.audit_module.compliance_engine import compliance_engine

logger = structlog.get_logger()


class ComplianceService:
    """Orchestrates compliance operations across the platform."""

    async def get_compliance_summary(self) -> dict:
        """Get a summary of overall compliance status."""
        async with async_session() as session:
            avg = await session.execute(select(func.avg(ComplianceScore.total_score)))
            total = await session.execute(select(func.count(ComplianceScore.id)))

            non_compliant = await session.execute(
                select(func.count(ComplianceScore.id)).where(
                    ComplianceScore.risk_level == RiskLevel.NON_COMPLIANT
                )
            )

            return {
                "average_score": round(avg.scalar() or 0, 2),
                "total_assessments": total.scalar() or 0,
                "non_compliant_count": non_compliant.scalar() or 0,
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def recalculate_score(self, alert_id: UUID, overrides: dict) -> dict:
        """Recalculate compliance score with manual overrides."""
        result = compliance_engine.calculate_score(**overrides)
        return {
            "alert_id": str(alert_id),
            "new_score": result.total_score,
            "risk_level": result.risk_level,
            "action_required": result.action_required,
        }


compliance_service = ComplianceService()
