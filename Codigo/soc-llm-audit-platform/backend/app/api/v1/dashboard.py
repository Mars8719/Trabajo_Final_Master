"""
Dashboard API - Board-Level KPIs and aggregated metrics.
Enterprise Dashboard: 8 KPIs (K1-K8) + Risk Monitor data.
"""
from datetime import datetime, timedelta, UTC
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.infrastructure.database import get_db
from app.models.db.alert import Alert, HITLStatus
from app.models.db.compliance_score import ComplianceScore, RiskLevel
from app.models.db.hitl_decision import HITLDecision
from app.models.db.incident import NIS2Incident, IncidentStatus
from app.models.db.bias_test import BiasTest
from app.core.audit_module.realtime_risk_monitor import risk_monitor

router = APIRouter()


@router.get("/kpis")
async def get_dashboard_kpis(db: AsyncSession = Depends(get_db)):
    """Board-level KPIs for DPO + CISO view."""
    now = datetime.now(UTC)
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    # Total alerts
    total_alerts = await db.execute(select(func.count(Alert.id)))
    alerts_24h = await db.execute(
        select(func.count(Alert.id)).where(Alert.created_at >= last_24h)
    )

    # Compliance metrics
    avg_score = await db.execute(select(func.avg(ComplianceScore.total_score)))
    non_compliant = await db.execute(
        select(func.count(ComplianceScore.id)).where(
            ComplianceScore.risk_level == RiskLevel.NON_COMPLIANT
        )
    )

    # HITL metrics
    pending_reviews = await db.execute(
        select(func.count(Alert.id)).where(Alert.hitl_status == HITLStatus.PENDING)
    )
    total_decisions = await db.execute(select(func.count(HITLDecision.id)))

    # Incident metrics
    active_incidents = await db.execute(
        select(func.count(NIS2Incident.id)).where(
            NIS2Incident.status != IncidentStatus.CLOSED
        )
    )

    # Bias testing
    bias_tests_passed = await db.execute(
        select(func.count(BiasTest.id)).where(BiasTest.passed == True)
    )
    bias_tests_total = await db.execute(select(func.count(BiasTest.id)))

    return {
        "timestamp": now.isoformat(),
        "alerts": {
            "total": total_alerts.scalar() or 0,
            "last_24h": alerts_24h.scalar() or 0,
        },
        "compliance": {
            "average_score": round(avg_score.scalar() or 0, 2),
            "non_compliant_count": non_compliant.scalar() or 0,
        },
        "hitl": {
            "pending_reviews": pending_reviews.scalar() or 0,
            "total_decisions": total_decisions.scalar() or 0,
        },
        "incidents": {
            "active": active_incidents.scalar() or 0,
        },
        "bias": {
            "tests_passed": bias_tests_passed.scalar() or 0,
            "tests_total": bias_tests_total.scalar() or 0,
        },
        "system_status": "operational",
    }


