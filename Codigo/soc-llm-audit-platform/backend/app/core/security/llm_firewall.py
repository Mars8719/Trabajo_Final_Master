"""
LLM Firewall - Runtime protection against LLM attacks.
OWASP LLM Top 10 coverage.
"""
import re
import time
import structlog
from dataclasses import dataclass
from typing import Optional
from collections import defaultdict

logger = structlog.get_logger()


@dataclass
class FirewallVerdict:
    allowed: bool
    risk_level: str  # safe, suspicious, blocked
    threats: list[str]
    latency_ms: int


class LLMFirewall:
    """Runtime LLM Firewall for input/output protection."""

    def __init__(self):
        self._request_log: dict[str, list[float]] = defaultdict(list)
        self._blocked_patterns = set()
        self._max_requests_per_minute = 60

    def inspect_input(self, text: str, source_ip: Optional[str] = None) -> FirewallVerdict:
        """Inspect input before sending to LLM."""
        start = time.time()
        threats = []

        # Rate limiting per source
        if source_ip:
            now = time.time()
            self._request_log[source_ip] = [
                t for t in self._request_log[source_ip] if now - t < 60
            ]
            if len(self._request_log[source_ip]) >= self._max_requests_per_minute:
                threats.append("Rate limit exceeded")
            self._request_log[source_ip].append(now)

        # Token injection detection
        injection_patterns = [
            r"(?i)\bignore\b.*\b(previous|all)\b.*\b(instructions?|prompts?)\b",
            r"(?i)\bignore\b.*\b(previous|above|all)\b",
            r"(?i)\b(system|assistant)\s*:",
            r"(?i)\bjailbreak\b",
            r"(?i)\bDAN\s+mode\b",
            r"(?i)\bdo\s+anything\s+now\b",
            r"(?i)\bpretend\s+(to\s+be|you're)\b",
            r"(?i)\breveal\b.*\bprompt\b",
            r"(?i)(rm\s+-rf|del\s+/[sfq]|format\s+c:)",
        ]

        for pattern in injection_patterns:
            if re.search(pattern, text):
                threats.append(f"Injection pattern: {pattern[:50]}")

        # Payload size check
        if len(text) > 50000:
            threats.append("Oversized payload")

        # Encoding attacks
        if any(ord(c) > 0xFFFF for c in text):
            threats.append("Suspicious Unicode characters")

        latency = int((time.time() - start) * 1000)

        if threats:
            risk_level = "blocked" if any("injection" in t.lower() for t in threats) else "suspicious"
        else:
            risk_level = "safe"

        return FirewallVerdict(
            allowed=risk_level != "blocked",
            risk_level=risk_level,
            threats=threats,
            latency_ms=latency,
        )

    def inspect_output(self, text: str) -> FirewallVerdict:
        """Inspect LLM output before delivery."""
        start = time.time()
        threats = []

        # Check for leaked system prompts
        system_prompt_indicators = [
            r"(?i)my\s+system\s+prompt\s+is",
            r"(?i)i\s+was\s+instructed\s+to",
            r"(?i)my\s+instructions\s+are",
        ]
        for pattern in system_prompt_indicators:
            if re.search(pattern, text):
                threats.append("Potential system prompt leak")

        # Check for harmful content generation
        harmful_patterns = [
            r"(?i)\b(execute|run)\s+this\s+(command|code|script)\b",
            r"(?i)sudo\s+rm\s+-rf",
        ]
        for pattern in harmful_patterns:
            if re.search(pattern, text):
                threats.append("Potentially harmful output")

        latency = int((time.time() - start) * 1000)

        return FirewallVerdict(
            allowed=len(threats) == 0,
            risk_level="blocked" if threats else "safe",
            threats=threats,
            latency_ms=latency,
        )


llm_firewall = LLMFirewall()
