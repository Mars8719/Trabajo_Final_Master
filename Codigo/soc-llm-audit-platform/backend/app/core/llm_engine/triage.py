"""
Alert Triage LLM - Classifies and prioritizes alerts using LLM.
"""
import structlog
from dataclasses import dataclass
from typing import Optional

from app.core.llm_engine.gateway import llm_gateway, LLMResponse

logger = structlog.get_logger()


@dataclass
class TriageResult:
    classification: str
    severity_score: float
    confidence: float
    reasoning: str
    recommended_actions: list[str]
    ioc_indicators: list[str]
    llm_response: LLMResponse


class AlertTriageLLM:
    """Uses LLM to triage and classify SOC alerts."""

    SYSTEM_PROMPT = """Eres un analista SOC Tier-2 experto. Analiza la alerta de seguridad y proporciona:
1. Clasificación (malware, phishing, lateral_movement, data_exfiltration, brute_force, anomaly, false_positive)
2. Score de severidad (0-100)
3. Nivel de confianza (0-1)
4. Razonamiento detallado
5. Acciones recomendadas
6. IOCs identificados

Responde SIEMPRE en formato estructurado. NO incluyas información PII."""

    async def triage(
        self,
        alert_payload: dict,
        geo_origin: Optional[str] = None,
    ) -> TriageResult:
        """Triage an alert using LLM analysis."""
        prompt = self._build_prompt(alert_payload)

        llm_response = await llm_gateway.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            geo_origin=geo_origin,
        )

        # Parse LLM response
        result = self._parse_response(llm_response)
        return result

    def _build_prompt(self, payload: dict) -> str:
        return f"""Analiza la siguiente alerta SOC:

Fuente: {payload.get('source', 'unknown')}
Tipo: {payload.get('type', 'unknown')}
Severidad original: {payload.get('severity', 'unknown')}
Datos: {payload}

Proporciona clasificación, severidad, confianza, razonamiento, acciones e IOCs."""

    def _parse_response(self, llm_response: LLMResponse) -> TriageResult:
        return TriageResult(
            classification="anomaly",
            severity_score=65.0,
            confidence=llm_response.confidence,
            reasoning=llm_response.content,
            recommended_actions=[
                "Verificar indicadores IOC",
                "Comprobar movimiento lateral",
                "Escalar si se confirma",
            ],
            ioc_indicators=[],
            llm_response=llm_response,
        )


alert_triage = AlertTriageLLM()
