"""
NIS2 Reporter - Automated incident reporting per NIS2 Art. 23.
Deadlines: 24h preliminary, 72h detailed, 1 month final.
"""
import structlog
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass
from typing import Optional

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class NIS2Report:
    report_type: str  # preliminary, detailed, final
    incident_id: str
    generated_at: str
    deadline: str
    within_deadline: bool
    content: dict


class NIS2Reporter:
    """Automated NIS2 incident reporting with deadline tracking."""

    def generate_preliminary_report(self, incident_data: dict) -> NIS2Report:
        """Generate 24h preliminary report for CSIRT notification."""
        now = datetime.now(UTC)
        deadline = now + timedelta(hours=settings.NIS2_PRELIMINARY_DEADLINE_HOURS)

        report = NIS2Report(
            report_type="preliminary",
            incident_id=incident_data.get("incident_id", "unknown"),
            generated_at=now.isoformat(),
            deadline=deadline.isoformat(),
            within_deadline=True,
            content={
                "incident_type": incident_data.get("type", "unknown"),
                "severity": incident_data.get("severity", "medium"),
                "affected_services": incident_data.get("affected_services", []),
                "initial_description": incident_data.get("description", ""),
                "detection_method": "SOC-LLM Automated Pipeline",
                "initial_impact": incident_data.get("impact", "Under assessment"),
                "regulatory_reference": "NIS2 Art. 23(4)(a)",
                "csirt_notification": True,
            },
        )

        logger.info("NIS2 preliminary report generated", incident_id=report.incident_id)
        return report

    def generate_detailed_report(self, incident_data: dict) -> NIS2Report:
        """Generate 72h detailed report."""
        now = datetime.now(UTC)
        deadline = now + timedelta(hours=settings.NIS2_DETAILED_DEADLINE_HOURS)

        return NIS2Report(
            report_type="detailed",
            incident_id=incident_data.get("incident_id", "unknown"),
            generated_at=now.isoformat(),
            deadline=deadline.isoformat(),
            within_deadline=True,
            content={
                "incident_type": incident_data.get("type", "unknown"),
                "severity": incident_data.get("severity", "medium"),
                "root_cause_analysis": incident_data.get("root_cause", "Investigation ongoing"),
                "affected_systems": incident_data.get("affected_systems", []),
                "data_compromise": incident_data.get("data_compromise", False),
                "containment_actions": incident_data.get("containment_actions", []),
                "remediation_plan": incident_data.get("remediation_plan", "In development"),
                "regulatory_reference": "NIS2 Art. 23(4)(b)",
            },
        )

    def generate_final_report(self, incident_data: dict) -> NIS2Report:
        """Generate 1-month final report."""
        now = datetime.now(UTC)
        deadline = now + timedelta(days=settings.NIS2_FINAL_DEADLINE_DAYS)

        return NIS2Report(
            report_type="final",
            incident_id=incident_data.get("incident_id", "unknown"),
            generated_at=now.isoformat(),
            deadline=deadline.isoformat(),
            within_deadline=True,
            content={
                "incident_type": incident_data.get("type", "unknown"),
                "root_cause": incident_data.get("root_cause", ""),
                "full_impact_assessment": incident_data.get("impact_assessment", {}),
                "remediation_complete": incident_data.get("remediation_complete", False),
                "lessons_learned": incident_data.get("lessons_learned", []),
                "preventive_measures": incident_data.get("preventive_measures", []),
                "regulatory_reference": "NIS2 Art. 23(4)(c)",
                "cross_border_impact": incident_data.get("cross_border", False),
            },
        )

    def check_deadlines(self, incident_created_at: datetime) -> dict:
        """Check if NIS2 reporting deadlines are met."""
        now = datetime.now(UTC)
        elapsed = now - incident_created_at

        return {
            "preliminary_24h": {
                "deadline_hours": settings.NIS2_PRELIMINARY_DEADLINE_HOURS,
                "elapsed_hours": round(elapsed.total_seconds() / 3600, 2),
                "within_deadline": elapsed < timedelta(hours=settings.NIS2_PRELIMINARY_DEADLINE_HOURS),
            },
            "detailed_72h": {
                "deadline_hours": settings.NIS2_DETAILED_DEADLINE_HOURS,
                "elapsed_hours": round(elapsed.total_seconds() / 3600, 2),
                "within_deadline": elapsed < timedelta(hours=settings.NIS2_DETAILED_DEADLINE_HOURS),
            },
            "final_30d": {
                "deadline_days": settings.NIS2_FINAL_DEADLINE_DAYS,
                "elapsed_days": round(elapsed.total_seconds() / 86400, 2),
                "within_deadline": elapsed < timedelta(days=settings.NIS2_FINAL_DEADLINE_DAYS),
            },
        }


nis2_reporter = NIS2Reporter()
