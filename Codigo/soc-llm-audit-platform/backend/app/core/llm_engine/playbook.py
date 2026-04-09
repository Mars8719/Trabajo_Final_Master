"""
Playbook Recommender - Recommends response playbooks based on LLM analysis.
"""
import structlog
from dataclasses import dataclass

from app.core.llm_engine.gateway import llm_gateway

logger = structlog.get_logger()


@dataclass
class PlaybookRecommendation:
    playbook_id: str
    name: str
    description: str
    priority: int
    estimated_time_minutes: int
    steps: list[str]
    applicable_frameworks: list[str]


class PlaybookRecommender:
    """Recommends incident response playbooks using LLM."""

    PLAYBOOKS = {
        "PB-001": PlaybookRecommendation(
            playbook_id="PB-001", name="Malware Containment",
            description="Contención y erradicación de malware",
            priority=1, estimated_time_minutes=60,
            steps=["Aislar host", "Capturar memoria", "Escanear IOCs", "Restaurar de backup"],
            applicable_frameworks=["NIS2 Art.21", "OWASP"],
        ),
        "PB-002": PlaybookRecommendation(
            playbook_id="PB-002", name="Phishing Response",
            description="Respuesta a incidente de phishing",
            priority=2, estimated_time_minutes=45,
            steps=["Bloquear remitente", "Buscar más víctimas", "Reset credenciales", "Notificar usuarios"],
            applicable_frameworks=["NIS2 Art.23", "GDPR Art.33"],
        ),
        "PB-003": PlaybookRecommendation(
            playbook_id="PB-003", name="Data Exfiltration",
            description="Respuesta a exfiltración de datos",
            priority=1, estimated_time_minutes=90,
            steps=["Bloquear canal", "Evaluar datos expuestos", "Notificar DPO", "DPIA si PII", "Notificar CSIRT 24h"],
            applicable_frameworks=["GDPR Art.33-34", "NIS2 Art.23", "DORA"],
        ),
        "PB-004": PlaybookRecommendation(
            playbook_id="PB-004", name="Brute Force Mitigation",
            description="Mitigación de ataques de fuerza bruta",
            priority=2, estimated_time_minutes=30,
            steps=["Bloquear IP", "Verificar cuentas comprometidas", "Forzar MFA", "Revisar logs"],
            applicable_frameworks=["NIS2 Art.21"],
        ),
        "PB-005": PlaybookRecommendation(
            playbook_id="PB-005", name="Ransomware Response",
            description="Respuesta a incidente de ransomware",
            priority=1, estimated_time_minutes=120,
            steps=["Aislar red", "Preservar evidencia", "Evaluar impacto", "Notificar CSIRT <24h", "Plan de recuperación"],
            applicable_frameworks=["NIS2 Art.23", "DORA", "GDPR Art.33"],
        ),
    }

    async def recommend(self, classification: str, severity: float) -> list[PlaybookRecommendation]:
        """Recommend playbooks based on alert classification."""
        mapping = {
            "malware": ["PB-001"],
            "phishing": ["PB-002"],
            "data_exfiltration": ["PB-003"],
            "brute_force": ["PB-004"],
            "ransomware": ["PB-005"],
            "lateral_movement": ["PB-001", "PB-003"],
            "anomaly": ["PB-004"],
        }

        pb_ids = mapping.get(classification, ["PB-004"])
        return [self.PLAYBOOKS[pid] for pid in pb_ids if pid in self.PLAYBOOKS]


playbook_recommender = PlaybookRecommender()
