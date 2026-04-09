"""
Compliance Policy Engine - Evaluates each LLM action against GDPR and NIS2 rules.
CS = Σ(wi × si) where Σ(wi) = 1.0

Score ranges:
  90-100: Compliant (normal logging)
  70-89:  Attention (GRC lead alert, weekly review)
  50-69:  Medium Risk (DPO escalation, 48h remediation)
  < 50:   Non-compliant (block transaction + formal incident + DPIA)
"""
import structlog
from dataclasses import dataclass
from typing import Optional

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class ComplianceDimension:
    name: str
    weight: float
    score: float  # 0-100
    details: str = ""


@dataclass
class ComplianceResult:
    total_score: float
    risk_level: str
    dimensions: list[ComplianceDimension]
    action_required: str
    gdpr_articles: list[str]
    nis2_articles: list[str]


class ComplianceScoringEngine:
    """
    Compliance Scoring Engine - Score compuesto 0-100 por transacción.
    Implementa CS = Σ(wi × si) donde Σ(wi) = 1.0
    """

    def __init__(self):
        self.weights = {
            "data_minimization": settings.CS_WEIGHT_DATA_MINIMIZATION,      # 0.15
            "legal_basis": settings.CS_WEIGHT_LEGAL_BASIS,                  # 0.15
            "transparency": settings.CS_WEIGHT_TRANSPARENCY,                # 0.15
            "pipeline_security": settings.CS_WEIGHT_PIPELINE_SECURITY,      # 0.15
            "bias_fairness": settings.CS_WEIGHT_BIAS_FAIRNESS,              # 0.10
            "retention_compliance": settings.CS_WEIGHT_RETENTION,            # 0.10
            "incident_reporting": settings.CS_WEIGHT_INCIDENT_REPORTING,     # 0.10
            "hitl_compliance": settings.CS_WEIGHT_HITL,                      # 0.10
        }

    def calculate_score(
        self,
        pii_removed_pct: float = 100.0,
        legal_basis_documented: bool = True,
        transparency_score: float = 80.0,
        security_score: float = 85.0,
        bias_score: float = 90.0,
        retention_score: float = 80.0,
        incident_latency_score: float = 90.0,
        hitl_active: bool = True,
    ) -> ComplianceResult:
        """Calculate composite compliance score."""

        dimensions = [
            ComplianceDimension(
                name="data_minimization",
                weight=self.weights["data_minimization"],
                score=pii_removed_pct,
                details=f"PII anonimizado: {pii_removed_pct:.1f}%",
            ),
            ComplianceDimension(
                name="legal_basis",
                weight=self.weights["legal_basis"],
                score=100.0 if legal_basis_documented else 0.0,
                details="Base legal documentada" if legal_basis_documented else "Sin base legal",
            ),
            ComplianceDimension(
                name="transparency",
                weight=self.weights["transparency"],
                score=transparency_score,
                details=f"SHAP/LIME + trazabilidad: {transparency_score:.1f}",
            ),
            ComplianceDimension(
                name="pipeline_security",
                weight=self.weights["pipeline_security"],
                score=security_score,
                details=f"Cifrado + RBAC + logs: {security_score:.1f}",
            ),
            ComplianceDimension(
                name="bias_fairness",
                weight=self.weights["bias_fairness"],
                score=bias_score,
                details=f"Ratio impacto adverso: {bias_score:.1f}",
            ),
            ComplianceDimension(
                name="retention_compliance",
                weight=self.weights["retention_compliance"],
                score=retention_score,
                details=f"Retención + borrado: {retention_score:.1f}",
            ),
            ComplianceDimension(
                name="incident_reporting",
                weight=self.weights["incident_reporting"],
                score=incident_latency_score,
                details=f"Latencia notificación NIS2: {incident_latency_score:.1f}",
            ),
            ComplianceDimension(
                name="hitl_compliance",
                weight=self.weights["hitl_compliance"],
                score=100.0 if hitl_active else 0.0,
                details="HITL activo" if hitl_active else "Sin supervisión humana",
            ),
        ]

        # CS = Σ(wi × si)
        total_score = sum(d.weight * d.score for d in dimensions)

        # Determine risk level and action
        risk_level, action_required = self._determine_risk_level(total_score)

        # Map to GDPR/NIS2 articles
        gdpr_articles = self._map_gdpr_articles(dimensions)
        nis2_articles = self._map_nis2_articles(dimensions)

        logger.info(
            "Compliance score calculated",
            total_score=round(total_score, 2),
            risk_level=risk_level,
        )

        return ComplianceResult(
            total_score=round(total_score, 2),
            risk_level=risk_level,
            dimensions=dimensions,
            action_required=action_required,
            gdpr_articles=gdpr_articles,
            nis2_articles=nis2_articles,
        )

    def _determine_risk_level(self, score: float) -> tuple[str, str]:
        if score >= 90:
            return "compliant", "Registro normal, sin acción"
        elif score >= 70:
            return "attention", "Alerta al GRC lead, revisión semanal"
        elif score >= 50:
            return "medium_risk", "Escalación al DPO, remediación 48h"
        else:
            return "non_compliant", "Bloqueo transacción + incidente formal + DPIA"

    def _map_gdpr_articles(self, dimensions: list[ComplianceDimension]) -> list[str]:
        articles = []
        for d in dimensions:
            if d.score < 70:
                if d.name == "data_minimization":
                    articles.extend(["Art. 5", "Art. 25"])
                elif d.name == "legal_basis":
                    articles.append("Art. 6")
                elif d.name == "transparency":
                    articles.extend(["Art. 13", "Art. 14"])
                elif d.name == "pipeline_security":
                    articles.append("Art. 32")
                elif d.name == "retention_compliance":
                    articles.append("Art. 17")
                elif d.name == "hitl_compliance":
                    articles.append("Art. 22")
        return list(set(articles))

    def _map_nis2_articles(self, dimensions: list[ComplianceDimension]) -> list[str]:
        articles = []
        for d in dimensions:
            if d.score < 70:
                if d.name == "pipeline_security":
                    articles.append("Art. 21")
                elif d.name == "incident_reporting":
                    articles.append("Art. 23")
        return list(set(articles))


# Singleton
compliance_engine = ComplianceScoringEngine()
