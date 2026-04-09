"""
Threat Summary Generator - Generates executive threat summaries via LLM.
"""
import structlog
from dataclasses import dataclass

from app.core.llm_engine.gateway import llm_gateway

logger = structlog.get_logger()


@dataclass
class ThreatSummary:
    executive_summary: str
    technical_details: str
    impact_assessment: str
    recommended_actions: list[str]
    regulatory_implications: list[str]


class ThreatSummarizer:
    """Generates threat summaries for board-level and technical audiences."""

    async def generate_summary(
        self,
        alerts: list[dict],
        audience: str = "technical",
    ) -> ThreatSummary:
        """Generate a threat summary from multiple alerts."""
        prompt = self._build_summary_prompt(alerts, audience)

        response = await llm_gateway.generate(prompt=prompt)

        return ThreatSummary(
            executive_summary=f"Se detectaron {len(alerts)} alertas de seguridad. "
                            f"Análisis LLM completado con confianza {response.confidence:.0%}.",
            technical_details=response.content,
            impact_assessment="Evaluación de impacto en progreso. Se requiere revisión humana.",
            recommended_actions=[
                "Revisar alertas priorizadas por el LLM",
                "Verificar IOCs contra inteligencia de amenazas",
                "Ejecutar playbooks recomendados",
            ],
            regulatory_implications=[
                "NIS2: Evaluar si requiere notificación 24h",
                "GDPR: Verificar si hay datos personales afectados",
                "DORA: Evaluar impacto en servicios financieros",
            ],
        )

    def _build_summary_prompt(self, alerts: list[dict], audience: str) -> str:
        return f"""Genera un resumen de amenazas para audiencia {audience}.
Alertas a analizar: {len(alerts)}
Datos: {alerts[:5]}  # Limit for token management
"""


threat_summarizer = ThreatSummarizer()
