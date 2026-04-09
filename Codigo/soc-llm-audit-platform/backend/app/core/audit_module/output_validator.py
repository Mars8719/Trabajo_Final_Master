"""
Output Validator - Filters PII, secrets, and non-compliant content
before delivering to the analyst.
"""
import re
import structlog
from dataclasses import dataclass
from typing import Optional

logger = structlog.get_logger()


@dataclass
class ValidationResult:
    is_valid: bool
    original_output: str
    sanitized_output: str
    blocked: bool
    violations: list[str]
    pii_leaked: bool
    secrets_leaked: bool


class OutputValidator:
    """Validates and sanitizes LLM output before delivery to analysts."""

    # Patterns for secrets detection
    SECRET_PATTERNS = [
        (r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"]?[\w\-]{20,}", "API Key"),
        (r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]?[^\s'\"]{8,}", "Password"),
        (r"(?i)(secret|token)\s*[=:]\s*['\"]?[\w\-]{20,}", "Secret/Token"),
        (r"(?i)bearer\s+[\w\-.~+/]+=*", "Bearer Token"),
        (r"-----BEGIN\s+(RSA\s+)?PRIVATE KEY-----", "Private Key"),
        (r"(?i)aws[_-]?(access[_-]?key|secret)", "AWS Credential"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Token"),
    ]

    # PII patterns for post-LLM leak detection
    PII_PATTERNS = [
        (r"\b\d{8}[A-Z]\b", "DNI español"),
        (r"\b[XYZ]\d{7}[A-Z]\b", "NIE español"),
        (r"\b[A-Z]{2}\d{2}\s?\d{4}\s?\d{4}\s?\d{2}\s?\d{10}\b", "IBAN"),
        (r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "Email"),
        (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "Phone US"),
        (r"\b\+?\d{1,3}[-.\s]?\d{6,12}\b", "Phone Intl"),
        (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "Credit Card"),
    ]

    # Prompt injection attempt patterns
    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?previous\s+instructions",
        r"(?i)you\s+are\s+now\s+(a|an)",
        r"(?i)system\s*prompt",
        r"(?i)forget\s+(all|everything)",
        r"(?i)override\s+safety",
        r"(?i)jailbreak",
        r"(?i)DAN\s+mode",
        r"(?i)do\s+anything\s+now",
    ]

    def validate(self, output: str, context: Optional[dict] = None) -> ValidationResult:
        """Validate LLM output for PII, secrets, and compliance."""
        violations = []
        sanitized = output
        pii_leaked = False
        secrets_leaked = False

        # Check for secrets
        for pattern, secret_type in self.SECRET_PATTERNS:
            if re.search(pattern, output):
                violations.append(f"Secreto detectado: {secret_type}")
                sanitized = re.sub(pattern, f"<{secret_type.upper()}_REDACTED>", sanitized)
                secrets_leaked = True

        # Check for PII leaks
        for pattern, pii_type in self.PII_PATTERNS:
            if re.search(pattern, output):
                violations.append(f"PII filtrado: {pii_type}")
                sanitized = re.sub(pattern, f"<{pii_type.upper()}_REDACTED>", sanitized)
                pii_leaked = True

        # Check for prompt injection in output (LLM trying to inject)
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, output):
                violations.append("Intento de prompt injection en output")

        blocked = secrets_leaked or (pii_leaked and not (context or {}).get("pii_allowed", False))

        if violations:
            logger.warning(
                "Output validation violations",
                violations=violations,
                blocked=blocked,
            )

        return ValidationResult(
            is_valid=len(violations) == 0,
            original_output=output,
            sanitized_output=sanitized,
            blocked=blocked,
            violations=violations,
            pii_leaked=pii_leaked,
            secrets_leaked=secrets_leaked,
        )


# Singleton
output_validator = OutputValidator()
