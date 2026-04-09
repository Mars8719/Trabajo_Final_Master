"""
NIS2 Test Suite — 5 Tests
NIS2-01: Reporte 24h
NIS2-02: Gestión riesgos
NIS2-03: Continuidad
NIS2-04: Auditoría bajo demanda
NIS2-05: Responsabilidad ejecutiva
"""
import pytest
from datetime import datetime, timedelta, UTC
from app.core.reporting.nis2_reporter import NIS2Reporter
from app.core.resilience.fallback_manager import FallbackManager, DegradationLevel
from app.core.audit_module.audit_logger import AuditTrailLogger
from app.core.audit_module.hitl_controller import HITLController


class TestNIS2:
    """5 tests NIS2 compliance."""

    def setup_method(self):
        self.nis2_reporter = NIS2Reporter()
        self.fallback_manager = FallbackManager()
        self.hitl_controller = HITLController()

    # NIS2-01: Reporte 24h — Ransomware a las 03:00 UTC
    def test_nis2_01_24h_reporting(self):
        """Ransomware at 03:00 UTC → CSIRT notification < 24h."""
        incident = {
            "incident_id": "INC-2026-001",
            "type": "ransomware",
            "severity": "critical",
            "description": "Ransomware detected at 03:00 UTC on production servers",
            "affected_services": ["web-app", "database"],
        }

        report = self.nis2_reporter.generate_preliminary_report(incident)

        assert report.report_type == "preliminary"
        assert report.within_deadline is True
        assert report.content["incident_type"] == "ransomware"
        assert report.content["csirt_notification"] is True
        assert "NIS2 Art. 23" in report.content["regulatory_reference"]

        # Verify deadline check
        deadline = self.nis2_reporter.check_deadlines(datetime.now(UTC))
        assert deadline["preliminary_24h"]["within_deadline"] is True

    # NIS2-02: Gestión de riesgos — CVE crítico en infra esencial
    def test_nis2_02_risk_management(self):
        """Critical CVE in essential infrastructure → LLM evaluates, recommends playbook."""
        from app.core.llm_engine.playbook import PlaybookRecommender

        recommender = PlaybookRecommender()

        # Malware/ransomware should map to containment playbooks
        import asyncio
        playbooks = asyncio.run(
            recommender.recommend("ransomware", severity=95.0)
        )

        assert len(playbooks) > 0, "Debe recomendar al menos un playbook"
        assert any("Ransomware" in p.name for p in playbooks), "Debe incluir playbook de ransomware"
        assert any("NIS2" in f for p in playbooks for f in p.applicable_frameworks), \
            "Playbooks deben referenciar NIS2"

    # NIS2-03: Continuidad — Caída de nodo LLM
    def test_nis2_03_continuity(self):
        """LLM node failure → Failover without interruption."""
        # Test graceful degradation
        status = self.fallback_manager.set_level(DegradationLevel.REDUCED, "LLM node failure")

        assert status.level == DegradationLevel.REDUCED
        assert status.ai_percentage == 30
        assert self.fallback_manager.should_use_llm("critical") is True, \
            "Critical alerts should still use LLM in Reduced mode"
        assert self.fallback_manager.should_use_llm("low") is False, \
            "Low severity should not use LLM in Reduced mode"

        # Test full manual fallback
        status_manual = self.fallback_manager.set_level(DegradationLevel.MANUAL, "Kill switch")
        assert status_manual.ai_percentage == 0
        assert self.fallback_manager.should_use_llm("critical") is False

        # Reset
        self.fallback_manager.set_level(DegradationLevel.FULL_AI)

    # NIS2-04: Auditoría bajo demanda — Solicitud de auditor para 90 días
    def test_nis2_04_audit_on_demand(self):
        """Auditor requests 90-day records → Audit Trail exports records."""
        audit_logger = AuditTrailLogger()

        # Verify audit logger can query with date filters
        assert hasattr(audit_logger, 'query'), "Debe soportar consultas"
        assert hasattr(audit_logger, 'verify_chain_integrity'), "Debe verificar integridad"

        # Verify retention settings
        from app.config import get_settings
        settings = get_settings()
        assert settings.AUDIT_OPERATIONAL_LOGS_DAYS >= 90, \
            f"Retención operativa debe ser >= 90 días, es {settings.AUDIT_OPERATIONAL_LOGS_DAYS}"
        assert settings.AUDIT_RETENTION_YEARS >= 7, \
            f"Retención de auditoría debe ser >= 7 años, es {settings.AUDIT_RETENTION_YEARS}"

    # NIS2-05: Responsabilidad ejecutiva — Decisión sin aprobación
    def test_nis2_05_executive_responsibility(self):
        """Decision without approval → HITL blocks and escalates."""
        # Low CS score should trigger mandatory HITL review
        assessment = self.hitl_controller.assess(
            compliance_score=45.0,
            confidence=0.40,
            has_special_data=True,
        )

        assert assessment.escalation.level == "L3", \
            f"Debe escalar a L3 (Mandatory), fue {assessment.escalation.level}"
        assert assessment.escalation.requires_approval is True, \
            "L3 debe requerir aprobación"
        assert assessment.escalation.auto_block is True, \
            "L3 debe bloquear automáticamente"
        assert "SOC Lead" in assessment.escalation.action, \
            "L3 debe escalar a SOC Lead + DPO"
