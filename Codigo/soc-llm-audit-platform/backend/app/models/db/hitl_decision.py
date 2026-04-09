"""
HITL Decision model - Human-in-the-Loop decisions with HOJR
(Human Oversight Justification Record).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean, ForeignKey, Enum as SAEnum, JSON

UTC = timezone.utc
from sqlalchemy.orm import relationship
import enum

from app.infrastructure.database import Base


class EscalationLevel(str, enum.Enum):
    L0_AUTO = "L0"
    L1_ASYNC = "L1"
    L2_SYNC = "L2"
    L3_MANDATORY = "L3"
    L4_KILL = "L4"


class DecisionType(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    MODIFIED = "modified"


class HITLDecision(Base):
    __tablename__ = "hitl_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36), ForeignKey("alerts.id"), nullable=False, index=True)
    escalation_level = Column(SAEnum(EscalationLevel), nullable=False)
    reviewer_id = Column(String(100))
    reviewer_role = Column(String(50))
    decision = Column(SAEnum(DecisionType), nullable=False)
    justification = Column(Text, nullable=False)
    alternatives_considered = Column(JSON)
    time_to_decision_seconds = Column(Integer)
    shap_viewed = Column(Boolean, default=False)
    lime_viewed = Column(Boolean, default=False)
    cs_at_review = Column(Float)
    confidence_at_review = Column(Float)
    anti_rubber_stamp_check = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)

    # Relationships
    alert = relationship("Alert", back_populates="hitl_decisions")
