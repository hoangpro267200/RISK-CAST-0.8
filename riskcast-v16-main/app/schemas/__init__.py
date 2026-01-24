"""
Pydantic schemas for RISKCAST API.
"""
from app.schemas.risk_assessment import (
    RiskAssessmentResponse,
)
from app.modules.risk_assessments.schemas import RiskAssessmentCreate

__all__ = [
    "RiskAssessmentCreate",
    "RiskAssessmentResponse",
]
