"""
Compliance Scoring Engine (re-export for module completeness).
See compliance_engine.py for full implementation.
"""
from app.core.audit_module.compliance_engine import compliance_engine, ComplianceScoringEngine

__all__ = ["compliance_engine", "ComplianceScoringEngine"]
