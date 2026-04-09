"""
Audit Trail Logger - Registro inmutable (append-only) con hash chain.
Integridad criptográfica SHA-256. Retención 7 años (SOX).
"""
import hashlib
import json
import structlog
from datetime import datetime, UTC
from typing import Optional, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.db.audit_record import AuditRecord
from app.infrastructure.database import async_session

logger = structlog.get_logger()


class AuditTrailLogger:
    """Append-only audit trail with cryptographic hash chain."""

    def __init__(self):
        self._last_hash: Optional[str] = None

    def _compute_hash(self, data: dict, previous_hash: str = "") -> str:
        """Compute SHA-256 hash for chain integrity."""
        content = json.dumps(data, sort_keys=True, default=str) + previous_hash
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def _get_last_hash(self, session: AsyncSession) -> str:
        """Get the hash of the last audit record for chain continuity."""
        result = await session.execute(
            select(AuditRecord.hash_chain)
            .order_by(AuditRecord.timestamp.desc())
            .limit(1)
        )
        last = result.scalar_one_or_none()
        return last or hashlib.sha256(b"GENESIS_BLOCK").hexdigest()

    async def log(
        self,
        actor: str,
        action: str,
        details: Optional[dict] = None,
        alert_id: Optional[Union[UUID, str]] = None,
        gdpr_articles: Optional[list[str]] = None,
        nis2_articles: Optional[list[str]] = None,
        session: Optional[AsyncSession] = None,
    ) -> AuditRecord:
        """Create an immutable audit record with hash chain.
        If session is provided, uses it (no commit). Otherwise creates its own.
        """
        if session is not None:
            return await self._log_in_session(
                session, actor, action, details, alert_id, gdpr_articles, nis2_articles
            )
        async with async_session() as own_session:
            record = await self._log_in_session(
                own_session, actor, action, details, alert_id, gdpr_articles, nis2_articles
            )
            await own_session.commit()
            await own_session.refresh(record)
            return record

    async def _log_in_session(
        self,
        session: AsyncSession,
        actor: str,
        action: str,
        details: Optional[dict],
        alert_id: Optional[Union[UUID, str]],
        gdpr_articles: Optional[list[str]],
        nis2_articles: Optional[list[str]],
    ) -> AuditRecord:
        previous_hash = await self._get_last_hash(session)

        alert_id_str = str(alert_id) if alert_id else None
        now = datetime.now(UTC)

        record_data = {
            "timestamp": now.isoformat(),
            "actor": actor,
            "action": action,
            "details": details or {},
            "alert_id": alert_id_str,
        }

        current_hash = self._compute_hash(record_data, previous_hash)

        record = AuditRecord(
            timestamp=now,
            alert_id=alert_id_str,
            actor=actor,
            action=action,
            details=details,
            gdpr_articles=gdpr_articles or [],
            nis2_articles=nis2_articles or [],
            hash_chain=current_hash,
            previous_hash=previous_hash,
        )

        session.add(record)

        logger.info(
            "Audit record created",
            actor=actor,
            action=action,
            hash=current_hash[:16],
        )

        return record

    async def verify_chain_integrity(self) -> tuple[bool, Optional[int]]:
        """Verify the entire hash chain integrity. Returns (is_valid, broken_at_id)."""
        async with async_session() as session:
            result = await session.execute(
                select(AuditRecord).order_by(AuditRecord.timestamp.asc())
            )
            records = result.scalars().all()

            if not records:
                return True, None

            previous_hash = hashlib.sha256(b"GENESIS_BLOCK").hexdigest()

            for record in records:
                record_data = {
                    "timestamp": record.timestamp.isoformat() if record.timestamp else "",
                    "actor": record.actor,
                    "action": record.action,
                    "details": record.details or {},
                    "alert_id": str(record.alert_id) if record.alert_id else None,
                }
                expected_hash = self._compute_hash(record_data, previous_hash)

                if record.hash_chain != expected_hash:
                    logger.error(
                        "Hash chain integrity violation",
                        record_id=record.id,
                        expected=expected_hash[:16],
                        actual=record.hash_chain[:16],
                    )
                    return False, record.id

                previous_hash = record.hash_chain

            return True, None

    async def query(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        alert_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditRecord], int]:
        """Query audit trail with filters and pagination."""
        async with async_session() as session:
            query = select(AuditRecord)

            if start_date:
                query = query.where(AuditRecord.timestamp >= start_date)
            if end_date:
                query = query.where(AuditRecord.timestamp <= end_date)
            if actor:
                query = query.where(AuditRecord.actor == actor)
            if action:
                query = query.where(AuditRecord.action.ilike(f"%{action}%"))
            if alert_id:
                query = query.where(AuditRecord.alert_id == str(alert_id))

            # Count
            count_result = await session.execute(
                select(func.count()).select_from(query.subquery())
            )
            total = count_result.scalar()

            # Paginate
            query = query.order_by(AuditRecord.timestamp.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)

            result = await session.execute(query)
            records = result.scalars().all()

            return records, total


# Singleton
audit_logger = AuditTrailLogger()
