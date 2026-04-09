"""
GDPR Compliance Engine — Sección 11.1 del Prompt Maestro

Motor específico GDPR con 6 controles ponderados:
  CS_GDPR = Σ(wi × si) - PII_penalty

Controles:
  purpose_limitation:   0.20
  data_minimisation:    0.20
  lawful_basis:         0.20
  automated_decision:   0.20
  security_measures:    0.10
  breach_notification:  0.10

PII Penalty: -0.30 si se detecta PII no anonimizado
"""
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class GDPRControl:
    name: str
    weight: float
    score: float  # 0.0 - 1.0
    article: str
    details: str = ""


@dataclass
class GDPRResult:
    total_score: float
    pii_penalty_applied: bool
    risk_level: str
    controls: list[GDPRControl]
    violated_articles: list[str]
    action_required: str


class GDPRComplianceEngine:
    """
    Motor de cumplimiento GDPR con 6 controles específicos.
    Implementa CS_GDPR = Σ(wi × si) - PII_penalty (0.30 si PII detectado).
    """

    WEIGHTS = {
        "purpose_limitation": 0.20,
        "data_minimisation": 0.20,
        "lawful_basis": 0.20,
        "automated_decision": 0.20,
        "security_measures": 0.10,
        "breach_notification": 0.10,
    }

    PII_PENALTY = 0.30

    ARTICLE_MAP = {
        "purpose_limitation": "Art. 5(1)(b)",
        "data_minimisation": "Art. 5(1)(c)",
        "lawful_basis": "Art. 6",
        "automated_decision": "Art. 22",
        "security_measures": "Art. 32",
        "breach_notification": "Art. 33/34",
    }

    def calculate_score(
        self,
        purpose_limitation: float = 1.0,
        data_minimisation: float = 1.0,
        lawful_basis: float = 1.0,
        automated_decision: float = 1.0,
        security_measures: float = 1.0,
        breach_notification: float = 1.0,
        pii_detected: bool = False,
    ) -> GDPRResult:
        """
        Calcula el score GDPR compuesto.

        Todos los scores de entrada normalizados 0.0 - 1.0.
        Retorna score final 0.0 - 1.0 (con penalización PII aplicada).
        """
        scores = {
            "purpose_limitation": purpose_limitation,
            "data_minimisation": data_minimisation,
            "lawful_basis": lawful_basis,
            "automated_decision": automated_decision,
            "security_measures": security_measures,
            "breach_notification": breach_notification,
        }

        controls = []
        for name, weight in self.WEIGHTS.items():
            controls.append(GDPRControl(
                name=name,
                weight=weight,
                score=scores[name],
                article=self.ARTICLE_MAP[name],
                details=f"{name}: {scores[name]:.2f} × {weight}",
            ))

        # CS_GDPR = Σ(wi × si)
        raw_score = sum(c.weight * c.score for c in controls)

        # Aplicar PII penalty
        pii_penalty_applied = pii_detected
        final_score = max(0.0, raw_score - (self.PII_PENALTY if pii_detected else 0.0))

        # Determinar nivel de riesgo
        risk_level, action = self._classify(final_score)

        # Artículos violados (controles con score < 0.60)
        violated = [c.article for c in controls if c.score < 0.60]
        if pii_detected:
            violated.append("Art. 5(1)(f) — PII no anonimizado")

        logger.info(
            "GDPR score calculated",
            raw_score=round(raw_score, 4),
            final_score=round(final_score, 4),
            pii_penalty=pii_detected,
            risk_level=risk_level,
        )

        return GDPRResult(
            total_score=round(final_score, 4),
            pii_penalty_applied=pii_penalty_applied,
            risk_level=risk_level,
            controls=controls,
            violated_articles=violated,
            action_required=action,
        )

    def _classify(self, score: float) -> tuple[str, str]:
        if score >= 0.85:
            return "compliant", "Registro normal, sin acción"
        elif score >= 0.60:
            return "warning", "Alerta GRC lead, revisión semanal"
        elif score >= 0.40:
            return "violation", "Escalación DPO, remediación 48h"
        else:
            return "blocked", "Bloquear transacción + incidente formal + DPIA"


gdpr_engine = GDPRComplianceEngine()
