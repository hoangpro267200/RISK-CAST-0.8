"""
Risk Run Schemas
Pydantic schemas for risk run API
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import enum


class RiskRunStatus(str, enum.Enum):
    """Risk run execution status"""
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RiskRunCreate(BaseModel):
    """Schema for creating a risk run"""
    assessment_id: str = Field(..., description="Risk assessment ID")
    seed: Optional[int] = Field(None, description="Random seed (required if seed_strategy=USER_PROVIDED)")
    seed_strategy: str = Field("DETERMINISTIC_INPUT_HASH", description="Seed strategy")
    iterations: int = Field(10000, ge=1, description="Number of Monte Carlo iterations")
    engine_version: Optional[str] = Field(None, description="Engine version (defaults to latest)")
    model_version_id: Optional[str] = Field(None, description="Model version ID")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")
    
    class Config:
        from_attributes = True


class RiskRunConfig(BaseModel):
    """Configuration for creating a risk run"""
    seed: Optional[int] = Field(None, description="Random seed (required if seed_strategy=USER_PROVIDED)")
    seed_strategy: str = Field("HASH_BASED", description="Seed strategy")
    iterations: int = Field(10000, ge=1, description="Number of Monte Carlo iterations")
    model_version_id: Optional[str] = Field(None, description="Model version ID")
    priority: int = Field(0, description="Job priority (higher = higher priority)")
    max_attempts: int = Field(3, ge=1, le=10, description="Maximum retry attempts")
    
    class Config:
        from_attributes = True


class RiskRunResponse(BaseModel):
    """Schema for risk run response"""
    id: str = Field(..., description="Run ID (UUID)")
    status: RiskRunStatus = Field(..., description="Run status")
    status_url: Optional[str] = Field(None, description="URL to check run status")
    
    class Config:
        from_attributes = True


class RiskRunStatusResponse(BaseModel):
    """Response for run status polling"""
    status: RiskRunStatus = Field(..., description="Current run status")
    progress: Optional[float] = Field(None, ge=0.0, le=1.0, description="Progress estimate (0.0 to 1.0)")
    eta_seconds: Optional[int] = Field(None, description="Estimated time to completion in seconds")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    class Config:
        from_attributes = True


class RiskRunResultResponse(BaseModel):
    """Response for run result (only if SUCCEEDED)"""
    id: str = Field(..., description="Run ID")
    status: RiskRunStatus = Field(..., description="Run status")
    result_json: Dict[str, Any] = Field(..., description="Result data")
    result_hash: str = Field(..., description="SHA256 hash of result")
    completed_at: datetime = Field(..., description="Completion timestamp")
    
    class Config:
        from_attributes = True


class RiskRunDetailResponse(BaseModel):
    """Detailed response for risk run"""
    id: str = Field(..., description="Run ID")
    tenant_id: str = Field(..., description="Tenant ID")
    assessment_id: str = Field(..., description="Risk assessment ID")
    status: RiskRunStatus = Field(..., description="Run status")
    
    # Configuration
    seed: int = Field(..., description="Random seed used")
    seed_strategy: str = Field(..., description="Seed strategy")
    iterations: int = Field(..., description="Number of iterations")
    
    # Versioning
    engine_version: str = Field(..., description="Engine version")
    model_version_id: Optional[str] = Field(None, description="Model version ID")
    
    # Results (if completed)
    result_json: Optional[Dict[str, Any]] = Field(None, description="Result data")
    result_hash: Optional[str] = Field(None, description="SHA256 hash of result")
    
    # Error info (if failed)
    error_message: Optional[str] = Field(None, description="Error message")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    
    # Timing
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    # Job info
    job_id: Optional[str] = Field(None, description="Job ID (if enqueued)")
    job_status: Optional[str] = Field(None, description="Job status")
    
    class Config:
        from_attributes = True


class RiskRunProvenanceResponse(BaseModel):
    """Detailed provenance response for risk run"""
    run_id: str = Field(..., description="Run ID")
    assessment_id: str = Field(..., description="Risk assessment ID")
    input_hash: str = Field(..., description="Input hash from assessment")
    seed: int = Field(..., description="Random seed used")
    seed_strategy: str = Field(..., description="Seed strategy")
    iterations: int = Field(..., description="Number of iterations")
    engine_version: str = Field(..., description="Engine version")
    model_version_id: Optional[str] = Field(None, description="Model version ID")
    result_hash: Optional[str] = Field(None, description="Result hash (if completed)")
    computed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    class Config:
        from_attributes = True


class ReplayResultResponse(BaseModel):
    """Response for replay verification"""
    run_id: str = Field(..., description="Run ID")
    matches: bool = Field(..., description="Whether replay matches original")
    original_hash: str = Field(..., description="Original result hash")
    replay_hash: str = Field(..., description="Replay result hash")
    diff_summary: Optional[Dict[str, Any]] = Field(None, description="Diff summary if mismatch")
    error: Optional[str] = Field(None, description="Error message if replay failed")
    replay_duration_seconds: Optional[float] = Field(None, description="Replay duration in seconds")
    
    class Config:
        from_attributes = True
