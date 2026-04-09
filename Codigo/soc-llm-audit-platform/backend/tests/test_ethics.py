"""
Ethics Test Suite — 3 Tests
ETH-01: Sesgo geográfico
ETH-02: Sesgo temporal  
ETH-03: Transparencia IA
"""
import pytest
from app.core.audit_module.bias_checker import BiasFairnessChecker
from app.core.audit_module.explainability import ExplainabilityModule


class TestEthics:
    """3 tests for ethical AI compliance."""

    def setup_method(self):
        self.bias_checker = BiasFairnessChecker()
        self.explainability = ExplainabilityModule()

    # ETH-01: Sesgo geográfico — Alertas idénticas: IP europea vs africana
    def test_eth_01_geographic_bias(self):
        """Identical alerts from European vs African IP → Same prioritization."""
        # Create identical alerts with different geo origins
        eu_responses = [
            {"severity_score": 75, "classification": "malware"},
            {"severity_score": 80, "classification": "malware"},
            {"severity_score": 78, "classification": "malware"},
        ]
        african_responses = [
            {"severity_score": 74, "classification": "malware"},
            {"severity_score": 79, "classification": "malware"},
            {"severity_score": 77, "classification": "malware"},
        ]

        result = self.bias_checker.test_geographic_bias(
            responses_group_a=eu_responses,
            responses_group_b=african_responses,
            group_a_label="EU",
            group_b_label="Africa",
        )

        assert result.adverse_impact_ratio >= 0.8, \
            f"Geographic bias ratio must be >= 0.8 (fair), was {result.adverse_impact_ratio}"
        assert result.passed is True, "Geographic bias test must pass for identical alerts"
        assert result.dimension == "geographic"

    # ETH-02: Sesgo temporal — Nocturnas vs diurnas, misma severidad
    def test_eth_02_temporal_bias(self):
        """Nighttime vs daytime alerts with same severity → No degradation by time."""
        daytime_responses = [
            {"severity_score": 82, "classification": "phishing"},
            {"severity_score": 85, "classification": "phishing"},
            {"severity_score": 83, "classification": "phishing"},
        ]
        nighttime_responses = [
            {"severity_score": 81, "classification": "phishing"},
            {"severity_score": 84, "classification": "phishing"},
            {"severity_score": 82, "classification": "phishing"},
        ]

        result = self.bias_checker.test_temporal_bias(
            responses_daytime=daytime_responses,
            responses_nighttime=nighttime_responses,
        )

        assert result.adverse_impact_ratio >= 0.8, \
            f"Temporal bias ratio must be >= 0.8, was {result.adverse_impact_ratio}"
        assert result.passed is True, "Temporal bias test must pass for same-severity alerts"
        assert result.dimension == "temporal"

    # ETH-03: Transparencia IA — "¿Por qué esta decisión?"
    def test_eth_03_ai_transparency(self):
        """'Why this decision?' → Explanation with sources."""
        feature_values = {
            "data_minimization": 95.0,
            "legal_basis": 100.0,
            "transparency": 85.0,
            "pipeline_security": 90.0,
            "bias_fairness": 88.0,
            "retention_compliance": 80.0,
            "incident_reporting": 92.0,
            "hitl_compliance": 100.0,
        }

        explanation = self.explainability.explain_compliance_score(
            feature_values=feature_values,
            total_score=91.05,
            alert_id="test-transparency-001",
        )

        # Must provide comprehensive explanation
        assert explanation.narrative is not None and len(explanation.narrative) > 100, \
            "Narrative must be substantial"
        assert explanation.feature_importance is not None, \
            "Feature importance must be provided"
        assert explanation.shap_values is not None, \
            "SHAP values must be present"
        assert explanation.lime_explanation is not None, \
            "LIME explanation must be present"

        # Narrative must reference regulatory frameworks
        assert "GDPR" in explanation.narrative, "Must reference GDPR"
        assert "NIS2" in explanation.narrative, "Must reference NIS2"

        # Must have all features explained
        assert len(explanation.feature_importance) == 8, \
            "All 8 compliance dimensions must be explained"
