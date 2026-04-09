"""
NIS2 Incident model - Incident reporting with 24h/72h/1month deadlines.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Enum as SAEnum, JSON

UTC = timezone.utc
import enum

from app.infrastructure.database import Base


class IncidentSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, enum.Enum):
    DETECTED = "detected"
    PRELIMINARY_SENT = "preliminary_sent"
    DETAILED_SENT = "detailed_sent"
    FINAL_SENT = "final_sent"
    CLOSED = "closed"


class NIS2Incident(Base):
    __tablename__ = "nis2_incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_ids = Column(JSON, default=list)
    incident_type = Column(String(100), nullable=False)
    severity = Column(SAEnum(IncidentSeverity), nullable=False)
    description = Column(Text, nullable=False)
    preliminary_report = Column(JSON)  # 24h
    detailed_report = Column(JSON)     # 72h
    final_report = Column(JSON)        # 1 month
    csirt_notified_at = Column(DateTime)
    preliminary_deadline = Column(DateTime)
    detailed_deadline = Column(DateTime)
    final_deadline = Column(DateTime)
    status = Column(SAEnum(IncidentStatus), default=IncidentStatus.DETECTED)
    affected_services = Column(JSON)
    impact_assessment = Column(JSON)
    remediation_actions = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
