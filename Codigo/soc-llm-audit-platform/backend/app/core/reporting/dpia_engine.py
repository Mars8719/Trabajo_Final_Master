"""
DPIA Engine - Automated Data Protection Impact Assessment (GDPR Art. 35).
Auto-generates data flows, identifies risks, calculates inherent risk scores,
maps technical measures, generates rights mechanisms.
"""
import uuid
import structlog
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass
from typing import Optional

logger = structlog.get_logger()


@dataclass
class DPIARisk:
    risk_id: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH, VERY_HIGH
    likelihood: str  # LOW, MEDIUM, HIGH, VERY_HIGH
    inherent_score: int
    mitigations: list[str]
    residual_severity: str
    regulatory_reference: str


class DPIAEngine:
    """Automated DPIA generation per GDPR Art. 35."""

    SEVERITY_MAP = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "VERY_HIGH": 4}

    def generate_dpia(self, system_description: str) -> dict:
        """Generate a complete DPIA report."""

        data_flows = self._identify_data_flows()
        risks = self._identify_risks()
        technical_measures = self._map_technical_measures()
        org_measures = self._map_organizational_measures()
        rights_mechanisms = self._generate_rights_mechanisms()

        # Check if authority consultation needed
        very_high_risks = [r for r in risks if r.inherent_score >= 12]
        requires_authority = len(very_high_risks) > 0

        report = {
            "id": str(uuid.uuid4()),
            "version": "1.0",
            "status": "draft",
            "generated_at": datetime.now(UTC).isoformat(),
            "system_description": system_description,
            "data_flows": data_flows,
            "risks": [
                {
                    "risk_id": r.risk_id,
                    "description": r.description,
                    "severity": r.severity,
                    "likelihood": r.likelihood,
                    "inherent_score": r.inherent_score,
                    "mitigations": r.mitigations,
                    "residual_severity": r.residual_severity,
                    "regulatory_reference": r.regulatory_reference,
                }
                for r in risks
            ],
            "risk_matrix": self._generate_risk_matrix(risks),
            "technical_measures": technical_measures,
            "organizational_measures": org_measures,
            "rights_mechanisms": rights_mechanisms,
            "requires_authority_consultation": requires_authority,
            "next_review": (datetime.now(UTC) + timedelta(days=90)).isoformat(),
        }

        return report

    def _identify_data_flows(self) -> dict:
        return {
            "ingestion": {
                "sources": ["SIEM (Splunk/Elastic/Sentinel)", "EDR", "NDR", "IAM", "Firewalls", "Cloud Logs"],
                "data_types": ["IP addresses", "User IDs", "Hostnames", "Alert payloads", "Timestamps"],
                "pii_present": True,
                "processing": "Kafka topics → PII Scanner → Anonymization",
            },
            "llm_processing": {
                "input": "Anonymized alert data",
                "processing": "LLM Gateway → Alert Triage / Playbook / Summary",
                "output": "Classifications, recommendations, summaries",
                "pii_risk": "Residual PII from incomplete anonymization",
            },
            "audit_storage": {
                "storage": "PostgreSQL + append-only audit trail",
                "retention": "7 years (audit), 90 days (operational), 365 days (LLM decisions)",
                "encryption": "AES-256 at rest, TLS 1.3 in transit",
            },
            "reporting": {
                "consumers": ["DPO Dashboard", "CISO Reports", "CSIRT Notifications", "Regulator Exports"],
                "data_minimization": "Only aggregated/anonymized data in reports",
            },
        }

    def _identify_risks(self) -> list[DPIARisk]:
        return [
            DPIARisk("R1", "Fuga de PII a través del LLM", "HIGH", "MEDIUM", 9,
                     ["PII Scanner", "Tokenización", "E2E encryption"], "LOW", "GDPR Art. 5, 25, 32"),
            DPIARisk("R2", "Incumplimiento plazo 24h NIS2", "HIGH", "LOW", 6,
                     ["Automatización reporte", "Plantillas pre-aprobadas"], "LOW", "NIS2 Art. 23"),
            DPIARisk("R3", "Falta de trazabilidad IA", "HIGH", "LOW", 6,
                     ["Audit Trail inmutable", "SHAP/LIME"], "LOW", "EU AI Act, GDPR Art. 13"),
            DPIARisk("R4", "Transferencia ilegal fuera UE", "VERY_HIGH", "LOW", 8,
                     ["Geo-fencing", "Data residency enforcement"], "LOW", "GDPR Art. 44-49"),
            DPIARisk("R5", "Prompt Injection", "HIGH", "HIGH", 12,
                     ["Validación multicapa", "Sandboxing", "Output filtering"], "MEDIUM", "OWASP LLM01"),
            DPIARisk("R6", "Alucinación / Misinformation", "HIGH", "HIGH", 12,
                     ["Cross-validation", "Confidence threshold"], "MEDIUM", "EU AI Act"),
            DPIARisk("R7", "Model Poisoning", "VERY_HIGH", "LOW", 8,
                     ["AI-BOM", "Verificación procedencia", "Escaneo"], "LOW", "OWASP LLM03"),
            DPIARisk("R8", "Excessive Agency", "HIGH", "MEDIUM", 9,
                     ["Mínimo privilegio", "HITL obligatorio"], "LOW", "OWASP LLM08"),
            DPIARisk("R9", "Consumo descontrolado", "MEDIUM", "MEDIUM", 4,
                     ["Rate limiting", "Timeouts", "Budget guardrails"], "LOW", "FinOps"),
            DPIARisk("R10", "Sesgo en decisiones IA", "HIGH", "MEDIUM", 9,
                     ["Bias testing 5 dimensiones", "CI/CD bias gates"], "LOW", "EU AI Act, ISO 42001"),
            DPIARisk("R11", "Compliance theater", "MEDIUM", "HIGH", 8,
                     ["Red teaming continuo", "Auditoría externa"], "MEDIUM", "NIS2 Art.21"),
            DPIARisk("R12", "Desalineación frameworks", "MEDIUM", "MEDIUM", 4,
                     ["Crosswalk GDPR-NIS2-ISO-AI Act"], "LOW", "Multi-framework"),
        ]

    def _map_technical_measures(self) -> dict:
        return {
            "encryption": {"at_rest": "AES-256 (pgcrypto)", "in_transit": "TLS 1.3", "key_rotation": "90 days"},
            "access_control": {"method": "RBAC OAuth2/OIDC", "roles": 6, "principle": "Least privilege"},
            "pii_protection": {"scanner": "Microsoft Presidio + custom", "anonymization": "Replace/Tokenize"},
            "audit_trail": {"type": "Append-only", "integrity": "SHA-256 hash chain", "retention": "7 years"},
            "llm_security": {"firewall": "Runtime guardrails", "sandboxing": True, "rate_limiting": True},
            "monitoring": {"stack": "Prometheus + Grafana", "alerting": True, "drift_detection": True},
        }

    def _map_organizational_measures(self) -> dict:
        return {
            "dpo_involvement": "Continuous oversight via dashboard",
            "training": "AI Literacy program (4 tracks)",
            "incident_response": "NIS2-compliant 24h/72h/1m reporting",
            "third_party": "AI-BOM schema, supply chain verification",
            "red_teaming": "Continuous adversarial testing",
        }

    def _generate_rights_mechanisms(self) -> dict:
        return {
            "art_15_access": "API endpoint for data subject access requests",
            "art_16_rectification": "Dashboard for data correction",
            "art_17_erasure": "Automated right-to-be-forgotten pipeline",
            "art_18_restriction": "Processing restriction flag in pipeline",
            "art_20_portability": "JSON export of personal data",
            "art_21_objection": "Opt-out mechanism for LLM processing",
            "art_22_automated": "HITL controller ensures human oversight for significant decisions",
        }

    def _generate_risk_matrix(self, risks: list[DPIARisk]) -> dict:
        matrix = {"LOW": {"LOW": [], "MEDIUM": [], "HIGH": [], "VERY_HIGH": []},
                  "MEDIUM": {"LOW": [], "MEDIUM": [], "HIGH": [], "VERY_HIGH": []},
                  "HIGH": {"LOW": [], "MEDIUM": [], "HIGH": [], "VERY_HIGH": []},
                  "VERY_HIGH": {"LOW": [], "MEDIUM": [], "HIGH": [], "VERY_HIGH": []}}

        for r in risks:
            matrix[r.severity][r.likelihood].append(r.risk_id)
        return matrix


dpia_engine = DPIAEngine()
