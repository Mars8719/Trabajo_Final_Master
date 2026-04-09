"""
DPIA Report model - GDPR Art. 35 Automated Data Protection Impact Assessment.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Boolean, Enum as SAEnum, JSON

UTC = timezone.utc
import enum

from app.infrastructure.database import Base


class DPIAStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REQUIRES_AUTHORITY = "requires_authority"
    REJECTED = "rejected"


class DPIAReport(Base):
    __tablename__ = "dpia_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String(20), default="1.0")
    status = Column(SAEnum(DPIAStatus), default=DPIAStatus.DRAFT)
    system_description = Column(Text, nullable=False)
    data_flows = Column(JSON, nullable=False)
    risks = Column(JSON, nullable=False)
    inherent_risk_score = Column(String(20))
    technical_measures = Column(JSON)
    organizational_measures = Column(JSON)
    rights_mechanisms = Column(JSON)
    residual_risk_score = Column(String(20))
    dpo_consulted = Column(Boolean, default=False)
    dpo_opinion = Column(Text)
    approved_by = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    next_review_at = Column(DateTime)
