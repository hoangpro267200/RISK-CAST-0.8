"""
Sanctions Screening Data Models
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class SanctionsList(str, Enum):
    """Sanctions lists."""
    OFAC_SDN = "OFAC_SDN"  # US Treasury SDN List
    OFAC_CONS = "OFAC_CONSOLIDATED"
    EU_SANCTIONS = "EU_SANCTIONS"
    UN_SANCTIONS = "UN_SANCTIONS"
    UK_SANCTIONS = "UK_SANCTIONS"
    AU_SANCTIONS = "AU_SANCTIONS"  # Australia DFAT
    
    # Additional lists
    BIS_DENIED = "BIS_DENIED"  # US Commerce Denied Persons
    PEP = "PEP"  # Politically Exposed Persons
    ADVERSE_MEDIA = "ADVERSE_MEDIA"
    WATCHLIST = "WATCHLIST"


class EntityType(str, Enum):
    """Entity types for screening."""
    INDIVIDUAL = "INDIVIDUAL"
    COMPANY = "COMPANY"
    VESSEL = "VESSEL"
    COUNTRY = "COUNTRY"


class MatchStrength(str, Enum):
    """Match strength levels."""
    EXACT = "EXACT"
    STRONG = "STRONG"
    MEDIUM = "MEDIUM"
    WEAK = "WEAK"


class RiskLevel(str, Enum):
    """Risk level assessment."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    CLEAR = "CLEAR"


@dataclass
class SanctionsMatch:
    """A sanctions match result."""
    match_id: str
    list_name: SanctionsList
    list_entry_id: str
    
    matched_name: str
    matched_name_original: str  # Name as it appears in the list
    
    match_strength: MatchStrength
    match_score: float  # 0-100
    
    entity_type: EntityType
    
    # Additional data from the list
    aliases: List[str] = field(default_factory=list)
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    
    # For companies
    registration_number: Optional[str] = None
    
    # For vessels
    imo_number: Optional[str] = None
    mmsi: Optional[str] = None
    flag_country: Optional[str] = None
    
    # Sanctions details
    program: Optional[str] = None  # e.g., "IRAN", "SYRIA", "RUSSIA"
    listing_date: Optional[datetime] = None
    remarks: Optional[str] = None
    
    # Source
    source_url: Optional[str] = None


@dataclass
class ScreeningResult:
    """Complete screening result."""
    screening_id: str
    query: str
    entity_type: EntityType
    
    # Results
    total_matches: int
    high_risk_matches: int
    
    matches: List[SanctionsMatch]
    
    # Risk assessment
    risk_level: RiskLevel
    risk_score: float  # 0-100
    risk_factors: List[str]
    
    # Lists checked
    lists_checked: List[SanctionsList]
    
    # Metadata
    screened_at: datetime
    cached: bool = False
    
    # Recommendation
    recommendation: str = ""  # "CLEAR", "REVIEW", "REJECT"


@dataclass
class VesselScreeningResult:
    """Vessel-specific screening result."""
    screening_id: str
    
    # Vessel identifiers
    imo: Optional[str]
    mmsi: Optional[str]
    vessel_name: str
    flag_country: str
    
    # Vessel screening
    vessel_sanctioned: bool
    vessel_matches: List[SanctionsMatch]
    
    # Owner screening
    owner_name: Optional[str]
    owner_sanctioned: bool
    owner_matches: List[SanctionsMatch]
    
    # Operator screening
    operator_name: Optional[str]
    operator_sanctioned: bool
    operator_matches: List[SanctionsMatch]
    
    # Flag country risk
    flag_country_sanctioned: bool
    flag_country_risk: RiskLevel
    
    # Overall assessment
    overall_risk: RiskLevel
    risk_factors: List[str]
    recommendation: str
    
    screened_at: datetime
