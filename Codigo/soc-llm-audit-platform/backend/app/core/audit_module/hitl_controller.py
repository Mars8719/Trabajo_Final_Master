"""
HITL Controller - Human-in-the-Loop with 5 escalation levels.
Implements HOJR (Human Oversight Justification Record).

Levels:
  L0 Auto:      CS>=90, conf>=0.90, no PII, reversible → Auto registration
  L1 Async:     CS 70-89, conf 0.75-0.90 → Analyst queue, LLM provisional (4h)
  L2 Sync:      CS 50-69, conf 0.50-0.75, PII → Suspended until approval (1h)
  L3 Mandatory: CS<50, conf<0.50, special data → SOC Lead+DPO escalation (30min)
  L4 Kill:      Prompt injection, compromise → Immediate deactivation
"""
import structlog
from datetime import datetime, timedelta, UTC
from typing import Optional
from uuid import UUID
from dataclasses import dataclass

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class HITLEscalation:
    level: str
    action: str
    deadline: Optional[timedelta]
    framework: str
    requires_approval: bool
    auto_block: bool


@dataclass
class HITLAssessment:
    escalation: HITLEscalation
    compliance_score: float
    confidence: float
    has_pii: bool
    is_prompt_injection: bool
    reasoning: str


class HITLController:
    """Human-in-the-Loop Controller with 5 escalation levels."""

    ESCALATION_LEVELS = {
        "L0": HITLEscalation(
            level="L0",
            action="Registro automático",
            deadline=None,
            framework="—",
            requires_approval=False,
            auto_block=False,
        ),
        "L1": HITLEscalation(
            level="L1",
            action="Cola analista, LLM provisional",
            deadline=timedelta(hours=4),
            framework="NIS2 Art.21",
            requires_approval=False,
            auto_block=False,
        ),
        "L2": HITLEscalation(
            level="L2",
            action="Suspendida hasta aprobación",
            deadline=timedelta(hours=1),
            framework="GDPR Art.22",
            requires_approval=True,
            auto_block=True,
        ),
        "L3": HITLEscalation(
            level="L3",
            action="Escalación SOC Lead + DPO",
            deadline=timedelta(minutes=30),
            framework="GDPR + AI Act",
            requires_approval=True,
            auto_block=True,
        ),
        "L4": HITLEscalation(
            level="L4",
            action="Desactivación inmediata",
            deadline=timedelta(seconds=0),
            framework="NIS2 + OWASP",
            requires_approval=False,
            auto_block=True,
        ),
    }

    def __init__(self):
        self.kill_switch_active = False
        self.kill_switch_reason: Optional[str] = None
        self.kill_switch_activated_by: Optional[str] = None
        self.kill_switch_activated_at: Optional[datetime] = None

    def assess(
        self,
        compliance_score: float,
        confidence: float,
        has_pii: bool = False,
        has_special_data: bool = False,
        is_prompt_injection: bool = False,
        is_compromise: bool = False,
    ) -> HITLAssessment:
        """Determine the HITL escalation level for a transaction."""

        # L4 Kill Switch - Immediate
        if is_prompt_injection or is_compromise or self.kill_switch_active:
            return HITLAssessment(
                escalation=self.ESCALATION_LEVELS["L4"],
                compliance_score=compliance_score,
                confidence=confidence,
                has_pii=has_pii,
                is_prompt_injection=is_prompt_injection,
                reasoning="Prompt injection o compromiso detectado. Desactivación inmediata.",
            )

        # L3 Mandatory - CS<50, conf<0.50, special data
        if compliance_score < settings.HITL_L3_CS_MAX or confidence < settings.HITL_L2_CONF_MIN or has_special_data:
            return HITLAssessment(
                escalation=self.ESCALATION_LEVELS["L3"],
                compliance_score=compliance_score,
                confidence=confidence,
                has_pii=has_pii,
                is_prompt_injection=False,
                reasoning=f"CS={compliance_score:.1f} < 50 o confianza baja. Escalación obligatoria a SOC Lead + DPO.",
            )

        # L2 Sync - CS 50-69, conf 0.50-0.75, PII
        if compliance_score < settings.HITL_L1_CS_MIN or confidence < settings.HITL_L1_CONF_MIN or has_pii:
            return HITLAssessment(
                escalation=self.ESCALATION_LEVELS["L2"],
                compliance_score=compliance_score,
                confidence=confidence,
                has_pii=has_pii,
                is_prompt_injection=False,
                reasoning=f"CS={compliance_score:.1f} en rango 50-69 o PII detectado. Suspendida hasta aprobación.",
            )

        # L1 Async - CS 70-89, conf 0.75-0.90
        if compliance_score < settings.HITL_L0_CS_MIN or confidence < settings.HITL_L0_CONF_MIN:
            return HITLAssessment(
                escalation=self.ESCALATION_LEVELS["L1"],
                compliance_score=compliance_score,
                confidence=confidence,
                has_pii=has_pii,
                is_prompt_injection=False,
                reasoning=f"CS={compliance_score:.1f} en rango 70-89. Revisión asíncrona en cola.",
            )

        # L0 Auto - CS>=90, conf>=0.90, no PII, reversible
        return HITLAssessment(
            escalation=self.ESCALATION_LEVELS["L0"],
            compliance_score=compliance_score,
            confidence=confidence,
            has_pii=has_pii,
            is_prompt_injection=False,
            reasoning=f"CS={compliance_score:.1f} >= 90, confianza alta. Procesamiento automático.",
        )

    def activate_kill_switch(self, reason: str, activated_by: str) -> dict:
        """Activate L4 Kill Switch - Immediate deactivation."""
        self.kill_switch_active = True
        self.kill_switch_reason = reason
        self.kill_switch_activated_by = activated_by
        self.kill_switch_activated_at = datetime.now(UTC)

        logger.critical(
            "KILL SWITCH ACTIVATED",
            reason=reason,
            activated_by=activated_by,
        )

        return {
            "status": "KILL_SWITCH_ACTIVE",
            "reason": reason,
            "activated_by": activated_by,
            "activated_at": self.kill_switch_activated_at.isoformat(),
        }

    def deactivate_kill_switch(self, deactivated_by: str) -> dict:
        """Deactivate kill switch (requires CISO role)."""
        self.kill_switch_active = False
        logger.warning("Kill switch deactivated", deactivated_by=deactivated_by)
        return {"status": "KILL_SWITCH_DEACTIVATED", "deactivated_by": deactivated_by}

    def validate_hojr(self, decision: dict) -> tuple[bool, list[str]]:
        """
        Validate HOJR (Human Oversight Justification Record).
        Anti-rubber-stamping: ensures meaningful review.
        """
        errors = []

        if not decision.get("justification") or len(decision["justification"]) < 20:
            errors.append("Justificación insuficiente (mínimo 20 caracteres)")

        if decision.get("time_to_decision_seconds", 0) < 10:
            errors.append("Anti-rubber-stamping: decisión demasiado rápida (< 10s)")

        if not decision.get("shap_viewed") and not decision.get("lime_viewed"):
            errors.append("Debe revisar explicabilidad SHAP o LIME antes de decidir")

        return len(errors) == 0, errors


# Singleton
hitl_controller = HITLController()
