"""
Compliance Score model - Scoring compuesto 0-100 por transacción.
CS = Σ(wi × si) donde Σ(wi) = 1.0
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum as SAEnum

UTC = timezone.utc
from sqlalchemy.orm import relationship
import enum

from app.infrastructure.database import Base


class RiskLevel(str, enum.Enum):
    COMPLIANT = "compliant"          # 90-100
    ATTENTION = "attention"          # 70-89
    MEDIUM_RISK = "medium_risk"      # 50-69
    NON_COMPLIANT = "non_compliant"  # < 50


class ComplianceScore(Base):
    __tablename__ = "compliance_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36), ForeignKey("alerts.id"), nullable=False, index=True)
    total_score = Column(Float, nullable=False)
    data_minimization = Column(Float, default=0.0)
    legal_basis = Column(Float, default=0.0)
    transparency = Column(Float, default=0.0)
    pipeline_security = Column(Float, default=0.0)
    bias_fairness = Column(Float, default=0.0)
    retention_compliance = Column(Float, default=0.0)
    incident_reporting = Column(Float, default=0.0)
    hitl_compliance = Column(Float, default=0.0)
    risk_level = Column(SAEnum(RiskLevel), nullable=False)
    details = Column(String(500))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)

    # Relationships
    alert = relationship("Alert", back_populates="compliance_scores")
