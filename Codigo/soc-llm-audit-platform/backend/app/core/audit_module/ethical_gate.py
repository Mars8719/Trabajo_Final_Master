"""
Ethical Gate — Interceptor Normativo Pre-Ejecución (Sección 10 del Prompt Maestro)

Interceptor que valida cada acción del LLM-SOC antes de su ejecución.
Calcula scores GDPR + NIS2 + Bias ponderados, clasifica en 4 niveles
y bloquea automáticamente acciones con score < 0.40.

Pesos: GDPR 40% | NIS2 40% | Bias/AI Act 20%
Umbrales:
  BLOCKED   < 0.40  → Acción cancelada automáticamente
  VIOLATION 0.40-0.59 → Escalación DPO, remediación 48h
  WARNING   0.60-0.84 → Alerta GRC, revisión semanal
  COMPLIANT >= 0.85  → Registro normal
"""
import hashlib
import time
import structlog
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

logger = structlog.get_logger()


class ComplianceLevel(str, Enum):
    COMPLIANT = "COMPLIANT"   # GREEN  >= 0.85
    WARNING = "WARNING"       # AMBER  0.60-0.84
    VIOLATION = "VIOLATION"   # RED    0.40-0.59
    BLOCKED = "BLOCKED"       # BLACK  < 0.40


class ComplianceViolationError(Exception):
    """Raised when an action is blocked by the Ethical Gate (score < 0.40)."""

    def __init__(self, record: "EthicalAuditRecord"):
        self.record = record
        super().__init__(
            f"Action BLOCKED by Ethical Gate: composite={record.composite_score:.3f}, "
            f"level={record.level.value}"
        )


@dataclass
class EthicalAuditRecord:
    timestamp: float
    agent_id: str
    action_type: str
    gdpr_score: float
    nis2_score: float
    bias_score: float
    composite_score: float
    level: ComplianceLevel
    pii_detected: bool
    human_review_required: bool
    details: dict = field(default_factory=dict)
    previous_hash: str = ""
    audit_hash: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["level"] = self.level.value
        return d


class EthicalGate:
    """
    Interceptor normativo que evalúa cada acción LLM contra GDPR, NIS2 y Bias/AI Act.
    Genera registros inmutables (EthicalAuditRecord) con hash chain SHA-256.
    """

    # Pesos del composite score
    WEIGHT_GDPR = 0.40
    WEIGHT_NIS2 = 0.40
    WEIGHT_BIAS = 0.20

    # Umbrales de clasificación
    THRESHOLD_COMPLIANT = 0.85
    THRESHOLD_WARNING = 0.60
    THRESHOLD_VIOLATION = 0.40

    def __init__(self):
        self._last_hash = "0" * 64  # Genesis hash

    def evaluate(
        self,
        agent_id: str,
        action_type: str,
        gdpr_score: float,
        nis2_score: float,
        bias_score: float,
        pii_detected: bool = False,
        context: Optional[dict] = None,
    ) -> EthicalAuditRecord:
        """
        Evalúa una acción del LLM-SOC antes de su ejecución.

        Args:
            agent_id: Identificador del agente que ejecuta la acción.
            action_type: Tipo de acción evaluada.
            gdpr_score: Score GDPR normalizado 0.0 - 1.0.
            nis2_score: Score NIS2 normalizado 0.0 - 1.0.
            bias_score: Score Bias/AI Act normalizado 0.0 - 1.0.
            pii_detected: Si se detectó PII en la acción.
            context: Contexto adicional de la acción.

        Returns:
            EthicalAuditRecord con el resultado de la evaluación.

        Raises:
            ComplianceViolationError: Si el composite score < 0.40 (BLOCKED).
        """
        # Calcular composite ponderado
        composite = (
            self.WEIGHT_GDPR * gdpr_score
            + self.WEIGHT_NIS2 * nis2_score
            + self.WEIGHT_BIAS * bias_score
        )

        # Clasificar nivel
        level = self._classify(composite)

        # Determinar si requiere revisión humana
        human_review = (
            level in (ComplianceLevel.VIOLATION, ComplianceLevel.BLOCKED)
            or pii_detected
        )

        # Crear registro
        record = EthicalAuditRecord(
            timestamp=time.time(),
            agent_id=agent_id,
            action_type=action_type,
            gdpr_score=round(gdpr_score, 4),
            nis2_score=round(nis2_score, 4),
            bias_score=round(bias_score, 4),
            composite_score=round(composite, 4),
            level=level,
            pii_detected=pii_detected,
            human_review_required=human_review,
            details=context or {},
            previous_hash=self._last_hash,
        )

        # Hash chain SHA-256 inmutable
        record.audit_hash = self._compute_hash(record)
        self._last_hash = record.audit_hash

        logger.info(
            "EthicalGate evaluation",
            agent_id=agent_id,
            action_type=action_type,
            composite=composite,
            level=level.value,
            blocked=level == ComplianceLevel.BLOCKED,
        )

        # Bloquear si score < VIOLATION threshold
        if level == ComplianceLevel.BLOCKED:
            raise ComplianceViolationError(record)

        return record

    def _classify(self, composite: float) -> ComplianceLevel:
        if composite >= self.THRESHOLD_COMPLIANT:
            return ComplianceLevel.COMPLIANT
        elif composite >= self.THRESHOLD_WARNING:
            return ComplianceLevel.WARNING
        elif composite >= self.THRESHOLD_VIOLATION:
            return ComplianceLevel.VIOLATION
        else:
            return ComplianceLevel.BLOCKED

    def _compute_hash(self, record: EthicalAuditRecord) -> str:
        payload = (
            f"{record.timestamp}|{record.agent_id}|{record.action_type}|"
            f"{record.gdpr_score}|{record.nis2_score}|{record.bias_score}|"
            f"{record.composite_score}|{record.level.value}|"
            f"{record.pii_detected}|{record.previous_hash}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
