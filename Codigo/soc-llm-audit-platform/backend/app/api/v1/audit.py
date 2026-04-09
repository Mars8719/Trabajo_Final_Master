"""
Audit Trail API - Query and export audit records.
GET /api/v1/audit/trail - Query audit trail
GET /api/v1/audit/export - Export for regulator
GET /api/v1/audit/verify - Verify hash chain integrity
"""
from typing import Optional
from datetime import datetime, UTC
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.core.audit_module.audit_logger import audit_logger
from app.models.schemas.schemas import AuditTrailQuery, AuditTrailResponse

router = APIRouter()


@router.get("/trail", response_model=list[AuditTrailResponse])
async def get_audit_trail(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    actor: Optional[str] = None,
    action: Optional[str] = None,
    alert_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    """Query the audit trail with filters and pagination."""
    records, total = await audit_logger.query(
        start_date=start_date,
        end_date=end_date,
        actor=actor,
        action=action,
        alert_id=alert_id,
        page=page,
        page_size=page_size,
    )

    return records


@router.get("/export")
async def export_audit_trail(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    format: str = Query("json", pattern="^(json|csv)$"),
):
    """Export audit trail for regulators (NIS2 Art. 23, GDPR Art. 30)."""
    records, total = await audit_logger.query(
        start_date=start_date,
        end_date=end_date,
        page=1,
        page_size=10000,
    )

    export_data = {
        "export_metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "total_records": total,
            "date_range": {
                "start": start_date.isoformat() if start_date else "all",
                "end": end_date.isoformat() if end_date else "all",
            },
            "format": format,
            "regulatory_compliance": ["GDPR Art. 30", "NIS2 Art. 23"],
        },
        "records": [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "actor": r.actor,
                "action": r.action,
                "details": r.details,
                "gdpr_articles": r.gdpr_articles,
                "nis2_articles": r.nis2_articles,
                "hash_chain": r.hash_chain,
            }
            for r in records
        ],
    }

    return JSONResponse(content=export_data)


@router.get("/verify")
async def verify_audit_integrity():
    """Verify audit trail hash chain integrity."""
    is_valid, broken_at = await audit_logger.verify_chain_integrity()

    return {
        "integrity_valid": is_valid,
        "broken_at_record_id": broken_at,
        "verified_at": datetime.now(UTC).isoformat(),
        "method": "SHA-256 hash chain",
    }
