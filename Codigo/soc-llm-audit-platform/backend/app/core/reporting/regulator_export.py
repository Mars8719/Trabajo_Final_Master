"""
Regulator Export - Export data in regulator-compliant formats.
Supports GDPR Art. 30, NIS2 Art. 23 reporting requirements.
"""
import json
import structlog
from datetime import datetime, UTC
from typing import Optional

logger = structlog.get_logger()


class RegulatorExport:
    """Exports compliance data in formats required by regulators."""

    def export_gdpr_records(self, records: list[dict]) -> dict:
        """Export records per GDPR Art. 30 (Records of Processing Activities)."""
        return {
            "export_type": "GDPR Art. 30 - Records of Processing Activities",
            "generated_at": datetime.now(UTC).isoformat(),
            "controller": "SOC-LLM Audit Platform",
            "processing_purposes": [
                "Security incident detection and response",
                "Compliance monitoring and auditing",
                "LLM-assisted alert triage",
            ],
            "data_categories": [
                "Network logs", "Alert payloads", "IP addresses (anonymized)",
                "User identifiers (pseudonymized)", "Security events",
            ],
            "retention_periods": {
                "audit_trail": "7 years",
                "operational_logs": "90 days",
                "llm_decisions": "365 days",
            },
            "technical_measures": [
                "AES-256 encryption at rest",
                "TLS 1.3 in transit",
                "PII anonymization via Presidio",
                "RBAC with 6 roles",
                "Append-only audit trail with hash chain",
            ],
            "records_count": len(records),
            "records": records,
        }

    def export_nis2_report(self, incident_data: dict) -> dict:
        """Export NIS2 incident report for CSIRT."""
        return {
            "export_type": "NIS2 Art. 23 - Incident Notification",
            "generated_at": datetime.now(UTC).isoformat(),
            "incident": incident_data,
            "reporting_entity": "SOC-LLM Audit Platform",
            "contact": {
                "role": "CISO / DPO",
                "method": "Secure channel",
            },
        }

    def export_ai_act_transparency(self, system_info: dict) -> dict:
        """Export EU AI Act transparency report."""
        return {
            "export_type": "EU AI Act - Transparency Report",
            "system_name": "SOC-LLM Audit Platform",
            "risk_category": "High-risk AI system (security domain)",
            "generated_at": datetime.now(UTC).isoformat(),
            "explainability": {
                "methods": ["SHAP (TreeSHAP/KernelSHAP)", "LIME"],
                "narrative_generation": True,
                "human_oversight": "HITL with 5 escalation levels",
            },
            "bias_testing": {
                "dimensions": ["geographic", "temporal", "linguistic", "severity", "source"],
                "ci_cd_quality_gate": True,
            },
            "data_governance": {
                "pii_protection": "Microsoft Presidio + custom recognizers",
                "data_residency": "EU geo-fencing enforced",
            },
            **system_info,
        }


regulator_export = RegulatorExport()
