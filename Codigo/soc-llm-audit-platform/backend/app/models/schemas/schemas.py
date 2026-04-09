"""
Pydantic schemas for API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


# ─── Alert Schemas ───
class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertIngest(BaseModel):
    source: str = Field(..., max_length=100, description="Source SIEM/EDR/NDR")
    raw_payload: dict = Field(..., description="Raw alert payload in JSON")
    severity_original: Optional[str] = None
    geo_origin: Optional[str] = Field(None, max_length=10)


class AlertResponse(BaseModel):
    id: UUID
    source: str
    severity_score: Optional[float]
    pii_score: Optional[float]
    compliance_score: Optional[float]
    llm_classification: Optional[str]
    llm_confidence: Optional[float]
    hitl_level: int
    hitl_status: str
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AlertDetail(AlertResponse):
    anonymized_payload: Optional[dict]
    llm_reasoning: Optional[str]
    data_sensitivity: Optional[str] = None
    processing_time_ms: Optional[int]


# ─── Compliance Score Schemas ───
class RiskLevel(str, Enum):
    COMPLIANT = "compliant"
    ATTENTION = "attention"
    MEDIUM_RISK = "medium_risk"
    NON_COMPLIANT = "non_compliant"


class ComplianceScoreResponse(BaseModel):
    id: UUID
    alert_id: UUID
    total_score: float
    data_minimization: float
    legal_basis: float
    transparency: float
    pipeline_security: float
    bias_fairness: float
    retention_compliance: float
    incident_reporting: float
    hitl_compliance: float
    risk_level: RiskLevel
    created_at: datetime

    class Config:
        from_attributes = True


class ComplianceDashboard(BaseModel):
    average_score: float
    total_alerts: int
    compliant_count: int
    attention_count: int
    medium_risk_count: int
    non_compliant_count: int
    trend_7d: list[float]
    top_violations: list[dict]


class ComplianceTrend(BaseModel):
    date: str
    average_score: float
    count: int


# ─── HITL Schemas ───
class EscalationLevel(str, Enum):
    L0_AUTO = "L0"
    L1_ASYNC = "L1"
    L2_SYNC = "L2"
    L3_MANDATORY = "L3"
    L4_KILL = "L4"


class HITLQueueItem(BaseModel):
    id: UUID
    alert_id: UUID
    escalation_level: EscalationLevel
    cs_at_review: Optional[float]
    confidence_at_review: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class HITLDecisionCreate(BaseModel):
    decision: str = Field(..., description="approved|rejected|escalated|modified")
    justification: str = Field(..., min_length=20, description="HOJR: justification required")
    alternatives_considered: Optional[dict] = None
    shap_viewed: bool = False
    lime_viewed: bool = False


class HITLKillSwitch(BaseModel):
    reason: str = Field(..., min_length=10)
    activated_by: str


# ─── Audit Trail Schemas ───
class AuditTrailQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    actor: Optional[str] = None
    action: Optional[str] = None
    alert_id: Optional[UUID] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)


class AuditTrailResponse(BaseModel):
    id: str
    timestamp: datetime
    alert_id: Optional[UUID]
    actor: str
    action: str
    details: Optional[dict]
    gdpr_articles: list[str]
    nis2_articles: list[str]
    hash_chain: str

    class Config:
        from_attributes = True


# ─── DPIA Schemas ───
class DPIAGenerate(BaseModel):
    system_description: str = Field(..., min_length=50)
    include_data_flows: bool = True
    include_risk_matrix: bool = True


class DPIAResponse(BaseModel):
    id: UUID
    version: str
    status: str
    system_description: str
    data_flows: Optional[dict] = None
    risks: Optional[list | dict] = None
    technical_measures: Optional[dict]
    organizational_measures: Optional[dict]
    rights_mechanisms: Optional[dict]
    dpo_consulted: bool
    created_at: datetime
    next_review_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Incident Schemas ───
class IncidentCreate(BaseModel):
    alert_ids: list[UUID] = []
    incident_type: str = Field(..., max_length=100)
    severity: str
    description: str = Field(..., min_length=20)
    affected_services: Optional[dict] = None


class IncidentUpdate(BaseModel):
    detailed_report: Optional[dict] = None
    final_report: Optional[dict] = None
    remediation_actions: Optional[dict] = None
    status: Optional[str] = None


class IncidentResponse(BaseModel):
    id: UUID
    incident_type: str
    severity: str
    status: str
    description: Optional[str] = None
    csirt_notified_at: Optional[datetime]
    preliminary_deadline: Optional[datetime]
    detailed_deadline: Optional[datetime]
    final_deadline: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Bias Schemas ───
class BiasTestRun(BaseModel):
    dimension: str = Field(..., description="geographic|temporal|linguistic|severity|source")
    test_name: str
    input_data: dict


class BiasTestResponse(BaseModel):
    id: UUID
    dimension: str
    test_name: str
    adverse_impact_ratio: Optional[float]
    passed: Optional[bool]
    threshold: float
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Drift Schemas ───
class DriftStatus(BaseModel):
    model_drift: float
    data_drift: float
    concept_drift: float
    prediction_drift: float
    provider_drift: float
    overall_status: str
    last_checked: datetime


# ─── FinOps Schemas ───
class FinOpsCosts(BaseModel):
    total_cost_30d: float
    cost_per_inference: float
    total_inferences: int
    model_breakdown: list[dict]
    budget_remaining: float
    budget_utilization_pct: float


# ─── Explainability Schemas ───
class ExplanationResponse(BaseModel):
    alert_id: UUID
    shap_values: Optional[dict]
    lime_explanation: Optional[dict]
    narrative: str
    confidence: float
    features_importance: list[dict]
