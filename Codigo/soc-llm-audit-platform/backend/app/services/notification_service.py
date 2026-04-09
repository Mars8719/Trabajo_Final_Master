"""
Notification Service - Alerts and compliance notifications.
"""
import structlog
from datetime import datetime, UTC
from typing import Optional

logger = structlog.get_logger()


class NotificationService:
    """Handles notification delivery for compliance events."""

    async def notify_grc_lead(self, subject: str, details: dict):
        """Notify GRC lead for attention-level compliance issues (CS 70-89)."""
        logger.info("GRC Lead notification", subject=subject, details=details)

    async def notify_dpo(self, subject: str, details: dict):
        """Notify DPO for medium-risk compliance issues (CS 50-69)."""
        logger.warning("DPO notification", subject=subject, details=details)

    async def notify_csirt(self, subject: str, details: dict, deadline_hours: int = 24):
        """Notify CSIRT for NIS2 incident reporting (24h deadline)."""
        logger.critical("CSIRT notification", subject=subject, deadline_hours=deadline_hours)

    async def notify_soc_lead(self, subject: str, details: dict):
        """Notify SOC Lead for L3 mandatory escalation."""
        logger.warning("SOC Lead notification", subject=subject, details=details)

    async def send_kill_switch_alert(self, reason: str, activated_by: str):
        """Emergency notification for L4 Kill Switch activation."""
        logger.critical(
            "KILL SWITCH ALERT",
            reason=reason,
            activated_by=activated_by,
            timestamp=datetime.now(UTC).isoformat(),
        )


notification_service = NotificationService()
