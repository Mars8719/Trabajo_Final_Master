"""
DPIA API - Automated Data Protection Impact Assessment (GDPR Art. 35).
POST /api/v1/dpia/generate - Generar DPIA automatizada
GET  /api/v1/dpia/{id}/risk-matrix - Matriz de riesgos
GET  /api/v1/dpia/list - Listar DPIAs
"""
from uuid import UUID
from datetime import datetime, timedelta, UTC
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database import get_db
from app.models.db.dpia_report import DPIAReport, DPIAStatus
from app.models.schemas.schemas import DPIAGenerate, DPIAResponse
from app.core.reporting.dpia_engine import DPIAEngine
from app.core.audit_module.audit_logger import audit_logger

router = APIRouter()
dpia_engine = DPIAEngine()


@router.post("/generate", response_model=DPIAResponse, status_code=201)
async def generate_dpia(data: DPIAGenerate, db: AsyncSession = Depends(get_db)):
    """Generate an automated DPIA report (GDPR Art. 35)."""
    report_data = dpia_engine.generate_dpia(data.system_description)

    dpia = DPIAReport(
        version=report_data["version"],
        status=DPIAStatus.DRAFT,
        system_description=data.system_description,
        data_flows=report_data["data_flows"],
        risks=report_data["risks"],
        technical_measures=report_data.get("technical_measures"),
        organizational_measures=report_data.get("organizational_measures"),
        rights_mechanisms=report_data.get("rights_mechanisms"),
        next_review_at=datetime.now(UTC) + timedelta(days=90),
    )
    db.add(dpia)
    await db.flush()

    await audit_logger.log(
        actor="system",
        action="dpia.generated",
        details={"dpia_id": str(dpia.id), "risks_count": len(report_data["risks"])},
        gdpr_articles=["Art. 35"],
        session=db,
    )

    return dpia


@router.get("/list", response_model=list[DPIAResponse])
async def list_dpias(db: AsyncSession = Depends(get_db)):
    """List all DPIA reports."""
    result = await db.execute(
        select(DPIAReport).order_by(DPIAReport.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{dpia_id}/risk-matrix")
async def get_risk_matrix(dpia_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get the risk matrix for a specific DPIA."""
    result = await db.execute(select(DPIAReport).where(DPIAReport.id == str(dpia_id)))
    dpia = result.scalar_one_or_none()
    if not dpia:
        raise HTTPException(status_code=404, detail="DPIA not found")

    # Build risk matrix from stored risks
    risks = dpia.risks or []
    matrix = {
        "dpia_id": str(dpia.id),
        "version": dpia.version,
        "status": dpia.status.value if dpia.status else "draft",
        "risks": risks,
        "matrix": {
            "very_high": [r for r in risks if r.get("inherent_score", 0) >= 12],
            "high": [r for r in risks if 8 <= r.get("inherent_score", 0) < 12],
            "medium": [r for r in risks if 4 <= r.get("inherent_score", 0) < 8],
            "low": [r for r in risks if r.get("inherent_score", 0) < 4],
        },
        "requires_authority_consultation": any(
            r.get("inherent_score", 0) >= 12 for r in risks
        ),
    }

    return matrix
