"""
Dashboard KPIs - Board-level compliance and operational metrics.
DPO + CISO view.
"""
import structlog
from datetime import datetime, timedelta, UTC
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import async_session
from app.models.db.alert import Alert
from app.models.db.compliance_score import ComplianceScore, RiskLevel
from app.models.db.incident import NIS2Incident

logger = structlog.get_logger()


class DashboardKPIs:
    """Generates board-level KPIs for DPO and CISO dashboards."""

    async def get_compliance_kpis(self) -> dict:
        """Get compliance-focused KPIs."""
        async with async_session() as session:
            avg = await session.execute(select(func.avg(ComplianceScore.total_score)))
            total = await session.execute(select(func.count(ComplianceScore.id)))

            return {
                "average_compliance_score": round(avg.scalar() or 0, 2),
                "total_assessments": total.scalar() or 0,
                "frameworks": ["GDPR", "NIS2", "EU AI Act", "DORA", "ISO 42001"],
                "generated_at": datetime.now(UTC).isoformat(),
            }

    async def get_operational_kpis(self) -> dict:
        """Get operational KPIs."""
        async with async_session() as session:
            now = datetime.now(UTC)
            last_24h = now - timedelta(hours=24)

            alerts_24h = await session.execute(
                select(func.count(Alert.id)).where(Alert.created_at >= last_24h)
            )
            avg_processing = await session.execute(
                select(func.avg(Alert.processing_time_ms)).where(Alert.created_at >= last_24h)
            )

            return {
                "alerts_last_24h": alerts_24h.scalar() or 0,
                "avg_processing_time_ms": round(avg_processing.scalar() or 0, 2),
                "sla_target_ms": 5000,
                "generated_at": now.isoformat(),
            }


dashboard_kpis = DashboardKPIs()
