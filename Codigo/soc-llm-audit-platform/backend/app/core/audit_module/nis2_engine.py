"""
NIS2 Compliance Engine — Sección 11.2 del Prompt Maestro

Motor específico NIS2 con 7 controles ponderados:
  CS_NIS2 = Σ(wi × si)

Controles:
  risk_analysis_policy:    0.15
  incident_handling:       0.20
  business_continuity:     0.15
  supply_chain_security:   0.15
  network_security:        0.15
  access_control:          0.10
  encryption_cryptography: 0.10
"""
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class NIS2Control:
    name: str
    weight: float
    score: float  # 0.0 - 1.0
    article: str
    details: str = ""


@dataclass
class NIS2Result:
    total_score: float
    risk_level: str
    controls: list[NIS2Control]
    violated_articles: list[str]
    sla_breach: bool
    action_required: str


class NIS2ComplianceEngine:
    """
    Motor de cumplimiento NIS2 con 7 controles específicos.
    Implementa CS_NIS2 = Σ(wi × si).
    """

    WEIGHTS = {
        "risk_analysis_policy": 0.15,
        "incident_handling": 0.20,
        "business_continuity": 0.15,
        "supply_chain_security": 0.15,
        "network_security": 0.15,
        "access_control": 0.10,
        "encryption_cryptography": 0.10,
    }

    ARTICLE_MAP = {
        "risk_analysis_policy": "Art. 21(2)(a)",
        "incident_handling": "Art. 21(2)(b) / Art. 23",
        "business_continuity": "Art. 21(2)(c)",
        "supply_chain_security": "Art. 21(2)(d)",
        "network_security": "Art. 21(2)(e)",
        "access_control": "Art. 21(2)(i)",
        "encryption_cryptography": "Art. 21(2)(h)",
    }

    # SLA deadlines NIS2 Art. 23
    SLA_PRELIMINARY_HOURS = 24
    SLA_DETAILED_HOURS = 72
    SLA_FINAL_DAYS = 30

    def calculate_score(
        self,
        risk_analysis_policy: float = 1.0,
        incident_handling: float = 1.0,
        business_continuity: float = 1.0,
        supply_chain_security: float = 1.0,
        network_security: float = 1.0,
        access_control: float = 1.0,
        encryption_cryptography: float = 1.0,
        incident_notification_hours: float | None = None,
    ) -> NIS2Result:
        """
        Calcula el score NIS2 compuesto.

        Todos los scores normalizados 0.0 - 1.0.
        incident_notification_hours: horas desde detección de incidente (None = sin incidente activo).
        """
        scores = {
            "risk_analysis_policy": risk_analysis_policy,
            "incident_handling": incident_handling,
            "business_continuity": business_continuity,
            "supply_chain_security": supply_chain_security,
            "network_security": network_security,
            "access_control": access_control,
            "encryption_cryptography": encryption_cryptography,
        }

        controls = []
        for name, weight in self.WEIGHTS.items():
            controls.append(NIS2Control(
                name=name,
                weight=weight,
                score=scores[name],
                article=self.ARTICLE_MAP[name],
                details=f"{name}: {scores[name]:.2f} × {weight}",
            ))

        # CS_NIS2 = Σ(wi × si)
        total_score = sum(c.weight * c.score for c in controls)

        # SLA breach detection
        sla_breach = False
        if incident_notification_hours is not None:
            if incident_notification_hours > self.SLA_PRELIMINARY_HOURS:
                sla_breach = True
                # Penalizar incident_handling si SLA excedido
                for c in controls:
                    if c.name == "incident_handling":
                        penalty = min(0.5, (incident_notification_hours - self.SLA_PRELIMINARY_HOURS) / self.SLA_PRELIMINARY_HOURS * 0.5)
                        c.score = max(0.0, c.score - penalty)
                        c.details += f" [SLA penalty: -{penalty:.2f}]"
                # Recalcular
                total_score = sum(c.weight * c.score for c in controls)

        # Clasificar nivel de riesgo
        risk_level, action = self._classify(total_score)

        # Artículos violados (controles con score < 0.60)
        violated = [c.article for c in controls if c.score < 0.60]
        if sla_breach:
            violated.append("Art. 23 — SLA notificación excedido")

        logger.info(
            "NIS2 score calculated",
            total_score=round(total_score, 4),
            risk_level=risk_level,
            sla_breach=sla_breach,
        )

        return NIS2Result(
            total_score=round(total_score, 4),
            risk_level=risk_level,
            controls=controls,
            violated_articles=violated,
            sla_breach=sla_breach,
            action_required=action,
        )

    def _classify(self, score: float) -> tuple[str, str]:
        if score >= 0.85:
            return "compliant", "Registro normal, sin acción"
        elif score >= 0.60:
            return "warning", "Alerta al CISO, revisión semanal"
        elif score >= 0.40:
            return "violation", "Escalación CSIRT, remediación inmediata"
        else:
            return "blocked", "Bloquear + notificación autoridad competente"


nis2_engine = NIS2ComplianceEngine()
