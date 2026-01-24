"""
Model Versioning Schemas
Pydantic schemas for model versioning operations
RISKCAST V3 - Modular Monolith
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime

from app.modules.model_versioning.models import (
    ModelVersionStatus, ModelScope, ActivationScopeType, ActivationStatus
)
from enum import Enum


class ModelVersionCreate(BaseModel):
    """Schema for creating a model version"""
    name: str = Field(..., description="Model name", min_length=1, max_length=255)
    scope: ModelScope = Field(..., description="Model scope (GLOBAL or TENANT)")
    weights_json: Dict[str, Any] = Field(..., description="Model weights/parameters")
    calibration_json: Optional[Dict[str, Any]] = Field(None, description="Calibration parameters")
    constraints_json: Optional[Dict[str, Any]] = Field(None, description="Model constraints")
    metrics_json: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    
    @field_validator('weights_json')
    @classmethod
    def validate_weights_not_empty(cls, v):
        if not v or not isinstance(v, dict):
            raise ValueError("weights_json must be a non-empty dictionary")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Global Risk Model v1.0",
                "scope": "GLOBAL",
                "weights_json": {
                    "route_layer": 0.4,
                    "cargo_layer": 0.3,
                    "climate_layer": 0.3
                },
                "calibration_json": {
                    "alpha": 1.0,
                    "beta": 0.5
                },
                "constraints_json": {
                    "min_score": 0.0,
                    "max_score": 1.0
                }
            }
        }


class ModelVersionUpdate(BaseModel):
    """Schema for updating a draft model version"""
    name: Optional[str] = Field(None, description="Model name", min_length=1, max_length=255)
    weights_json: Optional[Dict[str, Any]] = Field(None, description="Model weights/parameters")
    calibration_json: Optional[Dict[str, Any]] = Field(None, description="Calibration parameters")
    constraints_json: Optional[Dict[str, Any]] = Field(None, description="Model constraints")
    metrics_json: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Model Name",
                "weights_json": {
                    "route_layer": 0.45,
                    "cargo_layer": 0.25,
                    "climate_layer": 0.30
                }
            }
        }


class ModelVersionResponse(BaseModel):
    """Schema for model version response"""
    id: str = Field(..., description="Model version ID (ULID)")
    tenant_id: Optional[str] = Field(None, description="Tenant ID (NULL for global)")
    scope: ModelScope = Field(..., description="Model scope")
    name: str = Field(..., description="Model name")
    status: ModelVersionStatus = Field(..., description="Model status")
    model_schema_version: str = Field(..., description="Schema version")
    weights_json: Dict[str, Any] = Field(..., description="Model weights")
    calibration_json: Optional[Dict[str, Any]] = Field(None, description="Calibration parameters")
    constraints_json: Optional[Dict[str, Any]] = Field(None, description="Model constraints")
    metrics_json: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    created_by_user_id: Optional[str] = Field(None, description="Creator user ID")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    immutable_hash: Optional[str] = Field(None, description="Immutable hash (set on publish)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                "tenant_id": None,
                "scope": "GLOBAL",
                "name": "Global Risk Model v1.0",
                "status": "PUBLISHED",
                "model_schema_version": "risk_model_v1.0",
                "weights_json": {"route_layer": 0.4},
                "published_at": "2024-01-01T00:00:00Z",
                "immutable_hash": "a1b2c3d4e5f6...",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class ModelVersionListResponse(BaseModel):
    """Schema for paginated list of model versions"""
    items: list[ModelVersionResponse] = Field(..., description="List of model versions")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class ActivationCreate(BaseModel):
    """Schema for creating a model activation"""
    model_version_id: str = Field(..., description="Model version ID")
    corridor_id: Optional[str] = Field(None, description="Corridor ID (NULL = all corridors)")
    product_type: str = Field(..., description="Product type", min_length=1, max_length=100)
    effective_from: datetime = Field(..., description="Activation start date")
    effective_to: Optional[datetime] = Field(None, description="Activation end date (NULL = indefinite)")
    
    @field_validator('effective_to')
    @classmethod
    def validate_effective_period(cls, v, info):
        if v is not None and 'effective_from' in info.data:
            if v <= info.data['effective_from']:
                raise ValueError("effective_to must be after effective_from")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_version_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                "corridor_id": "VN-US-WEST",
                "product_type": "standard",
                "effective_from": "2024-01-01T00:00:00Z",
                "effective_to": None
            }
        }


class ActivationUpdate(BaseModel):
    """Schema for updating a model activation"""
    corridor_id: Optional[str] = Field(None, description="Corridor ID")
    product_type: Optional[str] = Field(None, description="Product type")
    effective_from: Optional[datetime] = Field(None, description="Activation start date")
    effective_to: Optional[datetime] = Field(None, description="Activation end date")
    
    class Config:
        json_schema_extra = {
            "example": {
                "effective_to": "2024-12-31T23:59:59Z"
            }
        }


class ActivationResponse(BaseModel):
    """Schema for model activation response"""
    id: str = Field(..., description="Activation ID (ULID)")
    tenant_id: str = Field(..., description="Tenant ID")
    model_version_id: str = Field(..., description="Model version ID")
    corridor_id: Optional[str] = Field(None, description="Corridor ID")
    product_type: str = Field(..., description="Product type")
    effective_from: datetime = Field(..., description="Activation start date")
    effective_to: Optional[datetime] = Field(..., description="Activation end date")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class ActivationListResponse(BaseModel):
    """Schema for paginated list of activations"""
    items: list[ActivationResponse] = Field(..., description="List of activations")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


# ===============================================================
# Detailed Model Parameter Schemas
# ===============================================================

class BaseWeights(BaseModel):
    """Base risk weights schema"""
    route_risk: float = Field(ge=0, le=1, description="Route risk weight")
    cargo_risk: float = Field(ge=0, le=1, description="Cargo risk weight")
    carrier_risk: float = Field(ge=0, le=1, description="Carrier risk weight")
    timing_risk: float = Field(ge=0, le=1, description="Timing risk weight")
    weather_risk: float = Field(ge=0, le=1, description="Weather risk weight")
    geopolitical_risk: float = Field(ge=0, le=1, description="Geopolitical risk weight")
    
    @field_validator('*')
    @classmethod
    def validate_weights(cls, v):
        """Validate individual weight values"""
        if not isinstance(v, (int, float)):
            raise ValueError("Weight must be a number")
        return float(v)
    
    def validate_sum(self):
        """Validate that weights sum to 1.0"""
        total = sum([
            self.route_risk, self.cargo_risk, self.carrier_risk,
            self.timing_risk, self.weather_risk, self.geopolitical_risk
        ])
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return self


class TailParameters(BaseModel):
    """Tail distribution parameters schema"""
    degrees_of_freedom: float = Field(gt=0, description="Degrees of freedom for t-distribution")
    tail_shock_probability: float = Field(ge=0, le=1, description="Probability of tail shock")
    extreme_loss_multiplier: float = Field(ge=1, description="Multiplier for extreme losses")
    
    @field_validator('degrees_of_freedom')
    @classmethod
    def validate_dof(cls, v):
        if v <= 0:
            raise ValueError("degrees_of_freedom must be > 0")
        return float(v)


class LossTransformParams(BaseModel):
    """Loss transformation parameters schema"""
    base_loss_rate: float = Field(ge=0, le=1, description="Base loss rate")
    risk_score_exponent: float = Field(gt=0, description="Risk score exponent")
    min_loss_pct: float = Field(ge=0, description="Minimum loss percentage")
    max_loss_pct: float = Field(le=1, description="Maximum loss percentage")
    
    @field_validator('max_loss_pct')
    @classmethod
    def validate_max_loss(cls, v, info):
        if 'min_loss_pct' in info.data and v < info.data['min_loss_pct']:
            raise ValueError("max_loss_pct must be >= min_loss_pct")
        return float(v)


class MonteCarloDefaults(BaseModel):
    """Monte Carlo simulation defaults schema"""
    default_iterations: int = Field(ge=100, le=1000000, description="Default number of iterations")
    confidence_levels: list[float] = Field(
        default=[0.95, 0.99],
        description="Confidence levels for VaR calculation"
    )
    
    @field_validator('confidence_levels')
    @classmethod
    def validate_confidence_levels(cls, v):
        if not isinstance(v, list):
            raise ValueError("confidence_levels must be a list")
        for level in v:
            if not (0 < level < 1):
                raise ValueError(f"Confidence level {level} must be between 0 and 1")
        return sorted(v)


# ===============================================================
# Detailed Model Version Request Schemas
# ===============================================================

class ModelVersionCreateRequest(BaseModel):
    """Detailed schema for creating a model version"""
    name: str = Field(min_length=1, max_length=100, description="Model name")
    version: str = Field(min_length=1, max_length=50, description="Semantic version (e.g., 1.0.0)")
    description: Optional[str] = Field(None, description="Model description")
    base_weights: BaseWeights = Field(..., description="Base risk weights")
    correlation_matrix: Dict[str, float] = Field(..., description="Correlation matrix")
    tail_parameters: TailParameters = Field(..., description="Tail distribution parameters")
    interaction_multipliers: Dict[str, float] = Field(..., description="Interaction multipliers")
    loss_transform_params: LossTransformParams = Field(..., description="Loss transformation parameters")
    monte_carlo_defaults: Optional[MonteCarloDefaults] = Field(None, description="Monte Carlo defaults")
    parent_version_id: Optional[str] = Field(None, description="Parent version ID for lineage")
    
    @field_validator('base_weights')
    @classmethod
    def validate_base_weights(cls, v):
        """Validate that base weights sum to 1.0"""
        if isinstance(v, dict):
            v = BaseWeights(**v)
        v.validate_sum()
        return v
    
    @field_validator('correlation_matrix')
    @classmethod
    def validate_correlation_matrix(cls, v):
        """Validate correlation matrix values"""
        if not isinstance(v, dict):
            raise ValueError("correlation_matrix must be a dictionary")
        for key, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Correlation value for {key} must be a number")
            if not (-1 <= value <= 1):
                raise ValueError(f"Correlation value for {key} must be between -1 and 1")
        return v


class ModelVersionUpdateRequest(BaseModel):
    """Schema for updating a model version (only metadata, not parameters)"""
    description: Optional[str] = Field(None, description="Model description")
    # Note: Parameters cannot be updated after creation - create new version instead


# ===============================================================
# Detailed Model Version Response Schemas
# ===============================================================

class ModelVersionDetailResponse(BaseModel):
    """Detailed response schema for model version"""
    id: str = Field(..., description="Model version ID (ULID)")
    tenant_id: Optional[str] = Field(None, description="Tenant ID (NULL for global)")
    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Semantic version")
    description: Optional[str] = Field(None, description="Model description")
    status: ModelVersionStatus = Field(..., description="Model status")
    immutable_hash: str = Field(..., description="Immutable hash")
    parent_version_id: Optional[str] = Field(None, description="Parent version ID")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    # Detailed parameters
    base_weights: Dict[str, float] = Field(..., description="Base risk weights")
    correlation_matrix: Dict[str, float] = Field(..., description="Correlation matrix")
    tail_parameters: Dict[str, float] = Field(..., description="Tail distribution parameters")
    interaction_multipliers: Dict[str, float] = Field(..., description="Interaction multipliers")
    loss_transform_params: Dict[str, float] = Field(..., description="Loss transformation parameters")
    monte_carlo_defaults: Optional[Dict[str, Any]] = Field(None, description="Monte Carlo defaults")
    calibration_run_id: Optional[str] = Field(None, description="Calibration run ID")
    approved_by_user_id: Optional[str] = Field(None, description="Approver user ID")
    
    class Config:
        from_attributes = True


class ModelActivationCreateRequest(BaseModel):
    """Schema for creating a model activation"""
    model_version_id: str = Field(..., description="Model version ID")
    scope_type: ActivationScopeType = Field(
        default=ActivationScopeType.DEFAULT,
        description="Activation scope type"
    )
    scope_id: Optional[str] = Field(None, description="Scope ID (corridor_id, product_id, etc.)")
    effective_from: datetime = Field(..., description="Activation start date")
    effective_to: Optional[datetime] = Field(None, description="Activation end date (NULL = indefinite)")
    
    @field_validator('effective_to')
    @classmethod
    def validate_effective_period(cls, v, info):
        if v is not None and 'effective_from' in info.data:
            if v <= info.data['effective_from']:
                raise ValueError("effective_to must be after effective_from")
        return v


class ModelActivationResponse(BaseModel):
    """Schema for model activation response"""
    id: str = Field(..., description="Activation ID (ULID)")
    model_version_id: str = Field(..., description="Model version ID")
    scope_type: ActivationScopeType = Field(..., description="Activation scope type")
    scope_id: Optional[str] = Field(None, description="Scope ID")
    effective_from: datetime = Field(..., description="Activation start date")
    effective_to: Optional[datetime] = Field(None, description="Activation end date")
    status: ActivationStatus = Field(..., description="Activation status")
    activated_at: datetime = Field(..., description="Activation timestamp")
    
    class Config:
        from_attributes = True
