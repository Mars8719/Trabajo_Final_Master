"""
Bias Testing API - Ethical Bias & Fairness testing.
GET  /api/v1/bias/results - Resultados bias testing
POST /api/v1/bias/run - Ejecutar bias test
"""
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database import get_db
from app.models.db.bias_test import BiasTest, BiasDimension
from app.core.audit_module.bias_checker import bias_checker
from app.core.audit_module.audit_logger import audit_logger

router = APIRouter()


@router.get("/results")
async def get_bias_results(db: AsyncSession = Depends(get_db)):
    """Get all bias test results."""
    result = await db.execute(
        select(BiasTest).order_by(BiasTest.created_at.desc())
    )
    tests = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "dimension": t.dimension.value,
            "test_name": t.test_name,
            "adverse_impact_ratio": t.adverse_impact_ratio,
            "passed": t.passed,
            "threshold": t.threshold,
            "details": t.details,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tests
    ]


@router.post("/run", status_code=201)
async def run_bias_test(
    test_data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Run bias tests across 5 dimensions."""
    results = bias_checker.run_all_tests(test_data)

    saved_tests = []
    for r in results:
        dimension_map = {
            "geographic": BiasDimension.GEOGRAPHIC,
            "temporal": BiasDimension.TEMPORAL,
            "linguistic": BiasDimension.LINGUISTIC,
            "severity": BiasDimension.SEVERITY,
            "source": BiasDimension.SOURCE,
        }

        test_record = BiasTest(
            dimension=dimension_map.get(r.dimension, BiasDimension.GEOGRAPHIC),
            test_name=r.test_name,
            input_data=test_data.get(r.dimension, {}),
            output_data=r.details,
            adverse_impact_ratio=r.adverse_impact_ratio,
            passed=r.passed,
            threshold=r.threshold,
            details=r.details,
            executed_by="system",
        )
        db.add(test_record)
        saved_tests.append({
            "dimension": r.dimension,
            "test_name": r.test_name,
            "adverse_impact_ratio": r.adverse_impact_ratio,
            "passed": r.passed,
            "recommendations": r.recommendations,
        })

    await audit_logger.log(
        actor="system",
        action="bias.test_executed",
        details={"tests_count": len(results), "passed": sum(1 for r in results if r.passed)},
        session=db,
    )

    return {"tests_executed": len(results), "results": saved_tests}
