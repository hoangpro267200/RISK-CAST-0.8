"""
AIS Data Models

Shared data models for AIS vessel tracking.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class VesselType(str, Enum):
    """Vessel type classification."""
    CONTAINER = "CONTAINER"
    BULK_CARRIER = "BULK_CARRIER"
    TANKER = "TANKER"
    GENERAL_CARGO = "GENERAL_CARGO"
    RO_RO = "RO_RO"
    REEFER = "REEFER"
    LNG_CARRIER = "LNG_CARRIER"
    PASSENGER = "PASSENGER"
    FISHING = "FISHING"
    TUG = "TUG"
    OTHER = "OTHER"


class NavigationStatus(str, Enum):
    """AIS navigation status codes."""
    UNDER_WAY_ENGINE = "0"
    AT_ANCHOR = "1"
    NOT_UNDER_COMMAND = "2"
    RESTRICTED_MANEUVERABILITY = "3"
    CONSTRAINED_BY_DRAUGHT = "4"
    MOORED = "5"
    AGROUND = "6"
    ENGAGED_IN_FISHING = "7"
    UNDER_WAY_SAILING = "8"
    RESERVED_HSC = "9"
    RESERVED_WIG = "10"
    RESERVED_11 = "11"
    RESERVED_12 = "12"
    RESERVED_13 = "13"
    AIS_SART = "14"
    NOT_DEFINED = "15"


@dataclass
class VesselPosition:
    """Real-time vessel position data."""
    mmsi: str
    imo: Optional[str]
    vessel_name: str
    
    # Position
    latitude: float
    longitude: float
    
    # Movement
    speed_knots: float
    course: float  # degrees
    heading: float  # degrees
    
    # Status
    navigation_status: NavigationStatus
    
    # Timestamps
    timestamp: datetime
    received_at: datetime
    
    # Voyage info
    destination: Optional[str] = None
    eta: Optional[datetime] = None
    draught: Optional[float] = None  # meters
    
    # Data quality
    data_source: str = "AIS"
    confidence: float = 1.0


@dataclass
class VesselInfo:
    """Static vessel information."""
    mmsi: str
    imo: Optional[str]
    vessel_name: str
    
    # Classification
    vessel_type: VesselType
    vessel_type_code: int
    
    # Dimensions
    length_meters: float
    width_meters: float
    
    # Registration
    flag_country: str
    flag_code: str
    
    # Optional fields
    gross_tonnage: Optional[int] = None
    deadweight_tonnage: Optional[int] = None
    call_sign: Optional[str] = None
    
    # Build info
    year_built: Optional[int] = None
    builder: Optional[str] = None
    
    # Owner/Operator
    owner: Optional[str] = None
    operator: Optional[str] = None
    
    # Technical
    max_speed_knots: Optional[float] = None
    engine_type: Optional[str] = None
    
    # Classification society
    class_society: Optional[str] = None
    
    # Risk indicators
    is_sanctioned: bool = False
    risk_flags: List[str] = field(default_factory=list)


@dataclass
class VoyageInfo:
    """Voyage tracking information."""
    mmsi: str
    imo: Optional[str]
    vessel_name: str
    
    # Voyage details
    origin_port: Optional[str] = None
    origin_port_name: Optional[str] = None
    destination_port: Optional[str] = None
    destination_port_name: Optional[str] = None
    
    # Timing
    departure_time: Optional[datetime] = None
    eta: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    
    # Progress
    distance_remaining_nm: Optional[float] = None
    distance_traveled_nm: Optional[float] = None
    progress_percentage: Optional[float] = None
    
    # Route
    waypoints: List[Tuple[float, float]] = field(default_factory=list)
    
    # Current position
    current_position: Optional[VesselPosition] = None


@dataclass
class GeofenceAlert:
    """Geofencing alert."""
    alert_id: str
    mmsi: str
    vessel_name: str
    
    alert_type: str  # "ENTERED", "EXITED", "APPROACHING"
    zone_name: str
    zone_type: str  # "HIGH_RISK", "PORT", "ECA", "CUSTOM"
    
    position: VesselPosition
    
    timestamp: datetime
    
    # Optional fields
    distance_to_zone_nm: Optional[float] = None
    time_to_zone_minutes: Optional[int] = None
    severity: str = "INFO"  # "INFO", "WARNING", "CRITICAL"


@dataclass
class TrackPoint:
    """Historical track point."""
    latitude: float
    longitude: float
    timestamp: datetime
    speed_knots: float
    course: float