@router.get("/kpis/enterprise")
async def get_enterprise_kpis(db: AsyncSession = Depends(get_db)):
    """Enterprise KPIs K1-K8 for CISO/DPO/Compliance Officer/SOC Manager."""
    now = datetime.now(UTC)
    last_1h = now - timedelta(hours=1)
    last_24h = now - timedelta(hours=24)
    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
    yesterday_end = yesterday_start + timedelta(days=1)
    today_start = now.replace(hour=0, minute=0, second=0)

    # K1: CENS Score Card — Score ejecutivo 0-100 con delta vs 1h
    avg_score_now = await db.execute(select(func.avg(ComplianceScore.total_score)))
    avg_score_1h = await db.execute(
        select(func.avg(ComplianceScore.total_score)).where(
            ComplianceScore.created_at <= last_1h
        )
    )
    score_now = avg_score_now.scalar() or 0
    score_1h = avg_score_1h.scalar() or score_now
    k1_delta = round(score_now - score_1h, 2)

    # K2: NIS2 SLA Countdown — Timer 24h/72h con % consumido
    active_incidents_q = await db.execute(
        select(NIS2Incident).where(NIS2Incident.status != IncidentStatus.CLOSED).limit(5)
    )
    active_incidents = active_incidents_q.scalars().all()
    nis2_sla_items = []
    for inc in active_incidents:
        elapsed = (now - inc.created_at).total_seconds()
        sla_24h_pct = min(round(elapsed / (24 * 3600) * 100, 1), 100)
        sla_72h_pct = min(round(elapsed / (72 * 3600) * 100, 1), 100)
        nis2_sla_items.append({
            "incident_id": str(inc.id),
            "sla_24h_pct": sla_24h_pct,
            "sla_72h_pct": sla_72h_pct,
            "elapsed_hours": round(elapsed / 3600, 1),
        })

    # K3: PII Events Card — Contador PII hoy + delta vs ayer
    pii_today = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.created_at >= today_start, Alert.pii_score is not None, Alert.pii_score > 0
        )
    )
    pii_yesterday = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.created_at >= yesterday_start,
            Alert.created_at < yesterday_end,
            Alert.pii_score is not None,
            Alert.pii_score > 0,
        )
    )
    pii_today_val = pii_today.scalar() or 0
    pii_yesterday_val = pii_yesterday.scalar() or 0

    # K4: Active Violations — Violaciones activas por nivel
    violations_critical = await db.execute(
        select(func.count(ComplianceScore.id)).where(
            ComplianceScore.risk_level == RiskLevel.NON_COMPLIANT
        )
    )
    violations_warning = await db.execute(
        select(func.count(ComplianceScore.id)).where(
            ComplianceScore.risk_level == RiskLevel.MEDIUM_RISK
        )
    )

    # K5: Audit Chain Integrity — checksum verification
    from app.core.audit_module.audit_logger import AuditTrailLogger
    audit_logger = AuditTrailLogger(db)
    chain_status = await audit_logger.verify_chain_integrity()

    # K6: Human Review Queue — Pendientes + urgentes
    pending = await db.execute(
        select(func.count(Alert.id)).where(Alert.hitl_status == HITLStatus.PENDING)
    )

    # K7: DoW Budget Card — from risk monitor
    risk_metrics = risk_monitor.metrics_snapshot
    dow_data = risk_metrics["checks"]["dow_budget"]

    # K8: AI Act Risk Level
    bias_tests_q = await db.execute(
        select(BiasTest).order_by(BiasTest.created_at.desc()).limit(10)
    )
    bias_tests = bias_tests_q.scalars().all()
    failed_bias = sum(1 for t in bias_tests if not t.passed) if bias_tests else 0
    ai_act_level = (
        "HIGH" if failed_bias > 3 else "LIMITED" if failed_bias > 0 else "MINIMAL"
    )

    return {
        "timestamp": now.isoformat(),
        "k1_cens_score": {
            "score": round(score_now, 2),
            "delta_1h": k1_delta,
            "status": "GREEN" if score_now >= 85 else "AMBER" if score_now >= 60 else "RED" if score_now >= 40 else "BLACK",
        },
        "k2_nis2_sla": {
            "active_incidents": len(nis2_sla_items),
            "items": nis2_sla_items,
        },
        "k3_pii_events": {
            "today": pii_today_val,
            "yesterday": pii_yesterday_val,
            "delta": pii_today_val - pii_yesterday_val,
        },
        "k4_active_violations": {
            "critical": violations_critical.scalar() or 0,
            "warning": violations_warning.scalar() or 0,
            "total": (violations_critical.scalar() or 0) + (violations_warning.scalar() or 0),
        },
        "k5_audit_integrity": chain_status,
        "k6_human_review": {
            "pending": pending.scalar() or 0,
        },
        "k7_dow_budget": dow_data,
        "k8_ai_act_risk": {
            "level": ai_act_level,
            "failed_bias_tests": failed_bias,
            "deadline": "2026-08-02T00:00:00Z",
        },
    }


@router.get("/risk-monitor")
async def get_risk_monitor_status():
    """Real-time risk monitor status and active alerts."""
    return {
        "metrics": risk_monitor.metrics_snapshot,
        "active_alerts": risk_monitor.active_alerts,
        "total_alerts": len(risk_monitor.all_alerts),
    }


@router.get("/risk-monitor/alerts")
async def get_risk_alerts():
    """All regulatory risk alerts (active + resolved)."""
    return {
        "alerts": risk_monitor.all_alerts,
        "total": len(risk_monitor.all_alerts),
    }
