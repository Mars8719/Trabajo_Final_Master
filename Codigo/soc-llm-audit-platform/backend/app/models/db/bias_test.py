"""
Bias Test model - Ethical Bias & Fairness testing across 5 dimensions.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, Boolean, Enum as SAEnum, JSON

UTC = timezone.utc
import enum

from app.infrastructure.database import Base


class BiasDimension(str, enum.Enum):
    GEOGRAPHIC = "geographic"
    TEMPORAL = "temporal"
    LINGUISTIC = "linguistic"
    SEVERITY = "severity"
    SOURCE = "source"


class BiasTest(Base):
    __tablename__ = "bias_tests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dimension = Column(SAEnum(BiasDimension), nullable=False)
    test_name = Column(String(200), nullable=False)
    description = Column(Text)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON)
    adverse_impact_ratio = Column(Float)
    passed = Column(Boolean)
    threshold = Column(Float, default=0.8)
    details = Column(JSON)
    executed_by = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
