"""
Audit Record model - Registro inmutable (append-only) con hash chain.
Integridad criptográfica SHA-256.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, LargeBinary, JSON

UTC = timezone.utc
from sqlalchemy.orm import relationship

from app.infrastructure.database import Base


class AuditRecord(Base):
    __tablename__ = "audit_trail"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)
    alert_id = Column(String(36), ForeignKey("alerts.id"), index=True)
    actor = Column(String(100), nullable=False)
    action = Column(String(200), nullable=False)
    details = Column(JSON)
    gdpr_articles = Column(JSON, default=list)
    nis2_articles = Column(JSON, default=list)
    hash_chain = Column(String(64), nullable=False)  # SHA-256 hex
    previous_hash = Column(String(64))
    signature = Column(LargeBinary)

    # Relationships
    alert = relationship("Alert", back_populates="audit_records")
