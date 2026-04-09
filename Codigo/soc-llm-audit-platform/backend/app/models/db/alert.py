"""
Alert model - Core entity for SOC alert pipeline.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Enum as SAEnum, JSON

UTC = timezone.utc
from sqlalchemy.orm import relationship
import enum

from app.infrastructure.database import Base


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class HITLStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    AUTO_PROCESSED = "auto_processed"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(100), nullable=False, index=True)
    raw_payload = Column(JSON, nullable=False)
    anonymized_payload = Column(JSON)
    severity_original = Column(String(20))
    severity_score = Column(Float)
    pii_score = Column(Float, default=0.0)
    compliance_score = Column(Float)
    llm_classification = Column(String(100))
    llm_confidence = Column(Float)
    llm_reasoning = Column(Text)
    hitl_level = Column(Integer, default=0)
    hitl_status = Column(
        SAEnum(HITLStatus), default=HITLStatus.PENDING
    )
    geo_origin = Column(String(10))
    data_sensitivity = Column(String(20), default="internal")
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    processed_at = Column(DateTime)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    compliance_scores = relationship("ComplianceScore", back_populates="alert")
    hitl_decisions = relationship("HITLDecision", back_populates="alert")
    audit_records = relationship("AuditRecord", back_populates="alert")
