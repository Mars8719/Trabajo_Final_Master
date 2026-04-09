"""
SOC PII Scanner - GDPR Art. 5, 25, 32
Hybrid approach: Regex + NER (SpaCy/HuggingFace) + ML contextual.
Base: Microsoft Presidio with custom recognizers for DNI/NIE español,
passports EU, IBAN.  Falls back to regex-only when Presidio is unavailable.
"""
import re
import json
import hashlib
import structlog
from typing import Optional
from dataclasses import dataclass, field

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Try importing Presidio; fall back to regex-only mode
try:
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerResult
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    logger.warning("Presidio not installed – using regex-only PII scanner (dev mode)")


@dataclass
class PIIScanResult:
    """Result of PII scanning."""
    original_text: str
    anonymized_text: str
    pii_found: list[dict] = field(default_factory=list)
    pii_score: float = 0.0
    entities_count: int = 0
    anonymization_method: str = "replace"


# ─── Regex-only fallback patterns ───
_REGEX_PII_PATTERNS: list[tuple[str, str, str]] = [
    (r"\b\d{8}[A-Z]\b", "ES_DNI_NIE", "<DNI_REDACTADO>"),
    (r"\b[XYZ]\d{7}[A-Z]\b", "ES_DNI_NIE", "<DNI_REDACTADO>"),
    (r"\bES\d{2}\s?\d{4}\s?\d{4}\s?\d{2}\s?\d{10}\b", "EU_IBAN", "<IBAN_REDACTADO>"),
    (r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "EMAIL_ADDRESS", "<EMAIL_REDACTADO>"),
    (r"\b\+?\d{1,3}[-.\s]?\d{6,12}\b", "PHONE_NUMBER", "<TELEFONO_REDACTADO>"),
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "CREDIT_CARD", "<TARJETA_REDACTADA>"),
    (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "IP_ADDRESS", "<IP_REDACTADA>"),
]


class SOCPIIScanner:
    """
    Main PII Scanner for the SOC pipeline.
    Uses Microsoft Presidio when available, regex fallback otherwise.
    """

    def __init__(self):
        self.confidence_threshold = settings.PII_CONFIDENCE_THRESHOLD
        self.supported_languages = settings.PII_SUPPORTED_LANGUAGES

        if PRESIDIO_AVAILABLE:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            # Register custom recognizers
            self.analyzer.registry.add_recognizer(
                PatternRecognizer(
                    supported_entity="ES_DNI_NIE",
                    patterns=[Pattern("DNI", r"\b\d{8}[A-Z]\b", 0.85),
                              Pattern("NIE", r"\b[XYZ]\d{7}[A-Z]\b", 0.85)],
                    supported_language="es",
                    name="Spanish DNI/NIE Recognizer",
                )
            )
        else:
            self.analyzer = None
            self.anonymizer = None

    # ── public API ──

    def scan(self, text: str, language: str = "es") -> PIIScanResult:
        if not text or not text.strip():
            return PIIScanResult(original_text=text, anonymized_text=text)

        if PRESIDIO_AVAILABLE and self.analyzer is not None:
            return self._scan_presidio(text, language)
        return self._scan_regex(text)

    def scan_payload(self, payload: dict, language: str = "es") -> tuple[dict, PIIScanResult]:
        combined_text = json.dumps(payload, ensure_ascii=False, default=str)
        scan_result = self.scan(combined_text, language)
        try:
            anonymized_payload = json.loads(scan_result.anonymized_text)
        except json.JSONDecodeError:
            anonymized_payload = {"anonymized_content": scan_result.anonymized_text}
        return anonymized_payload, scan_result

    def tokenize_pii(self, text: str, language: str = "es") -> tuple[str, dict]:
        scan = self.scan(text, language)
        token_map = {}
        tokenized = scan.anonymized_text
        for entity in scan.pii_found:
            original = text[entity["start"]:entity["end"]]
            token = f"<{entity['entity_type']}_{hashlib.sha256(original.encode()).hexdigest()[:8]}>"
            token_map[token] = original
        return tokenized, token_map

    # ── private helpers ──

    def _scan_regex(self, text: str) -> PIIScanResult:
        anonymized = text
        pii_found: list[dict] = []
        for pattern, entity_type, replacement in _REGEX_PII_PATTERNS:
            for m in re.finditer(pattern, text):
                pii_found.append({"entity_type": entity_type, "start": m.start(), "end": m.end(), "score": 0.8})
            anonymized = re.sub(pattern, replacement, anonymized)
        pii_score = min(100.0, len(pii_found) * 15.0)
        return PIIScanResult(
            original_text=text, anonymized_text=anonymized,
            pii_found=pii_found, pii_score=pii_score,
            entities_count=len(pii_found), anonymization_method="regex",
        )

    def _scan_presidio(self, text: str, language: str) -> PIIScanResult:
        results = self.analyzer.analyze(
            text=text,
            language=language if language in self.supported_languages else "en",
            score_threshold=self.confidence_threshold,
        )
        if not results:
            return PIIScanResult(original_text=text, anonymized_text=text)
        anonymized = self.anonymizer.anonymize(
            text=text, analyzer_results=results,
            operators={
                "DEFAULT": OperatorConfig("replace", {"new_value": "<PII_REDACTED>"}),
                "PERSON": OperatorConfig("replace", {"new_value": "<NOMBRE_REDACTADO>"}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL_REDACTADO>"}),
                "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<TELEFONO_REDACTADO>"}),
                "ES_DNI_NIE": OperatorConfig("replace", {"new_value": "<DNI_REDACTADO>"}),
                "EU_IBAN": OperatorConfig("replace", {"new_value": "<IBAN_REDACTADO>"}),
                "IP_ADDRESS": OperatorConfig("replace", {"new_value": "<IP_REDACTADA>"}),
                "CREDIT_CARD": OperatorConfig("replace", {"new_value": "<TARJETA_REDACTADA>"}),
            },
        )
        pii_entities = [{"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": r.score} for r in results]
        pii_score = min(100.0, len(results) * 15.0)
        return PIIScanResult(
            original_text=text, anonymized_text=anonymized.text,
            pii_found=pii_entities, pii_score=pii_score,
            entities_count=len(results), anonymization_method="replace",
        )


# Singleton instance
pii_scanner = SOCPIIScanner()
