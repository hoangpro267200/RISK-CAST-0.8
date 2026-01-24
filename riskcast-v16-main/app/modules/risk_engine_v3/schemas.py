"""
Risk Engine V3 Schemas
Input/output DTOs for deterministic risk engine
RISKCAST V3 - Modular Monolith
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class RiskEngineInputV3(BaseModel):
    """Input DTO for engine"""
    tenant_id: str = Field(..., description="Tenant ID")
    risk_assessment_id: str = Field(..., description="Risk assessment ID")
    input_schema_version: str = Field(..., description="Input schema version")
    input_snapshot: Dict[str, Any] = Field(..., description="Canonical normalized input data")
    input_hash: str = Field(..., description="SHA256 hash of input")
    corridor_id: Optional[str] = Field(None, description="Corridor identifier")
    product_type: Optional[str] = Field(None, description="Product type identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                "risk_assessment_id": "01ARZ3NDEKTSV4RRFFQ69G5FAW",
                "input_schema_version": "risk_input_v3.0",
                "input_snapshot": {
                    "origin": {"port_code": "VNHPH", "country": "VN"},
                    "destination": {"port_code": "USLAX", "country": "US"},
                    "cargo": {"type": "electronics", "value_usd": 100000}
                },
                "input_hash": "a1b2c3d4e5f6...",
                "corridor_id": "VN-US-WEST",
                "product_type": "standard"
            }
        }


class RiskEngineRunConfig(BaseModel):
    """Run configuration for deterministic execution"""
    engine_version: str = Field(..., description="Engine version (Git SHA or semver+build)")
    model_version_id: Optional[str] = Field(None, description="Model version ID")
    model_payload: Optional[Dict[str, Any]] = Field(None, description="Loaded model payload from DB")
    result_schema_version: str = Field(..., description="Result schema version")
    seed: int = Field(..., description="Random seed for reproducibility")
    seed_strategy: str = Field(..., description="Seed strategy (DETERMINISTIC_INPUT_HASH, USER_PROVIDED)")
    iterations: int = Field(..., description="Number of Monte Carlo iterations")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options (scenario_set_id, toggles, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "engine_version": "v3.0.0+abc123",
                "model_version_id": "01ARZ3NDEKTSV4RRFFQ69G5FAX",
                "model_payload": {"weights": {...}, "parameters": {...}},
                "result_schema_version": "risk_result_v3.0",
                "seed": 1234567890,
                "seed_strategy": "DETERMINISTIC_INPUT_HASH",
                "iterations": 10000,
                "options": {"scenario_set_id": "scenario-001", "enable_climate": True}
            }
        }


class LayerContribution(BaseModel):
    """Contribution of a risk layer to overall score"""
    layer_name: str = Field(..., description="Layer name (e.g., 'route', 'cargo', 'climate')")
    contribution: float = Field(..., description="Contribution value (0.0 to 1.0)")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional layer details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "layer_name": "route",
                "contribution": 0.45,
                "details": {
                    "distance_km": 12000,
                    "risk_factors": ["piracy", "weather"]
                }
            }
        }


class DistributionSummary(BaseModel):
    """Statistical summary of risk distribution"""
    mean: float = Field(..., description="Mean value")
    std: float = Field(..., description="Standard deviation")
    var_95: float = Field(..., description="Value at Risk (95th percentile)")
    var_99: float = Field(..., description="Value at Risk (99th percentile)")
    cvar_95: float = Field(..., description="Conditional VaR (95th percentile)")
    cvar_99: float = Field(..., description="Conditional VaR (99th percentile)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mean": 0.75,
                "std": 0.15,
                "var_95": 0.92,
                "var_99": 0.98,
                "cvar_95": 0.95,
                "cvar_99": 0.99
            }
        }


class RiskEngineResultV3(BaseModel):
    """Output DTO from engine"""
    result_schema_version: str = Field(..., description="Result schema version")
    overall_risk_score: float = Field(..., description="Overall risk score (0.0 to 1.0)")
    layer_contributions: List[LayerContribution] = Field(..., description="Contributions from each risk layer")
    distribution_summary: DistributionSummary = Field(..., description="Statistical summary")
    explainability_graph: Optional[Dict[str, Any]] = Field(None, description="Explainability graph for visualization")
    
    # Provenance (populated by wrapper)
    provenance: Dict[str, Any] = Field(..., description="Provenance information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "result_schema_version": "risk_result_v3.0",
                "overall_risk_score": 0.75,
                "layer_contributions": [
                    {"layer_name": "route", "contribution": 0.45},
                    {"layer_name": "cargo", "contribution": 0.30},
                    {"layer_name": "climate", "contribution": 0.25}
                ],
                "distribution_summary": {
                    "mean": 0.75,
                    "std": 0.15,
                    "var_95": 0.92,
                    "var_99": 0.98,
                    "cvar_95": 0.95,
                    "cvar_99": 0.99
                },
                "explainability_graph": {
                    "nodes": [...],
                    "edges": [...]
                },
                "provenance": {
                    "engine_version": "v3.0.0+abc123",
                    "model_version_id": "01ARZ3NDEKTSV4RRFFQ69G5FAX",
                    "seed": 1234567890,
                    "iterations": 10000,
                    "input_hash": "a1b2c3d4e5f6..."
                }
            }
        }
