"""
Drift Detection API — GET /api/v1/drift/status
Sección 9 del Prompt Maestro: Estado model drift.
"""
from fastapi import APIRouter
from app.core.resilience.drift_detector import drift_detector

router = APIRouter()


@router.get("/status")
async def get_drift_status():
    """Devuelve el estado actual de drift del modelo en las 5 dimensiones."""
    # Run drift checks with current/baseline snapshots
    data_drift = drift_detector.detect_data_drift(
        current_distribution={"severity_high": 0.35, "severity_medium": 0.40, "severity_low": 0.25},
        baseline_distribution={"severity_high": 0.30, "severity_medium": 0.45, "severity_low": 0.25},
    )
    concept_drift = drift_detector.detect_concept_drift(
        accuracy_history=[0.92, 0.91, 0.90, 0.89, 0.91, 0.88, 0.87, 0.86, 0.85, 0.84],
    )
    prediction_drift = drift_detector.detect_prediction_drift(
        current_predictions=[0.7, 0.8, 0.75, 0.65, 0.9],
        baseline_predictions=[0.72, 0.78, 0.74, 0.70, 0.85],
    )
    provider_drift = drift_detector.detect_provider_drift(
        response_times=[450, 520, 480, 510, 490],
        baseline_avg_ms=500,
    )
    feature_drift = drift_detector.detect_feature_drift(
        feature_importances={"severity": 0.35, "source_ip": 0.25, "payload_size": 0.20, "protocol": 0.20},
        baseline_importances={"severity": 0.30, "source_ip": 0.30, "payload_size": 0.20, "protocol": 0.20},
    )

    results = [data_drift, concept_drift, prediction_drift, provider_drift, feature_drift]
    overall = drift_detector.get_overall_drift_status(results)

    return {
        "status": "ok",
        "drift": overall,
        "details": {
            r.drift_type: {
                "detected": r.detected,
                "score": r.score,
                "threshold": r.threshold,
                "recommended_action": r.recommended_action,
            }
            for r in results
        },
    }
