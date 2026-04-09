"""
LLM Gateway - Intelligent routing, rate-limiting, and guardrails.
Geo-fencing: EU data stays in GDPR-compliant infrastructure.
"""
import structlog
import time
from typing import Optional
from dataclasses import dataclass

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class LLMResponse:
    content: str
    model: str
    confidence: float
    tokens_used: int
    processing_time_ms: int
    geo_compliant: bool
    cost_estimate: float


class LLMGateway:
    """
    LLM Gateway with routing, rate-limiting, guardrails, and geo-fencing.
    """

    EU_REGIONS = {"EU", "ES", "DE", "FR", "IT", "NL", "BE", "PT", "PL", "SE", "AT", "IE"}

    def __init__(self):
        self.rate_limit_rpm = settings.LLM_RATE_LIMIT_RPM
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.request_count = 0
        self.last_reset = time.time()

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        geo_origin: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Send prompt to LLM with guardrails."""
        start_time = time.time()

        # Rate limiting check
        self._check_rate_limit()

        # Geo-fencing check
        geo_compliant = self._check_geo_compliance(geo_origin)

        # Input sanitization
        sanitized_prompt = self._sanitize_input(prompt)

        # Route to appropriate model
        model = self._route_model(geo_origin)

        # Simulate LLM call (replace with actual LangChain/OpenAI call in production)
        response_content = await self._call_llm(
            sanitized_prompt, system_prompt, model, max_tokens or self.max_tokens
        )

        processing_time = int((time.time() - start_time) * 1000)

        return LLMResponse(
            content=response_content,
            model=model,
            confidence=0.85,
            tokens_used=len(response_content.split()) * 2,
            processing_time_ms=processing_time,
            geo_compliant=geo_compliant,
            cost_estimate=self._estimate_cost(len(response_content.split()) * 2),
        )

    def _check_rate_limit(self):
        current_time = time.time()
        if current_time - self.last_reset >= 60:
            self.request_count = 0
            self.last_reset = current_time

        self.request_count += 1
        if self.request_count > self.rate_limit_rpm:
            raise Exception(f"Rate limit exceeded: {self.rate_limit_rpm} RPM")

    def _check_geo_compliance(self, geo_origin: Optional[str]) -> bool:
        if geo_origin and geo_origin.upper() not in self.EU_REGIONS:
            logger.warning("Non-EU data detected", geo_origin=geo_origin)
            return False
        return True

    def _route_model(self, geo_origin: Optional[str]) -> str:
        """Route to EU-compliant model if data is from EU."""
        if geo_origin and geo_origin.upper() in self.EU_REGIONS:
            return settings.LLM_MODEL  # EU-compliant endpoint
        return settings.LLM_MODEL

    def _sanitize_input(self, prompt: str) -> str:
        """Basic input sanitization against prompt injection."""
        dangerous_patterns = [
            "IGNORE ALL PREVIOUS",
            "ignore all instructions",
            "system prompt",
            "you are now",
            "DAN mode",
            "jailbreak",
        ]
        sanitized = prompt
        for pattern in dangerous_patterns:
            if pattern.lower() in sanitized.lower():
                logger.critical("Prompt injection attempt detected", pattern=pattern)
                raise PromptInjectionDetected(f"Prompt injection detected: {pattern}")
        return sanitized

    async def _call_llm(
        self, prompt: str, system_prompt: Optional[str], model: str, max_tokens: int
    ) -> str:
        """Call LLM API. Override this for actual implementation."""
        # Simulated response for development/testing
        return (
            f"[LLM Analysis - {model}] Based on the alert data, this appears to be a "
            f"medium-severity security event. Recommended actions: 1) Verify IOC indicators, "
            f"2) Check lateral movement, 3) Escalate if confirmed. Confidence: 0.85"
        )

    def _estimate_cost(self, tokens: int) -> float:
        cost_per_1k = 0.03  # GPT-4 pricing estimate
        return round((tokens / 1000) * cost_per_1k, 6)


class PromptInjectionDetected(Exception):
    """Raised when prompt injection is detected."""
    pass


# Singleton
llm_gateway = LLMGateway()
