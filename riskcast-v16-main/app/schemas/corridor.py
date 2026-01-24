"""
Corridor intelligence Pydantic schemas.
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


# ==================== Corridor Schemas ====================

class CorridorCreateRequest(BaseModel):
    """Request schema for creating a corridor."""
    corridor_code: str = Field(..., description="Unique corridor code (e.g., 'SHA-ROT')")
    name: str = Field(..., description="Corridor name")
    origin_port_code: str = Field(..., description="Origin port code")
    destination_port_code: str = Field(..., description="Destination port code")
    description: Optional[str] = Field(None, description="Corridor description")
    origin_port_name: Optional[str] = Field(None, description="Origin port name")
    origin_country: Optional[str] = Field(None, description="Origin country code (ISO 3)")
    origin_coordinates: Optional[Dict[str, float]] = Field(None, description="Origin coordinates {lat, lng}")
    destination_port_name: Optional[str] = Field(None, description="Destination port name")
    destination_country: Optional[str] = Field(None, description="Destination country code (ISO 3)")
    destination_coordinates: Optional[Dict[str, float]] = Field(None, description="Destination coordinates {lat, lng}")
    distance_nm: Optional[int] = Field(None, description="Distance in nautical miles")
    typical_transit_days: Optional[int] = Field(None, description="Typical transit time in days")
    route_type: Optional[str] = Field(None, description="Route type: DIRECT, TRANSSHIPMENT, MULTIMODAL")
    transshipment_ports: Optional[List[str]] = Field(None, description="List of transshipment ports")
    trade_lane: Optional[str] = Field(None, description="Trade lane (e.g., 'Asia-Europe')")
    region: Optional[str] = Field(None, description="Region")
    cargo_types: Optional[List[str]] = Field(None, description="Typical cargo types")


class CorridorResponse(BaseModel):
    """Response schema for corridor."""
    id: str = Field(..., description="Corridor ID (ULID)")
    corridor_code: str = Field(..., description="Corridor code")
    name: str = Field(..., description="Corridor name")
    description: Optional[str] = None
    origin_port_code: str
    origin_port_name: Optional[str] = None
    origin_country: Optional[str] = None
    origin_coordinates: Optional[Dict[str, float]] = None
    destination_port_code: str
    destination_port_name: Optional[str] = None
    destination_country: Optional[str] = None
    destination_coordinates: Optional[Dict[str, float]] = None
    distance_nm: Optional[int] = None
    typical_transit_days: Optional[int] = None
    route_type: Optional[str] = None
    transshipment_ports: Optional[List[str]] = None
    trade_lane: Optional[str] = None
    region: Optional[str] = None
    cargo_types: Optional[List[str]] = None
    status: str = Field(..., description="Status: ACTIVE, INACTIVE, SEASONAL")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CorridorDetailResponse(BaseModel):
    """Response schema for corridor with current benchmark."""
    corridor: CorridorResponse
    current_benchmark: Optional['BenchmarkResponse'] = None


# ==================== Benchmark Schemas ====================

class DelayMetrics(BaseModel):
    """Delay metrics schema."""
    on_time_rate: Optional[float] = Field(None, description="On-time rate (0-1)")
    avg_delay_days: Optional[float] = Field(None, description="Average delay in days")
    delay_std_days: Optional[float] = Field(None, description="Delay standard deviation")
    p50_delay_days: Optional[float] = Field(None, description="50th percentile delay")
    p90_delay_days: Optional[float] = Field(None, description="90th percentile delay")
    p99_delay_days: Optional[float] = Field(None, description="99th percentile delay")


class RiskMetrics(BaseModel):
    """Risk metrics schema."""
    corridor_risk_score: Optional[float] = Field(None, description="Corridor risk score (0-1)")
    loss_rate_historical: Optional[float] = Field(None, description="Historical loss rate")
    claim_frequency: Optional[float] = Field(None, description="Claim frequency")
    avg_claim_severity_pct: Optional[float] = Field(None, description="Average claim severity %")
    piracy_risk: Optional[str] = Field(None, description="Piracy risk: LOW, MEDIUM, HIGH")
    weather_risk: Optional[str] = Field(None, description="Weather risk: LOW, MEDIUM, HIGH")
    port_congestion_risk: Optional[str] = Field(None, description="Port congestion risk: LOW, MEDIUM, HIGH")


class CostBenchmarks(BaseModel):
    """Cost benchmarks schema."""
    avg_freight_rate_per_teu: Optional[float] = Field(None, description="Average freight rate per TEU")
    currency: Optional[str] = Field(None, description="Currency code")
    insurance_rate_per_mille: Optional[float] = Field(None, description="Insurance rate per mille")


class BenchmarkPublishRequest(BaseModel):
    """Request schema for publishing a benchmark."""
    delay_metrics: DelayMetrics = Field(..., description="Delay metrics")
    risk_metrics: RiskMetrics = Field(..., description="Risk metrics")
    effective_from: date = Field(..., description="Effective start date")
    carrier_performance: Optional[Dict[str, Any]] = Field(None, description="Carrier performance by carrier code")
    seasonal_factors: Optional[Dict[str, Any]] = Field(None, description="Seasonal factors by quarter")
    cost_benchmarks: Optional[CostBenchmarks] = Field(None, description="Cost benchmarks")
    data_source: Optional[str] = Field(None, description="Data source identifier")
    data_period_start: Optional[date] = Field(None, description="Data period start")
    data_period_end: Optional[date] = Field(None, description="Data period end")
    sample_size: Optional[int] = Field(None, description="Sample size")


class BenchmarkResponse(BaseModel):
    """Response schema for benchmark."""
    id: str = Field(..., description="Benchmark ID (ULID)")
    corridor_id: str = Field(..., description="Corridor ID (ULID)")
    version: int = Field(..., description="Version number")
    effective_from: date
    effective_to: Optional[date] = None
    is_current: bool = Field(..., description="Is current active benchmark")
    data_source: Optional[str] = None
    data_period_start: Optional[date] = None
    data_period_end: Optional[date] = None
    sample_size: Optional[int] = None
    delay_metrics: Optional[Dict[str, Any]] = None
    risk_metrics: Optional[Dict[str, Any]] = None
    carrier_performance: Optional[Dict[str, Any]] = None
    seasonal_factors: Optional[Dict[str, Any]] = None
    cost_benchmarks: Optional[Dict[str, Any]] = None
    benchmark_hash: Optional[str] = None
    created_at: datetime
    created_by_user_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class BenchmarkComparisonResponse(BaseModel):
    """Response schema for benchmark comparison."""
    benchmark_1: Dict[str, Any] = Field(..., description="First benchmark info")
    benchmark_2: Dict[str, Any] = Field(..., description="Second benchmark info")
    delay_metrics_changes: Dict[str, Any] = Field(..., description="Delay metrics changes")
    risk_metrics_changes: Dict[str, Any] = Field(..., description="Risk metrics changes")
    cost_changes: Dict[str, Any] = Field(..., description="Cost benchmark changes")


# ==================== Port Intelligence Schemas ====================

class PortIntelligenceResponse(BaseModel):
    """Response schema for port intelligence."""
    id: str = Field(..., description="Port ID (ULID)")
    port_code: str = Field(..., description="Port code")
    port_name: str
    country: str
    region: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    port_type: Optional[str] = None
    size_class: Optional[str] = None
    annual_teu_capacity: Optional[int] = None
    current_conditions: Optional[Dict[str, Any]] = None
    risk_factors: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Carrier Profile Schemas ====================

class CarrierProfileResponse(BaseModel):
    """Response schema for carrier profile."""
    id: str = Field(..., description="Carrier ID (ULID)")
    carrier_code: str = Field(..., description="Carrier code")
    carrier_name: str
    carrier_type: Optional[str] = None
    global_metrics: Optional[Dict[str, Any]] = None
    service_quality: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Risk Engine Integration Schemas ====================

class CorridorRiskInputResponse(BaseModel):
    """Response schema for corridor risk inputs."""
    corridor: Dict[str, Any] = Field(..., description="Corridor information")
    benchmark: Dict[str, Any] = Field(..., description="Benchmark metrics")
    origin_port_conditions: Optional[Dict[str, Any]] = Field(None, description="Origin port conditions")
    destination_port_conditions: Optional[Dict[str, Any]] = Field(None, description="Destination port conditions")
    seasonal_factors: Optional[Dict[str, Any]] = Field(None, description="Seasonal factors")
    carrier_performance: Optional[Dict[str, Any]] = Field(None, description="Carrier-specific performance")
