"""
Incidents API - NIS2 Incident Reporting (24h/72h/1month).
POST /api/v1/incidents/report - Crear reporte NIS2
PUT  /api/v1/incidents/{id}/update - Update 72h / 1 mes
GET  /api/v1/incidents - Listar incidentes
"""
from uuid import UUID
from datetime import datetime, timedelta, UTC
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database import get_db
from app.models.db.incident import NIS2Incident, IncidentStatus, IncidentSeverity
from app.models.schemas.schemas import IncidentCreate, IncidentUpdate, IncidentResponse
from app.core.audit_module.audit_logger import audit_logger
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/report", response_model=IncidentResponse, status_code=201)
async def create_incident(data: IncidentCreate, db: AsyncSession = Depends(get_db)):
    """Create a NIS2 incident report with automatic deadline tracking."""
    now = datetime.now(UTC)

    severity_map = {
        "critical": IncidentSeverity.CRITICAL,
        "high": IncidentSeverity.HIGH,
        "medium": IncidentSeverity.MEDIUM,
        "low": IncidentSeverity.LOW,
    }

    incident = NIS2Incident(
        alert_ids=[str(a) for a in data.alert_ids] if data.alert_ids else [],
        incident_type=data.incident_type,
        severity=severity_map.get(data.severity, IncidentSeverity.MEDIUM),
        description=data.description,
        preliminary_report={"description": data.description, "created_at": now.isoformat()},
        csirt_notified_at=now,
        preliminary_deadline=now + timedelta(hours=settings.NIS2_PRELIMINARY_DEADLINE_HOURS),
        detailed_deadline=now + timedelta(hours=settings.NIS2_DETAILED_DEADLINE_HOURS),
        final_deadline=now + timedelta(days=settings.NIS2_FINAL_DEADLINE_DAYS),
        status=IncidentStatus.PRELIMINARY_SENT,
        affected_services=data.affected_services,
    )
    db.add(incident)
    await db.flush()

    await audit_logger.log(
        actor="system",
        action="incident.created",
        details={
            "incident_id": str(incident.id),
            "type": data.incident_type,
            "severity": data.severity,
            "preliminary_deadline": incident.preliminary_deadline.isoformat(),
        },
        nis2_articles=["Art. 23"],
        session=db,
    )

    return incident


@router.put("/{incident_id}/update")
async def update_incident(
    incident_id: UUID,
    data: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update incident with 72h detailed or 1-month final report."""
    result = await db.execute(select(NIS2Incident).where(NIS2Incident.id == str(incident_id)))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if data.detailed_report:
        incident.detailed_report = data.detailed_report
        incident.status = IncidentStatus.DETAILED_SENT
    if data.final_report:
        incident.final_report = data.final_report
        incident.status = IncidentStatus.FINAL_SENT
    if data.remediation_actions:
        incident.remediation_actions = data.remediation_actions
    if data.status:
        status_map = {
            "closed": IncidentStatus.CLOSED,
            "detailed_sent": IncidentStatus.DETAILED_SENT,
            "final_sent": IncidentStatus.FINAL_SENT,
        }
        incident.status = status_map.get(data.status, incident.status)

    incident.updated_at = datetime.now(UTC)

    await audit_logger.log(
        actor="soc_lead",
        action="incident.updated",
        details={"incident_id": str(incident_id), "new_status": incident.status.value},
        nis2_articles=["Art. 23"],
        session=db,
    )

    return {"status": "updated", "incident_id": str(incident_id)}


@router.get("/", response_model=list[IncidentResponse])
async def list_incidents(db: AsyncSession = Depends(get_db)):
    """List all NIS2 incidents."""
    result = await db.execute(
        select(NIS2Incident).order_by(NIS2Incident.created_at.desc())
    )
    return result.scalars().all()
