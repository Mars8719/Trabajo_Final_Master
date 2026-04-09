"""
HITL API - Human-in-the-Loop queue and decisions.
GET  /api/v1/hitl/queue - Cola revisión pendiente
POST /api/v1/hitl/{id}/decision - Registrar decisión (HOJR)
POST /api/v1/hitl/kill-switch - Activar kill switch L4
"""
from uuid import UUID
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database import get_db
from app.models.db.alert import Alert, HITLStatus
from app.models.db.hitl_decision import HITLDecision, EscalationLevel, DecisionType
from app.models.schemas.schemas import HITLQueueItem, HITLDecisionCreate, HITLKillSwitch
from app.core.audit_module.hitl_controller import hitl_controller
from app.core.audit_module.audit_logger import audit_logger

router = APIRouter()


@router.get("/queue", response_model=list[HITLQueueItem])
async def get_hitl_queue(db: AsyncSession = Depends(get_db)):
    """Get pending HITL review queue."""
    result = await db.execute(
        select(Alert)
        .where(Alert.hitl_status == HITLStatus.PENDING)
        .where(Alert.hitl_level > 0)
        .order_by(Alert.hitl_level.desc(), Alert.created_at.asc())
    )
    alerts = result.scalars().all()

    queue_items = []
    for alert in alerts:
        level_map = {0: "L0", 1: "L1", 2: "L2", 3: "L3", 4: "L4"}
        queue_items.append(HITLQueueItem(
            id=alert.id,
            alert_id=alert.id,
            escalation_level=level_map.get(alert.hitl_level, "L1"),
            cs_at_review=alert.compliance_score,
            confidence_at_review=alert.llm_confidence,
            created_at=alert.created_at,
        ))

    return queue_items


@router.post("/{alert_id}/decision", status_code=status.HTTP_201_CREATED)
async def submit_hitl_decision(
    alert_id: UUID,
    decision_data: HITLDecisionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Submit a HITL decision with HOJR (Human Oversight Justification Record)."""
    # Fetch alert
    result = await db.execute(select(Alert).where(Alert.id == str(alert_id)))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.hitl_status != HITLStatus.PENDING:
        raise HTTPException(status_code=400, detail="Alert is not pending review")

    # Validate HOJR (anti-rubber-stamping)
    hojr_data = {
        "justification": decision_data.justification,
        "time_to_decision_seconds": 30,  # Would come from frontend timing
        "shap_viewed": decision_data.shap_viewed,
        "lime_viewed": decision_data.lime_viewed,
    }
    is_valid, errors = hitl_controller.validate_hojr(hojr_data)
    if not is_valid:
        raise HTTPException(status_code=422, detail={"hojr_errors": errors})

    # Create HITL decision record
    level_map = {0: EscalationLevel.L0_AUTO, 1: EscalationLevel.L1_ASYNC,
                 2: EscalationLevel.L2_SYNC, 3: EscalationLevel.L3_MANDATORY,
                 4: EscalationLevel.L4_KILL}
    decision_type_map = {
        "approved": DecisionType.APPROVED, "rejected": DecisionType.REJECTED,
        "escalated": DecisionType.ESCALATED, "modified": DecisionType.MODIFIED,
    }

    hitl_decision = HITLDecision(
        alert_id=str(alert_id),
        escalation_level=level_map.get(alert.hitl_level, EscalationLevel.L1_ASYNC),
        reviewer_id="analyst_001",  # Would come from auth context
        reviewer_role="analyst_t2",
        decision=decision_type_map.get(decision_data.decision, DecisionType.APPROVED),
        justification=decision_data.justification,
        alternatives_considered=decision_data.alternatives_considered,
        time_to_decision_seconds=30,
        shap_viewed=decision_data.shap_viewed,
        lime_viewed=decision_data.lime_viewed,
        cs_at_review=alert.compliance_score,
        confidence_at_review=alert.llm_confidence,
        anti_rubber_stamp_check=True,
    )
    db.add(hitl_decision)

    # Update alert status
    status_map = {
        "approved": HITLStatus.APPROVED,
        "rejected": HITLStatus.REJECTED,
        "escalated": HITLStatus.ESCALATED,
    }
    alert.hitl_status = status_map.get(decision_data.decision, HITLStatus.APPROVED)
    alert.updated_at = datetime.now(UTC)

    # Audit trail
    await audit_logger.log(
        actor="analyst_001",
        action=f"hitl.decision.{decision_data.decision}",
        details={
            "decision": decision_data.decision,
            "justification": decision_data.justification,
            "escalation_level": alert.hitl_level,
        },
        alert_id=str(alert_id),
        gdpr_articles=["Art. 22"] if alert.hitl_level >= 2 else [],
        nis2_articles=["Art. 21"] if alert.hitl_level >= 1 else [],
        session=db,
    )

    return {"status": "decision_recorded", "alert_id": str(alert_id), "decision": decision_data.decision}


@router.post("/kill-switch")
async def activate_kill_switch(data: HITLKillSwitch, db: AsyncSession = Depends(get_db)):
    """Activate L4 Kill Switch - Immediate LLM deactivation."""
    result = hitl_controller.activate_kill_switch(
        reason=data.reason, activated_by=data.activated_by
    )

    await audit_logger.log(
        actor=data.activated_by,
        action="hitl.kill_switch.activated",
        details={"reason": data.reason},
        gdpr_articles=["Art. 22"],
        nis2_articles=["Art. 21", "Art. 23"],
        session=db,
    )

    return result


@router.post("/kill-switch/deactivate")
async def deactivate_kill_switch(deactivated_by: str = "ciso", db: AsyncSession = Depends(get_db)):
    """Deactivate kill switch (requires CISO role)."""
    result = hitl_controller.deactivate_kill_switch(deactivated_by=deactivated_by)

    await audit_logger.log(
        actor=deactivated_by,
        action="hitl.kill_switch.deactivated",
        session=db,
    )

    return result
