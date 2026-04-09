"""
XAI-LLM Bridge - Connects explainability module with LLM for narrative generation.
"""
import structlog
from typing import Optional

logger = structlog.get_logger()


class XAILLMBridge:
    """Bridges SHAP/LIME explanations to LLM for natural language narratives."""

    async def generate_narrative(
        self,
        shap_values: dict,
        lime_explanation: Optional[dict],
        context: dict,
    ) -> str:
        """Use local LLM to generate human-readable explanation from XAI data."""
        # Build prompt for narrative generation
        prompt = self._build_narrative_prompt(shap_values, lime_explanation, context)

        # For now, return a structured narrative without LLM call
        narrative = self._structured_narrative(shap_values, context)
        return narrative

    def _build_narrative_prompt(
        self, shap_values: dict, lime_explanation: Optional[dict], context: dict
    ) -> str:
        return f"""Genera una explicación clara y auditable de la siguiente decisión de compliance:

Score total: {context.get('total_score', 'N/A')}
Nivel de riesgo: {context.get('risk_level', 'N/A')}

Valores SHAP (contribución de cada dimensión):
{shap_values}

La explicación debe ser entendible por un DPO no técnico y cumplir con GDPR Art. 13-14.
Incluye: factores principales, base normativa aplicable, y acciones recomendadas.
"""

    def _structured_narrative(self, shap_values: dict, context: dict) -> str:
        score = context.get("total_score", 0)
        risk = context.get("risk_level", "unknown")

        narrative = f"Decisión de cumplimiento: Score {score}/100 (Nivel: {risk}).\n"

        top_factors = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        for factor, value in top_factors:
            direction = "favorece" if value > 0 else "penaliza"
            narrative += f"- {factor}: {direction} la puntuación ({value:+.3f})\n"

        return narrative


xai_llm_bridge = XAILLMBridge()
