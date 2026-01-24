"""
Pydantic schemas for trigger definitions.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class TriggerType(str, Enum):
    """Trigger type"""
    RAINFALL = "RAINFALL"
    WIND_SPEED = "WIND_SPEED"
    FLOOD = "FLOOD"
    DELAY = "DELAY"
    TEMPERATURE = "TEMPERATURE"
    CYCLONE = "CYCLONE"
    PORT_CONGESTION = "PORT_CONGESTION"
    VESSEL_DELAY = "VESSEL_DELAY"


class TriggerDefinitionStatus(str, Enum):
    """Trigger definition status"""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"


class ComparisonOperator(str, Enum):
    """Comparison operator"""
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="


class AggregationMethod(str, Enum):
    """Aggregation method"""
    MAX = "MAX"
    MIN = "MIN"
    AVG = "AVG"
    SUM = "SUM"
    ANY = "ANY"


class PayoutType(str, Enum):
    """Payout type"""
    FIXED = "FIXED"
    TIERED = "TIERED"
    PERCENTAGE = "PERCENTAGE"


class TriggerParams(BaseModel):
    """Trigger parameters."""
    threshold_value: float = Field(description="Threshold value")
    threshold_unit: str = Field(description="Threshold unit (e.g., 'mm', 'kmh', 'celsius')")
    comparison: ComparisonOperator = Field(description="Comparison operator")
    duration_hours: Optional[int] = Field(None, description="Sustained duration in hours")
    measurement_window_hours: Optional[int] = Field(None, description="Measurement window in hours")
    aggregation: Optional[AggregationMethod] = Field(None, description="Aggregation method")


class ScopeConstraints(BaseModel):
    """Scope constraints."""
    scope_type: Optional[str] = Field(None, description="Scope type (PORT, LOCATION, ROUTE, GLOBAL)")
    allowed_scope_ids: Optional[List[str]] = Field(None, description="Allowed scope IDs")
    geographic_bounds: Optional[Dict[str, Any]] = Field(None, description="Geographic bounds")


class CorroborationRequirements(BaseModel):
    """Corroboration requirements."""
    required_sources: int = Field(ge=1, description="Required number of sources")
    preferred_sources: Optional[List[str]] = Field(None, description="Preferred source names")
    correlation_threshold: Optional[float] = Field(None, ge=0, le=1, description="Correlation threshold (0-1)")
    time_tolerance_minutes: Optional[int] = Field(None, description="Time tolerance in minutes")


class PayoutTier(BaseModel):
    """Payout tier."""
    threshold: float = Field(description="Tier threshold")
    payout_pct: float = Field(ge=0, le=1, description="Payout percentage (0-1)")


class PayoutStructure(BaseModel):
    """Payout structure."""
    type: PayoutType = Field(description="Payout type")
    fixed_amount_cents: Optional[int] = Field(None, ge=0, description="Fixed amount in cents (for FIXED type)")
    tiers: Optional[List[PayoutTier]] = Field(None, description="Payout tiers (for TIERED type)")
    percentage: Optional[float] = Field(None, ge=0, le=1, description="Payout percentage (for PERCENTAGE type)")


class TriggerDefinitionCreateRequest(BaseModel):
    """Request to create trigger definition."""
    name: str = Field(min_length=1, max_length=100, description="Definition name")
    description: Optional[str] = Field(None, description="Description")
    trigger_type: TriggerType = Field(description="Trigger type")
    params: TriggerParams = Field(description="Trigger parameters")
    scope_constraints: Optional[ScopeConstraints] = Field(None, description="Scope constraints")
    corroboration: Optional[CorroborationRequirements] = Field(None, description="Corroboration requirements")
    payout_structure: PayoutStructure = Field(description="Payout structure")


class TriggerDefinitionResponse(BaseModel):
    """Trigger definition response."""
    id: str = Field(description="Definition ID (ULID)")
    tenant_id: Optional[str] = Field(None, description="Tenant ID (ULID, None for system)")
    name: str = Field(description="Definition name")
    description: Optional[str] = Field(None, description="Description")
    trigger_type: str = Field(description="Trigger type")
    status: TriggerDefinitionStatus = Field(description="Status")
    version: int = Field(description="Version number")
    params: Dict[str, Any] = Field(description="Trigger parameters")
    scope_constraints: Optional[Dict[str, Any]] = Field(None, description="Scope constraints")
    corroboration: Optional[Dict[str, Any]] = Field(None, description="Corroboration requirements")
    payout_structure: Optional[Dict[str, Any]] = Field(None, description="Payout structure")
    immutable_hash: Optional[str] = Field(None, description="Immutable hash (if published)")
    published_at: Optional[str] = Field(None, description="Published timestamp")
    created_at: str = Field(description="Created timestamp")
    
    class Config:
        from_attributes = True


class TriggerDefinitionDetailResponse(TriggerDefinitionResponse):
    """Trigger definition detail response."""
    replaces_definition_id: Optional[str] = Field(None, description="Replaced definition ID")
    created_by_user_id: Optional[str] = Field(None, description="Creator user ID")
    published_by_user_id: Optional[str] = Field(None, description="Publisher user ID")
    
    class Config:
        from_attributes = True
