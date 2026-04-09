"""
Drift Detector - Model drift detection across 5 types.
Monitors provider drift and LLM observability.
"""
import structlog
from datetime import datetime, UTC
from dataclasses import dataclass
from typing import Optional

logger = structlog.get_logger()


@dataclass
class DriftResult:
    drift_type: str
    detected: bool
    score: float  # 0-1, higher = more drift
    threshold: float
    details: dict
    recommended_action: str


class DriftDetector:
    """Detects model drift across 5 dimensions."""

    DEFAULT_THRESHOLD = 0.3

    def detect_data_drift(self, current_distribution: dict, baseline_distribution: dict) -> DriftResult:
        """Detect data distribution drift (input features changing)."""
        if not current_distribution or not baseline_distribution:
            return DriftResult("data", False, 0.0, self.DEFAULT_THRESHOLD, {}, "No action needed")

        # Simplified KL divergence approximation
        drift_score = 0.0
        for key in baseline_distribution:
            baseline_val = baseline_distribution.get(key, 0)
            current_val = current_distribution.get(key, 0)
            if baseline_val > 0:
                diff = abs(current_val - baseline_val) / baseline_val
                drift_score += diff

        drift_score = min(1.0, drift_score / max(len(baseline_distribution), 1))

        return DriftResult(
            drift_type="data",
            detected=drift_score > self.DEFAULT_THRESHOLD,
            score=round(drift_score, 4),
            threshold=self.DEFAULT_THRESHOLD,
            details={"current": current_distribution, "baseline": baseline_distribution},
            recommended_action="Retrain model" if drift_score > self.DEFAULT_THRESHOLD else "Monitor",
        )

    def detect_concept_drift(self, accuracy_history: list[float]) -> DriftResult:
        """Detect concept drift (model accuracy degradation over time)."""
        if len(accuracy_history) < 5:
            return DriftResult("concept", False, 0.0, self.DEFAULT_THRESHOLD, {}, "Insufficient data")

        recent = accuracy_history[-5:]
        baseline = accuracy_history[:5]
        recent_avg = sum(recent) / len(recent)
        baseline_avg = sum(baseline) / len(baseline)

        drift_score = max(0, baseline_avg - recent_avg)

        return DriftResult(
            drift_type="concept",
            detected=drift_score > self.DEFAULT_THRESHOLD,
            score=round(drift_score, 4),
            threshold=self.DEFAULT_THRESHOLD,
            details={"recent_avg": recent_avg, "baseline_avg": baseline_avg},
            recommended_action="Investigate and retrain" if drift_score > self.DEFAULT_THRESHOLD else "Monitor",
        )

    def detect_prediction_drift(self, current_predictions: list, baseline_predictions: list) -> DriftResult:
        """Detect prediction distribution drift."""
        if not current_predictions or not baseline_predictions:
            return DriftResult("prediction", False, 0.0, self.DEFAULT_THRESHOLD, {}, "No action")

        current_avg = sum(current_predictions) / len(current_predictions)
        baseline_avg = sum(baseline_predictions) / len(baseline_predictions)
        drift_score = abs(current_avg - baseline_avg) / max(baseline_avg, 1)
        drift_score = min(1.0, drift_score)

        return DriftResult(
            drift_type="prediction",
            detected=drift_score > self.DEFAULT_THRESHOLD,
            score=round(drift_score, 4),
            threshold=self.DEFAULT_THRESHOLD,
            details={"current_avg": current_avg, "baseline_avg": baseline_avg},
            recommended_action="Review model" if drift_score > self.DEFAULT_THRESHOLD else "Monitor",
        )

    def detect_provider_drift(self, response_times: list[float], baseline_avg_ms: float = 500) -> DriftResult:
        """Detect LLM provider drift (latency, quality changes)."""
        if not response_times:
            return DriftResult("provider", False, 0.0, self.DEFAULT_THRESHOLD, {}, "No data")

        current_avg = sum(response_times) / len(response_times)
        drift_score = abs(current_avg - baseline_avg_ms) / baseline_avg_ms
        drift_score = min(1.0, drift_score)

        return DriftResult(
            drift_type="provider",
            detected=drift_score > 0.5,
            score=round(drift_score, 4),
            threshold=0.5,
            details={"current_avg_ms": current_avg, "baseline_avg_ms": baseline_avg_ms},
            recommended_action="Evaluate provider switch" if drift_score > 0.5 else "Monitor",
        )

    def detect_feature_drift(self, feature_importances: dict, baseline_importances: dict) -> DriftResult:
        """Detect feature importance drift."""
        if not feature_importances or not baseline_importances:
            return DriftResult("feature", False, 0.0, self.DEFAULT_THRESHOLD, {}, "No data")

        drift_score = 0.0
        for feat in baseline_importances:
            base_val = baseline_importances.get(feat, 0)
            curr_val = feature_importances.get(feat, 0)
            if base_val > 0:
                drift_score += abs(curr_val - base_val) / base_val

        drift_score = min(1.0, drift_score / max(len(baseline_importances), 1))

        return DriftResult(
            drift_type="feature",
            detected=drift_score > self.DEFAULT_THRESHOLD,
            score=round(drift_score, 4),
            threshold=self.DEFAULT_THRESHOLD,
            details={"current": feature_importances, "baseline": baseline_importances},
            recommended_action="Feature review needed" if drift_score > self.DEFAULT_THRESHOLD else "Monitor",
        )

    def get_overall_drift_status(self, results: list[DriftResult]) -> dict:
        """Get overall drift status from multiple drift checks."""
        max_score = max((r.score for r in results), default=0)
        any_detected = any(r.detected for r in results)

        return {
            "overall_drift_detected": any_detected,
            "max_drift_score": round(max_score, 4),
            "individual_results": [
                {"type": r.drift_type, "detected": r.detected, "score": r.score}
                for r in results
            ],
            "checked_at": datetime.now(UTC).isoformat(),
        }


drift_detector = DriftDetector()
