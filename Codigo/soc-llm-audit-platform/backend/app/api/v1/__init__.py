"""
API v1 Router - All REST endpoints.
"""
from fastapi import APIRouter

from app.api.v1.alerts import router as alerts_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.hitl import router as hitl_router
from app.api.v1.audit import router as audit_router
from app.api.v1.dpia import router as dpia_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.bias import router as bias_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.drift import router as drift_router
from app.api.v1.finops import router as finops_router

router = APIRouter()

router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
router.include_router(compliance_router, prefix="/compliance", tags=["Compliance"])
router.include_router(hitl_router, prefix="/hitl", tags=["HITL"])
router.include_router(audit_router, prefix="/audit", tags=["Audit"])
router.include_router(dpia_router, prefix="/dpia", tags=["DPIA"])
router.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])
router.include_router(bias_router, prefix="/bias", tags=["Bias"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(drift_router, prefix="/drift", tags=["Drift"])
router.include_router(finops_router, prefix="/finops", tags=["FinOps"])
