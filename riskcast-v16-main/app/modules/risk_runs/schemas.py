"""
Risk Runs Schemas
Pydantic schemas for risk calculation runs
RISKCAST V3 - Modular Monolith
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.modules.risk_runs.models import RiskRunStatus, SeedStrategy
from app.modules.risk_engine_v3.schemas import RiskEngineResultV3


class RiskRunCreate(BaseModel):
    """Schema for creating a risk run"""
    assessment_id: str = Field(..., description="Risk assessment ID")
    model_version_id: Optional[str] = Field(None, description="Model version ID")
    iterations: Optional[int] = Field(None, description="Number of Monte Carlo iterations")
    seed_strategy: SeedStrategy = Field(
        default=SeedStrategy.DETERMINISTIC_INPUT_HASH,
        description="Seed strategy"
    )
    seed: Optional[int] = Field(None, description="User-provided seed (required if seed_strategy=USER_PROVIDED)")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options (scenario_set_id, toggles, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "assessment_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                "model_version_id": "01ARZ3NDEKTSV4RRFFQ69G5FAX",
                "iterations": 10000,
                "seed_strategy": "DETERMINISTIC_INPUT_HASH",
                "options": {
                    "scenario_set_id": "scenario-001",
                    "enable_climate": True
                }
            }
        }


class RiskRunResponse(BaseModel):
    """Schema for risk run response"""
    id: str = Field(..., description="Run ID (ULID)")
    tenant_id: str = Field(..., description="Tenant ID")
    risk_assessment_id: str = Field(..., description="Risk assessment ID")
    status: RiskRunStatus = Field(..., description="Run status")
    engine_version: str = Field(..., description="Engine version")
    model_version_id: Optional[str] = Field(None, description="Model version ID")
    result_schema_version: str = Field(..., description="Result schema version")
    seed_strategy: SeedStrategy = Field(..., description="Seed strategy")
    seed: int = Field(..., description="Random seed used")
    iterations: int = Field(..., description="Number of iterations")
    options_json: Optional[Dict[str, Any]] = Field(None, description="Run options")
    result_json: Optional[Dict[str, Any]] = Field(None, description="Result data (if completed)")
    result_hash: Optional[str] = Field(None, description="SHA256 hash of result")
    error_json: Optional[Dict[str, Any]] = Field(None, description="Error details (if failed)")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Computed fields
    result: Optional[RiskEngineResultV3] = Field(None, description="Parsed result (if available)")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm_with_result(cls, run):
        """Create response from ORM with parsed result"""
        data = {
            'id': run.id,
            'tenant_id': run.tenant_id,
            'risk_assessment_id': run.risk_assessment_id,
            'status': run.status,
            'engine_version': run.engine_version,
            'model_version_id': run.model_version_id,
            'result_schema_version': run.result_schema_version,
            'seed_strategy': run.seed_strategy,
            'seed': run.seed,
            'iterations': run.iterations,
            'options_json': run.options_json,
            'result_json': run.result_json,
            'result_hash': run.result_hash,
            'error_json': run.error_json,
            'started_at': run.started_at,
            'completed_at': run.completed_at,
            'created_at': run.created_at,
            'updated_at': run.updated_at,
        }
        
        # Parse result if available
        if run.result_json:
            try:
                data['result'] = RiskEngineResultV3(**run.result_json)
            except Exception:
                data['result'] = None
        
        # Compute duration
        if run.started_at and run.completed_at:
            delta = run.completed_at - run.started_at
            data['duration_seconds'] = delta.total_seconds()
        
        return cls(**data)


class RiskRunDetailResponse(BaseModel):
    """Detailed response schema for risk run with all fields"""
    id: str = Field(..., description="Run ID (ULID)")
    risk_assessment_id: str = Field(..., description="Risk assessment ID")
    status: RiskRunStatus = Field(..., description="Run status")
    engine_version: str = Field(..., description="Engine version")
    model_version_id: Optional[str] = Field(None, description="Model version ID")
    seed: int = Field(..., description="Random seed used")
    seed_strategy: SeedStrategy = Field(..., description="Seed strategy")
    iterations: int = Field(..., description="Number of iterations")
    result_schema_version: str = Field(..., description="Result schema version")
    result_json: Optional[Dict[str, Any]] = Field(None, description="Result data (if completed)")
    result_hash: Optional[str] = Field(None, description="SHA256 hash of result")
    error_json: Optional[Dict[str, Any]] = Field(None, description="Error details (if failed)")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class RiskRunListResponse(BaseModel):
    """Schema for paginated list of risk runs"""
    items: List[RiskRunResponse] = Field(..., description="List of runs")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")
