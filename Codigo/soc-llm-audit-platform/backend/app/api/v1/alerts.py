"""
Alerts API - Ingestión y consulta de alertas SOC.
POST /api/v1/alerts/ingest - Ingestión de alertas
GET  /api/v1/alerts/{id} - Detalle de alerta
GET  /api/v1/alerts/{id}/explanation - SHAP explanation
"""
from uuid import UUID
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database import get_db
from app.models.db.alert import Alert, HITLStatus
from app.models.db.compliance_score import ComplianceScore, RiskLevel
from app.models.schemas.schemas import AlertIngest, AlertResponse, AlertDetail
from app.core.pii_scanner.scanner import pii_scanner
from app.core.llm_engine.triage import alert_triage
from app.core.llm_engine.sanitizer import input_sanitizer
from app.core.audit_module.compliance_engine import compliance_engine
from app.core.audit_module.hitl_controller import hitl_controller
from app.core.audit_module.output_validator import output_validator
from app.core.audit_module.audit_logger import audit_logger
from app.core.audit_module.explainability import explainability_module

router = APIRouter()


@router.post("/ingest", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def ingest_alert(alert_data: AlertIngest, db: AsyncSession = Depends(get_db)):
    """Ingest a new alert into the SOC-LLM pipeline."""
    start_time = datetime.now(UTC)

    # Step 1: Input Sanitization (OWASP LLM01)
    import json
    raw_text = json.dumps(alert_data.raw_payload, ensure_ascii=False, default=str)
    sanitization = input_sanitizer.sanitize(raw_text)

    is_prompt_injection = not sanitization.is_safe

    # Step 2: PII Scanning (GDPR Art. 5, 25, 32)
    anonymized_payload, pii_result = pii_scanner.scan_payload(
        alert_data.raw_payload, language="es"
    )

    # Step 3: LLM Triage (if input is safe)
    llm_classification = None
    llm_confidence = 0.0
    llm_reasoning = None

    if sanitization.is_safe:
        try:
            triage_result = await alert_triage.triage(
                anonymized_payload, geo_origin=alert_data.geo_origin
            )
            llm_classification = triage_result.classification
            llm_confidence = triage_result.confidence
            llm_reasoning = triage_result.reasoning

            # Output Validation
            validation = output_validator.validate(triage_result.reasoning)
            if validation.blocked:
                llm_reasoning = validation.sanitized_output
        except Exception:
            llm_classification = "error"
            llm_confidence = 0.0

    # Step 4: Compliance Scoring
    pii_removed_pct = 100.0 - pii_result.pii_score if pii_result.pii_score else 100.0
    cs_result = compliance_engine.calculate_score(
        pii_removed_pct=pii_removed_pct,
        legal_basis_documented=True,
        transparency_score=80.0,
        security_score=85.0,
        bias_score=90.0,
        retention_score=80.0,
        incident_latency_score=90.0,
        hitl_active=True,
    )

    # Step 5: HITL Assessment
    hitl_assessment = hitl_controller.assess(
        compliance_score=cs_result.total_score,
        confidence=llm_confidence,
        has_pii=pii_result.entities_count > 0,
        is_prompt_injection=is_prompt_injection,
    )

    hitl_status_map = {
        "L0": HITLStatus.AUTO_PROCESSED,
        "L1": HITLStatus.PENDING,
        "L2": HITLStatus.PENDING,
        "L3": HITLStatus.PENDING,
        "L4": HITLStatus.PENDING,
    }

    processing_time = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

    # Step 6: Persist Alert
    alert = Alert(
        source=alert_data.source,
        raw_payload=alert_data.raw_payload,
        anonymized_payload=anonymized_payload,
        severity_original=alert_data.severity_original,
        severity_score=65.0,
        pii_score=pii_result.pii_score,
        compliance_score=cs_result.total_score,
        llm_classification=llm_classification,
        llm_confidence=llm_confidence,
        llm_reasoning=llm_reasoning,
        hitl_level=int(hitl_assessment.escalation.level[1]),
        hitl_status=hitl_status_map.get(hitl_assessment.escalation.level, HITLStatus.PENDING),
        geo_origin=alert_data.geo_origin,
        processing_time_ms=processing_time,
        processed_at=datetime.now(UTC),
    )
    db.add(alert)
    await db.flush()

    # Step 7: Persist Compliance Score
    risk_level_map = {
        "compliant": RiskLevel.COMPLIANT,
        "attention": RiskLevel.ATTENTION,
        "medium_risk": RiskLevel.MEDIUM_RISK,
        "non_compliant": RiskLevel.NON_COMPLIANT,
    }
    cs_record = ComplianceScore(
        alert_id=alert.id,
        total_score=cs_result.total_score,
        data_minimization=pii_removed_pct,
        legal_basis=100.0,
        transparency=80.0,
        pipeline_security=85.0,
        bias_fairness=90.0,
        retention_compliance=80.0,
        incident_reporting=90.0,
        hitl_compliance=100.0,
        risk_level=risk_level_map.get(cs_result.risk_level, RiskLevel.ATTENTION),
    )
    db.add(cs_record)

    # Step 8: Audit Trail
    await audit_logger.log(
        actor="system",
        action="alert.ingested",
        details={
            "source": alert_data.source,
            "pii_entities": pii_result.entities_count,
            "compliance_score": cs_result.total_score,
            "hitl_level": hitl_assessment.escalation.level,
            "prompt_injection": is_prompt_injection,
        },
        alert_id=alert.id,
        gdpr_articles=cs_result.gdpr_articles,
        nis2_articles=cs_result.nis2_articles,
        session=db,
    )

    await db.flush()

    return alert


@router.get("/{alert_id}", response_model=AlertDetail)
async def get_alert(alert_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get alert details by ID."""
    result = await db.execute(select(Alert).where(Alert.id == str(alert_id)))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.get("/{alert_id}/explanation")
async def get_alert_explanation(alert_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get SHAP/LIME explanation for an alert's compliance score."""
    result = await db.execute(
        select(ComplianceScore).where(ComplianceScore.alert_id == str(alert_id))
    )
    cs = result.scalar_one_or_none()
    if not cs:
        raise HTTPException(status_code=404, detail="Compliance score not found")

    feature_values = {
        "data_minimization": cs.data_minimization,
        "legal_basis": cs.legal_basis,
        "transparency": cs.transparency,
        "pipeline_security": cs.pipeline_security,
        "bias_fairness": cs.bias_fairness,
        "retention_compliance": cs.retention_compliance,
        "incident_reporting": cs.incident_reporting,
        "hitl_compliance": cs.hitl_compliance,
    }

    explanation = explainability_module.explain_compliance_score(
        feature_values=feature_values,
        total_score=cs.total_score,
        alert_id=str(alert_id),
    )

    return {
        "alert_id": str(alert_id),
        "method": explanation.method,
        "narrative": explanation.narrative,
        "feature_importance": explanation.feature_importance,
        "shap_values": explanation.shap_values,
        "lime_explanation": explanation.lime_explanation,
        "confidence": explanation.confidence,
    }
