"""
Alert Pipeline Service - Orchestrates the full alert processing pipeline.
Capa 0 (Ingestión) → Capa 1 (Pre-procesamiento) → Capa 2 (LLM) → Capa 3 (Auditoría)
"""
import structlog
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID

from app.core.pii_scanner.scanner import pii_scanner
from app.core.llm_engine.sanitizer import input_sanitizer
from app.core.llm_engine.triage import alert_triage
from app.core.llm_engine.playbook import playbook_recommender
from app.core.llm_engine.summarizer import threat_summarizer
from app.core.audit_module.compliance_engine import compliance_engine
from app.core.audit_module.gdpr_engine import gdpr_engine
from app.core.audit_module.nis2_engine import nis2_engine
from app.core.audit_module.ethical_gate import EthicalGate, ComplianceViolationError
from app.core.audit_module.hitl_controller import hitl_controller
from app.core.audit_module.output_validator import output_validator
from app.core.audit_module.audit_logger import audit_logger
from app.core.audit_module.explainability import explainability_module
from app.infrastructure.kafka_client import kafka_producer
from app.api.websocket.alerts_stream import broadcast_alert
from app.api.websocket.compliance_live import broadcast_compliance_update
from app.api.websocket.hitl_queue import broadcast_hitl_update

logger = structlog.get_logger()


class AlertPipelineService:
    """Full alert processing pipeline orchestrator."""

    def __init__(self):
        self.ethical_gate = EthicalGate()

    async def process_alert(self, raw_payload: dict, source: str, geo_origin: Optional[str] = None) -> dict:
        """Process an alert through the full 4-layer pipeline."""
        pipeline_start = datetime.now(UTC)
        import json

        # ─── Capa 1: Pre-procesamiento ───
        # 1.1 Input Sanitization
        raw_text = json.dumps(raw_payload, ensure_ascii=False, default=str)
        sanitization = input_sanitizer.sanitize(raw_text)

        if not sanitization.is_safe:
            await kafka_producer.produce(
                topic="compliance.blocked.alerts",
                value={"source": source, "reason": "prompt_injection", "threats": sanitization.threats_detected},
            )
            await audit_logger.log(
                actor="system", action="alert.blocked.prompt_injection",
                details={"threats": sanitization.threats_detected, "risk_score": sanitization.risk_score},
            )
            return {"status": "blocked", "reason": "prompt_injection", "threats": sanitization.threats_detected}

        # 1.2 PII Scanning
        anonymized_payload, pii_result = pii_scanner.scan_payload(raw_payload)

        if pii_result.entities_count > 0:
            await kafka_producer.produce(
                topic="compliance.audit.pii",
                value={"source": source, "pii_count": pii_result.entities_count, "pii_score": pii_result.pii_score},
            )

        # Publish anonymized alert
        await kafka_producer.produce(
            topic="siem.alerts.anonymized",
            value=anonymized_payload,
        )

        # ─── Capa 2: LLM Core Engine ───
        triage_result = await alert_triage.triage(anonymized_payload, geo_origin)
        playbooks = await playbook_recommender.recommend(triage_result.classification, triage_result.severity_score)

        # Output validation
        validation = output_validator.validate(triage_result.reasoning)

        # ─── Capa 3: Auditoría ───
        pii_removed_pct = 100.0 - pii_result.pii_score
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

        # ─── Capa 3.1: Motores GDPR y NIS2 específicos ───
        gdpr_result = gdpr_engine.calculate_score(
            purpose_limitation=0.90,
            data_minimisation=pii_removed_pct / 100.0,
            lawful_basis=1.0,
            automated_decision=0.85,
            security_measures=0.85,
            breach_notification=0.90,
            pii_detected=pii_result.entities_count > 0,
        )

        nis2_result = nis2_engine.calculate_score(
            risk_analysis_policy=0.90,
            incident_handling=0.85,
            business_continuity=0.80,
            supply_chain_security=0.85,
            network_security=0.90,
            access_control=0.85,
            encryption_cryptography=0.90,
        )

        # ─── Capa 3.2: Ethical Gate (Interceptor Normativo) ───
        try:
            ethical_record = self.ethical_gate.evaluate(
                agent_id="alert_pipeline",
                action_type="alert_processing",
                gdpr_score=gdpr_result.total_score,
                nis2_score=nis2_result.total_score,
                bias_score=cs_result.total_score / 100.0,
                pii_detected=pii_result.entities_count > 0,
                context={
                    "source": source,
                    "classification": triage_result.classification,
                    "gdpr_risk": gdpr_result.risk_level,
                    "nis2_risk": nis2_result.risk_level,
                },
            )
        except ComplianceViolationError as e:
            await audit_logger.log(
                actor="ethical_gate",
                action="action.blocked",
                details=e.record.to_dict(),
            )
            await kafka_producer.produce(
                topic="compliance.blocked.alerts",
                value={"source": source, "reason": "ethical_gate_blocked", "record": e.record.to_dict()},
            )
            return {
                "status": "blocked",
                "reason": "ethical_gate_blocked",
                "composite_score": e.record.composite_score,
                "level": e.record.level.value,
            }

        hitl_assessment = hitl_controller.assess(
            compliance_score=cs_result.total_score,
            confidence=triage_result.confidence,
            has_pii=pii_result.entities_count > 0,
        )

        processing_time = int((datetime.now(UTC) - pipeline_start).total_seconds() * 1000)

        result = {
            "status": "processed",
            "source": source,
            "classification": triage_result.classification,
            "severity_score": triage_result.severity_score,
            "confidence": triage_result.confidence,
            "compliance_score": cs_result.total_score,
            "risk_level": cs_result.risk_level,
            "gdpr_score": gdpr_result.total_score,
            "gdpr_risk": gdpr_result.risk_level,
            "nis2_score": nis2_result.total_score,
            "nis2_risk": nis2_result.risk_level,
            "ethical_gate_level": ethical_record.level.value,
            "ethical_gate_composite": ethical_record.composite_score,
            "hitl_level": hitl_assessment.escalation.level,
            "pii_entities": pii_result.entities_count,
            "playbooks": [p.playbook_id for p in playbooks],
            "output_valid": validation.is_valid,
            "processing_time_ms": processing_time,
        }

        # Broadcast to WebSocket clients
        await broadcast_alert(result)
        await broadcast_compliance_update({
            "compliance_score": cs_result.total_score,
            "risk_level": cs_result.risk_level,
        })

        if hitl_assessment.escalation.level != "L0":
            await broadcast_hitl_update({
                "type": "new_review",
                "escalation_level": hitl_assessment.escalation.level,
                "compliance_score": cs_result.total_score,
            })

        return result


alert_pipeline = AlertPipelineService()
