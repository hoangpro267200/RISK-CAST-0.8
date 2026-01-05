"""
RISKCAST v16 - Canonical Engine Interface

This module defines the standard interface for all risk calculation engines.
All engine implementations should conform to this interface for consistency
and interoperability.

ARCHITECTURE: ENGINE-FIRST
- This interface is the contract between API layer and engine layer
- All engines (v14, v15, v16, v2) should implement this interface
- Adapters convert between legacy formats and this canonical format
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Standard risk level classification"""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class EvidenceItem:
    """Evidence supporting a risk layer calculation"""
    source: str  # e.g., "weather_api", "carrier_db", "historical_data"
    value: Any
    confidence: float  # 0.0-1.0
    timestamp: Optional[datetime] = None


@dataclass
class LayerResult:
    """Result from a single risk layer calculation"""
    layer_name: str  # e.g., "Transport Reliability", "Weather Exposure"
    score: float  # 0.0-10.0 (normalized)
    confidence: float  # 0.0-1.0
    evidence: List[EvidenceItem] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfidenceResult:
    """Overall confidence metrics for the risk calculation"""
    overall: float  # 0.0-1.0
    data_quality: float  # 0.0-1.0
    model_confidence: float  # 0.0-1.0
    sample_size: Optional[int] = None  # For Monte Carlo


@dataclass
class FinancialMetrics:
    """Financial risk metrics"""
    expected_loss: float  # USD
    var_95: float  # Value at Risk (95th percentile) in USD
    cvar_95: float  # Conditional VaR (95th percentile) in USD
    distribution: List[float] = field(default_factory=list)  # Monte Carlo samples


@dataclass
class RiskRequest:
    """
    Standardized risk calculation request
    
    This is the canonical input format. All legacy formats should be
    converted to this format via adapters before calling the engine.
    """
    # Core shipment data
    transport_mode: str  # e.g., "sea", "air", "rail", "road", "multimodal"
    cargo_type: str  # e.g., "fragile", "standard", "perishable", "hazardous"
    route: str  # Route identifier
    incoterm: str  # e.g., "FOB", "CIF", "EXW"
    
    # Container and packaging
    container: Optional[str] = None
    container_match: Optional[float] = None  # 0.0-10.0
    packaging: Optional[str] = None
    packaging_quality: Optional[float] = None  # 0.0-10.0
    
    # Priority and timing
    priority: Optional[str] = None
    priority_profile: Optional[str] = None  # e.g., "speed", "cost", "risk"
    priority_weights: Optional[Dict[str, int]] = None  # e.g., {"speed": 40, "cost": 40, "risk": 20}
    transit_time: Optional[float] = None  # days
    etd: Optional[str] = None  # ISO date string
    eta: Optional[str] = None  # ISO date string
    
    # Financial
    cargo_value: float  # USD
    shipment_value: Optional[float] = None  # USD
    
    # Route details
    route_type: Optional[str] = None  # e.g., "direct", "standard", "complex"
    distance: Optional[float] = None  # km
    
    # Risk factors
    weather_risk: Optional[float] = None  # 0.0-10.0
    port_risk: Optional[float] = None  # 0.0-10.0
    carrier_rating: Optional[float] = None  # 0.0-10.0
    
    # Climate variables
    ENSO_index: Optional[float] = None
    typhoon_frequency: Optional[float] = None
    sst_anomaly: Optional[float] = None
    port_climate_stress: Optional[float] = None
    climate_volatility_index: Optional[float] = None
    climate_tail_event_probability: Optional[float] = None
    ESG_score: Optional[float] = None  # 0.0-100.0
    climate_resilience: Optional[float] = None
    green_packaging: Optional[float] = None
    
    # Parties
    buyer: Optional[Dict[str, Any]] = None
    seller: Optional[Dict[str, Any]] = None
    
    # Engine configuration
    use_fuzzy: bool = False
    use_forecast: bool = False
    use_mc: bool = True
    use_var: bool = True
    mc_iterations: Optional[int] = None  # Default from env
    
    # Language
    language: Optional[str] = "en"  # "en", "vi", "zh"
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskResult:
    """
    Standardized risk calculation result
    
    This is the canonical output format. All engines should return this format,
    and adapters can convert to legacy formats for backward compatibility.
    """
    # Overall metrics
    overall_score: float  # 0.0-10.0 (normalized)
    risk_level: RiskLevel
    confidence: ConfidenceResult
    
    # Layer results
    layers: List[LayerResult]  # All 13 layers (or subset)
    
    # Financial metrics
    financial: FinancialMetrics
    
    # Additional metrics
    reliability: Optional[float] = None  # 0.0-1.0
    esg_score: Optional[float] = None  # 0.0-100.0
    
    # Climate metrics
    climate_hazard_index: Optional[float] = None
    climate_var_metrics: Optional[Dict[str, Any]] = None
    
    # Scenario analysis
    scenario_analysis: Optional[Dict[str, Any]] = None
    
    # Forecast
    forecast: Optional[Dict[str, Any]] = None
    
    # Buyer/seller analysis
    buyer_seller_analysis: Optional[Dict[str, Any]] = None
    
    # Metadata
    engine_version: str = "v16"
    calculation_timestamp: datetime = field(default_factory=datetime.now)
    iterations_used: Optional[int] = None  # Monte Carlo iterations
    metadata: Dict[str, Any] = field(default_factory=dict)


class RiskEngineInterface:
    """
    Interface that all risk engines must implement
    
    This ensures consistency across engine versions and enables
    easy swapping of implementations.
    """
    
    def calculate(self, request: RiskRequest) -> RiskResult:
        """
        Calculate risk for a given shipment request
        
        Args:
            request: Standardized risk calculation request
            
        Returns:
            Standardized risk calculation result
            
        Raises:
            RiskCalculationError: If calculation fails
        """
        raise NotImplementedError("Subclasses must implement calculate()")
    
    def validate_request(self, request: RiskRequest) -> List[str]:
        """
        Validate a risk request and return list of errors (empty if valid)
        
        Args:
            request: Risk calculation request
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Required fields
        if not request.transport_mode:
            errors.append("transport_mode is required")
        if not request.cargo_type:
            errors.append("cargo_type is required")
        if not request.route:
            errors.append("route is required")
        if request.cargo_value <= 0:
            errors.append("cargo_value must be positive")
        
        # Validate ranges
        if request.container_match is not None and not (0.0 <= request.container_match <= 10.0):
            errors.append("container_match must be between 0.0 and 10.0")
        if request.packaging_quality is not None and not (0.0 <= request.packaging_quality <= 10.0):
            errors.append("packaging_quality must be between 0.0 and 10.0")
        
        return errors

