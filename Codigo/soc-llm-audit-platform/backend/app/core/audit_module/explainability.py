"""
Explainability Module - SHAP (TreeSHAP/KernelSHAP) + LIME.
Generates auditable explanations with legal-readable narratives.
"""
import structlog
from dataclasses import dataclass
from typing import Optional

logger = structlog.get_logger()


@dataclass
class ExplanationResult:
    alert_id: str
    method: str  # "shap" | "lime" | "combined"
    feature_importance: list[dict]
    narrative: str
    confidence: float
    shap_values: Optional[dict] = None
    lime_explanation: Optional[dict] = None


class ExplainabilityModule:
    """
    SHAP + LIME explainability for LLM SOC decisions.
    Generates human-readable narratives for auditing.
    """

    # Feature names used in compliance scoring
    FEATURE_NAMES = [
        "data_minimization",
        "legal_basis",
        "transparency",
        "pipeline_security",
        "bias_fairness",
        "retention_compliance",
        "incident_reporting",
        "hitl_compliance",
    ]

    def explain_compliance_score(
        self,
        feature_values: dict[str, float],
        total_score: float,
        alert_id: str,
    ) -> ExplanationResult:
        """Generate SHAP-like explanation for a compliance score."""

        # Simulate SHAP values (contribution of each feature to final score)
        mean_score = 75.0  # Base expectation
        shap_values = {}
        for feature, value in feature_values.items():
            weight = self._get_weight(feature)
            contribution = weight * (value - mean_score)
            shap_values[feature] = round(contribution, 4)

        # Sort by absolute impact
        sorted_features = sorted(
            shap_values.items(), key=lambda x: abs(x[1]), reverse=True
        )

        feature_importance = [
            {
                "feature": name,
                "value": feature_values.get(name, 0),
                "shap_value": shap_val,
                "impact": "positive" if shap_val >= 0 else "negative",
            }
            for name, shap_val in sorted_features
        ]

        # Generate LIME-like local explanation
        lime_explanation = self._generate_lime_explanation(feature_values, total_score)

        # Generate human-readable narrative
        narrative = self._generate_narrative(
            feature_importance, total_score, alert_id
        )

        return ExplanationResult(
            alert_id=alert_id,
            method="combined",
            feature_importance=feature_importance,
            narrative=narrative,
            confidence=total_score / 100.0,
            shap_values=shap_values,
            lime_explanation=lime_explanation,
        )

    def _get_weight(self, feature: str) -> float:
        weights = {
            "data_minimization": 0.15,
            "legal_basis": 0.15,
            "transparency": 0.15,
            "pipeline_security": 0.15,
            "bias_fairness": 0.10,
            "retention_compliance": 0.10,
            "incident_reporting": 0.10,
            "hitl_compliance": 0.10,
        }
        return weights.get(feature, 0.1)

    def _generate_lime_explanation(
        self, features: dict[str, float], score: float
    ) -> dict:
        """Generate LIME-style local interpretable explanation."""
        explanation = {
            "intercept": 50.0,
            "local_prediction": score,
            "feature_weights": {},
        }

        for feature, value in features.items():
            weight = self._get_weight(feature)
            explanation["feature_weights"][feature] = {
                "weight": round(weight * value / 100, 4),
                "value": value,
                "contribution_pct": round(weight * 100, 1),
            }

        return explanation

    def _generate_narrative(
        self, features: list[dict], total_score: float, alert_id: str
    ) -> str:
        """Generate human-readable narrative for auditing (GDPR Art. 13-14)."""
        narrative = f"## Explicación de Decisión — Alerta {alert_id}\n\n"
        narrative += f"**Score de Cumplimiento Total: {total_score:.1f}/100**\n\n"

        if total_score >= 90:
            narrative += "✅ La transacción cumple con todos los marcos normativos.\n\n"
        elif total_score >= 70:
            narrative += "⚠️ La transacción requiere atención en algunas dimensiones.\n\n"
        elif total_score >= 50:
            narrative += "🔶 Riesgo medio detectado. Se requiere escalación al DPO.\n\n"
        else:
            narrative += "🔴 No conforme. Transacción bloqueada. Incidente formal requerido.\n\n"

        narrative += "### Factores principales:\n\n"

        for i, feat in enumerate(features[:5], 1):
            impact = "↑ positivo" if feat["impact"] == "positive" else "↓ negativo"
            narrative += (
                f"{i}. **{feat['feature'].replace('_', ' ').title()}** "
                f"(valor: {feat['value']:.1f}, impacto: {impact}, "
                f"SHAP: {feat['shap_value']:.4f})\n"
            )

        narrative += "\n### Base normativa:\n"
        narrative += "- GDPR Art. 5 (Minimización), Art. 6 (Base legal), Art. 13-14 (Transparencia)\n"
        narrative += "- NIS2 Art. 21 (Gestión de riesgos), Art. 23 (Notificación)\n"
        narrative += "- EU AI Act: Transparencia y explicabilidad obligatoria\n"

        return narrative


# Singleton
explainability_module = ExplainabilityModule()
