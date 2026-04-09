"""
Fallback Manager - Graceful Degradation with 4 levels.

Level 0 (Full AI):  LLM + SHAP + HITL + CS complete (100% AI)
Level 1 (Reduced):  LLM only Critical/High, SOAR rest (30% AI) - Medium drift
Level 2 (Shadow):   LLM background, rule-based decisions (0% AI log) - High drift
Level 3 (Manual):   LLM disabled, playbooks + manual (0% AI) - Kill switch

RTO fallback: < 5 min, RPO: 0 (no alerts lost)
"""
import structlog
from datetime import datetime, UTC
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional

logger = structlog.get_logger()


class DegradationLevel(IntEnum):
    FULL_AI = 0
    REDUCED = 1
    SHADOW = 2
    MANUAL = 3


@dataclass
class FallbackStatus:
    level: DegradationLevel
    level_name: str
    ai_percentage: int
    trigger: str
    activated_at: Optional[str]
    description: str


class FallbackManager:
    """Manages graceful degradation of the LLM pipeline."""

    LEVEL_CONFIG = {
        DegradationLevel.FULL_AI: FallbackStatus(
            level=DegradationLevel.FULL_AI, level_name="Full AI",
            ai_percentage=100, trigger="Normal",
            activated_at=None,
            description="LLM + SHAP + HITL + CS completo",
        ),
        DegradationLevel.REDUCED: FallbackStatus(
            level=DegradationLevel.REDUCED, level_name="Reduced",
            ai_percentage=30, trigger="Medium drift",
            activated_at=None,
            description="LLM solo Critical/High, SOAR para el resto",
        ),
        DegradationLevel.SHADOW: FallbackStatus(
            level=DegradationLevel.SHADOW, level_name="Shadow",
            ai_percentage=0, trigger="High drift",
            activated_at=None,
            description="LLM en background, decisiones por reglas",
        ),
        DegradationLevel.MANUAL: FallbackStatus(
            level=DegradationLevel.MANUAL, level_name="Manual",
            ai_percentage=0, trigger="Kill switch",
            activated_at=None,
            description="LLM desactivado, playbooks + manual",
        ),
    }

    def __init__(self):
        self.current_level = DegradationLevel.FULL_AI
        self._activated_at: Optional[datetime] = None

    def get_status(self) -> FallbackStatus:
        """Get current degradation status."""
        status = self.LEVEL_CONFIG[self.current_level]
        if self._activated_at:
            status.activated_at = self._activated_at.isoformat()
        return status

    def set_level(self, level: DegradationLevel, reason: str = "") -> FallbackStatus:
        """Set degradation level."""
        old_level = self.current_level
        self.current_level = level
        self._activated_at = datetime.now(UTC)

        logger.warning(
            "Degradation level changed",
            old_level=old_level.name,
            new_level=level.name,
            reason=reason,
        )

        return self.get_status()

    def should_use_llm(self, severity: str = "medium") -> bool:
        """Determine if LLM should be used based on current degradation level."""
        if self.current_level == DegradationLevel.FULL_AI:
            return True
        elif self.current_level == DegradationLevel.REDUCED:
            return severity in ("critical", "high")
        return False

    def auto_assess_level(self, drift_score: float, error_rate: float) -> DegradationLevel:
        """Automatically assess appropriate degradation level."""
        if error_rate > 0.5 or drift_score > 0.8:
            return DegradationLevel.MANUAL
        elif error_rate > 0.3 or drift_score > 0.5:
            return DegradationLevel.SHADOW
        elif error_rate > 0.1 or drift_score > 0.3:
            return DegradationLevel.REDUCED
        return DegradationLevel.FULL_AI


fallback_manager = FallbackManager()
