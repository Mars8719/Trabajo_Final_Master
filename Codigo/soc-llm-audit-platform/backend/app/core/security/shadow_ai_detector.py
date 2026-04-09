"""
Shadow AI Detector - Detects unauthorized AI tool usage.
AI Tool Registry + DLP for AI interactions.
"""
import structlog
from datetime import datetime, UTC
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class ShadowAIDetection:
    detected: bool
    tool_name: str
    risk_level: str
    details: str
    timestamp: str


class ShadowAIDetector:
    """Detects unauthorized AI tool usage within the organization."""

    # Approved AI tools registry
    APPROVED_TOOLS = {
        "soc-llm-triage": {"version": "1.0", "approved_by": "CISO", "risk_level": "low"},
        "soc-llm-playbook": {"version": "1.0", "approved_by": "CISO", "risk_level": "low"},
        "soc-llm-summary": {"version": "1.0", "approved_by": "CISO", "risk_level": "low"},
    }

    # Known shadow AI indicators
    SHADOW_AI_INDICATORS = [
        "chatgpt.com",
        "chat.openai.com",
        "bard.google.com",
        "claude.ai",
        "api.openai.com",
        "api.anthropic.com",
        "huggingface.co/api",
    ]

    def check_tool(self, tool_name: str) -> ShadowAIDetection:
        """Check if an AI tool is in the approved registry."""
        if tool_name in self.APPROVED_TOOLS:
            return ShadowAIDetection(
                detected=False,
                tool_name=tool_name,
                risk_level="approved",
                details=f"Tool {tool_name} is in the approved registry",
                timestamp=datetime.now(UTC).isoformat(),
            )

        logger.warning("Shadow AI tool detected", tool=tool_name)
        return ShadowAIDetection(
            detected=True,
            tool_name=tool_name,
            risk_level="high",
            details=f"Unauthorized AI tool '{tool_name}' detected. Not in approved registry.",
            timestamp=datetime.now(UTC).isoformat(),
        )

    def scan_network_traffic(self, urls: list[str]) -> list[ShadowAIDetection]:
        """Scan network traffic for shadow AI usage indicators."""
        detections = []
        for url in urls:
            for indicator in self.SHADOW_AI_INDICATORS:
                if indicator in url.lower():
                    detections.append(ShadowAIDetection(
                        detected=True,
                        tool_name=indicator,
                        risk_level="high",
                        details=f"Shadow AI traffic detected to {indicator}",
                        timestamp=datetime.now(UTC).isoformat(),
                    ))
        return detections

    def get_tool_registry(self) -> dict:
        """Return the approved AI tool registry."""
        return self.APPROVED_TOOLS


shadow_ai_detector = ShadowAIDetector()
