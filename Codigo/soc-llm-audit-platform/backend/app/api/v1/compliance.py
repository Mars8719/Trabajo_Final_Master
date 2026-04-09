"""
Compliance API - Scores, dashboard KPIs, and trends.
GET /api/v1/compliance/scores - Listado CS con filtros
GET /api/v1/compliance/dashboard - KPIs agregados
GET /api/v1/compliance/trends - Tendencias temporales
"""
from typing import Optional
from datetime import datetime, timedelta, UTC
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.infrastructure.database import get_db
from app.models.db.compliance_score import ComplianceScore, RiskLevel
from app.models.schemas.schemas import ComplianceScoreResponse, ComplianceDashboard, ComplianceTrend

router = APIRouter()


@router.get("/scores", response_model=list[ComplianceScoreResponse])
async def get_compliance_scores(
    risk_level: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List compliance scores with filters."""
    query = select(ComplianceScore)

    if risk_level:
        query = query.where(ComplianceScore.risk_level == risk_level)
    if min_score is not None:
        query = query.where(ComplianceScore.total_score >= min_score)
    if max_score is not None:
        query = query.where(ComplianceScore.total_score <= max_score)

    query = query.order_by(ComplianceScore.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/dashboard", response_model=ComplianceDashboard)
async def get_compliance_dashboard(db: AsyncSession = Depends(get_db)):
    """Get aggregated compliance KPIs for DPO/CISO dashboard."""
    # Average score
    avg_result = await db.execute(select(func.avg(ComplianceScore.total_score)))
    avg_score = avg_result.scalar() or 0.0

    # Total alerts
    total_result = await db.execute(select(func.count(ComplianceScore.id)))
    total = total_result.scalar() or 0

    # Counts by risk level
    counts = {}
    for level in RiskLevel:
        count_result = await db.execute(
            select(func.count(ComplianceScore.id)).where(ComplianceScore.risk_level == level)
        )
        counts[level.value] = count_result.scalar() or 0

    # 7-day trend
    trend_7d = []
    for i in range(6, -1, -1):
        day = datetime.now(UTC) - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_avg = await db.execute(
            select(func.avg(ComplianceScore.total_score)).where(
                ComplianceScore.created_at.between(day_start, day_end)
            )
        )
        trend_7d.append(round(day_avg.scalar() or 0.0, 2))

    # Top violations
    low_scores = await db.execute(
        select(ComplianceScore)
        .where(ComplianceScore.total_score < 70)
        .order_by(ComplianceScore.total_score.asc())
        .limit(10)
    )
    violations = low_scores.scalars().all()
    top_violations = [
        {"alert_id": str(v.alert_id), "score": v.total_score, "risk_level": v.risk_level.value}
        for v in violations
    ]

    return ComplianceDashboard(
        average_score=round(avg_score, 2),
        total_alerts=total,
        compliant_count=counts.get("compliant", 0),
        attention_count=counts.get("attention", 0),
        medium_risk_count=counts.get("medium_risk", 0),
        non_compliant_count=counts.get("non_compliant", 0),
        trend_7d=trend_7d,
        top_violations=top_violations,
    )


@router.get("/trends", response_model=list[ComplianceTrend])
async def get_compliance_trends(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get compliance score trends over time."""
    trends = []
    for i in range(days - 1, -1, -1):
        day = datetime.now(UTC) - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        result = await db.execute(
            select(
                func.avg(ComplianceScore.total_score),
                func.count(ComplianceScore.id),
            ).where(ComplianceScore.created_at.between(day_start, day_end))
        )
        row = result.one()
        trends.append(ComplianceTrend(
            date=day_start.strftime("%Y-%m-%d"),
            average_score=round(row[0] or 0.0, 2),
            count=row[1] or 0,
        ))

    return trends
