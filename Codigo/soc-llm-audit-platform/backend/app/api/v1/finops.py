"""
FinOps API — GET /api/v1/finops/costs
Sección 9 del Prompt Maestro: Costes por inferencia / DoW.
"""
from fastapi import APIRouter
from datetime import datetime, UTC

router = APIRouter()


@router.get("/costs")
async def get_finops_costs():
    """Devuelve el coste por inferencia y estado del DoW (Dollar-on-Waste) budget."""
    # FinOps metrics — in production these would come from billing APIs
    return {
        "status": "ok",
        "period": "current_month",
        "checked_at": datetime.now(UTC).isoformat(),
        "cost_per_inference": {
            "avg_usd": 0.0042,
            "p95_usd": 0.0089,
            "p99_usd": 0.0156,
            "total_inferences": 142850,
        },
        "dow_budget": {
            "monthly_budget_usd": 5000.0,
            "spent_usd": 3245.80,
            "remaining_usd": 1754.20,
            "utilization_pct": 64.92,
            "projected_month_end_usd": 4890.50,
            "warning_threshold_pct": 80.0,
            "status": "within_budget",
        },
        "cost_by_model": [
            {"model": "gpt-4", "inferences": 45200, "cost_usd": 1890.40, "avg_tokens": 2100},
            {"model": "gpt-3.5-turbo", "inferences": 87500, "cost_usd": 875.00, "avg_tokens": 1500},
            {"model": "llama-3-70b", "inferences": 10150, "cost_usd": 480.40, "avg_tokens": 1800},
        ],
        "cost_by_pipeline_stage": [
            {"stage": "triage", "pct": 35.0, "cost_usd": 1136.03},
            {"stage": "summarization", "pct": 25.0, "cost_usd": 811.45},
            {"stage": "playbook_recommendation", "pct": 20.0, "cost_usd": 649.16},
            {"stage": "explainability", "pct": 15.0, "cost_usd": 486.87},
            {"stage": "bias_checking", "pct": 5.0, "cost_usd": 162.29},
        ],
    }


@router.get("/summary")
async def get_finops_summary():
    """Resumen ejecutivo FinOps para dashboard."""
    return {
        "daily_cost_usd": 108.19,
        "daily_inferences": 4762,
        "cost_trend": "stable",
        "budget_remaining_pct": 35.08,
        "top_cost_driver": "gpt-4",
        "optimization_suggestions": [
            "Migrar triage a gpt-3.5-turbo para reducir costes -40%",
            "Implementar cache de respuestas similares: ahorro estimado 15%",
            "Batch processing en horarios off-peak: ahorro estimado 10%",
        ],
    }
