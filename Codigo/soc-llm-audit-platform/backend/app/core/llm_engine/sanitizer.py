"""
Input Sanitizer - Anti-Prompt Injection with multi-layer validation.
OWASP LLM Top 10: LLM01 (Prompt Injection)
"""
import re
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class SanitizationResult:
    is_safe: bool
    original_input: str
    sanitized_input: str
    threats_detected: list[str]
    risk_score: float  # 0 = safe, 100 = definitely malicious


class InputSanitizer:
    """Multi-layer input sanitization for prompt injection prevention."""

    # Layer 1: Known injection patterns
    INJECTION_PATTERNS = [
        (r"(?i)ignore\s+(all\s+)?previous\s+(instructions?|prompts?|rules?)", "Direct injection: ignore previous"),
        (r"(?i)you\s+are\s+now\s+(a|an|the)\s+", "Role hijacking attempt"),
        (r"(?i)system\s*:\s*", "System prompt manipulation"),
        (r"(?i)forget\s+(all|everything|your)", "Memory manipulation"),
        (r"(?i)override\s+(all\s+)?safety", "Safety override attempt"),
        (r"(?i)jailbreak", "Jailbreak attempt"),
        (r"(?i)DAN\s+mode", "DAN mode activation"),
        (r"(?i)do\s+anything\s+now", "DAN variant"),
        (r"(?i)pretend\s+(you're|you\s+are|to\s+be)", "Identity spoofing"),
        (r"(?i)reveal\s+(your|the)\s+(system\s+)?prompt", "Prompt extraction"),
        (r"(?i)what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?)", "Prompt extraction"),
        (r"(?i)translate\s+the\s+above", "Exfiltration via translation"),
        (r"(?i)repeat\s+(everything|all)\s+above", "Content exfiltration"),
        (r"(?i)base64\s+(encode|decode)", "Encoding bypass"),
        (r"(?i)execute\s+(the\s+following|this)", "Code execution attempt"),
        (r"(?i)```\s*(python|bash|sh|javascript|sql)", "Code injection"),
    ]

    # Layer 2: Structural anomalies
    STRUCTURAL_CHECKS = [
        (r"[\x00-\x08\x0e-\x1f]", "Control characters detected"),
        (r"(.)\1{20,}", "Excessive character repetition"),
        (r"\b(sudo|rm\s+-rf|chmod|chown|wget|curl)\b", "System command injection"),
    ]

    def sanitize(self, input_text: str) -> SanitizationResult:
        """Multi-layer input sanitization."""
        threats = []
        risk_score = 0.0
        sanitized = input_text

        # Layer 1: Pattern matching
        for pattern, threat_name in self.INJECTION_PATTERNS:
            if re.search(pattern, input_text):
                threats.append(threat_name)
                risk_score += 25.0
                sanitized = re.sub(pattern, "[BLOCKED]", sanitized, flags=re.IGNORECASE)

        # Layer 2: Structural checks
        for pattern, threat_name in self.STRUCTURAL_CHECKS:
            if re.search(pattern, input_text):
                threats.append(threat_name)
                risk_score += 15.0

        # Layer 3: Length checks
        if len(input_text) > 10000:
            threats.append("Excessive input length (>10K chars)")
            risk_score += 10.0

        # Layer 4: Unicode homoglyph detection
        if self._detect_homoglyphs(input_text):
            threats.append("Unicode homoglyph detected (possible obfuscation)")
            risk_score += 20.0

        risk_score = min(100.0, risk_score)
        is_safe = risk_score < 25.0

        if not is_safe:
            logger.warning(
                "Input sanitization: threats detected",
                threats=threats,
                risk_score=risk_score,
            )

        return SanitizationResult(
            is_safe=is_safe,
            original_input=input_text,
            sanitized_input=sanitized,
            threats_detected=threats,
            risk_score=risk_score,
        )

    def _detect_homoglyphs(self, text: str) -> bool:
        """Detect Unicode homoglyphs that could bypass filters."""
        homoglyph_ranges = [
            (0x0400, 0x04FF),  # Cyrillic
            (0x2000, 0x206F),  # General punctuation
            (0xFF00, 0xFFEF),  # Halfwidth/fullwidth forms
        ]
        for char in text:
            code = ord(char)
            for start, end in homoglyph_ranges:
                if start <= code <= end:
                    return True
        return False


# Singleton
input_sanitizer = InputSanitizer()
