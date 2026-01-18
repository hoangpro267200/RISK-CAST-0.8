"""
RISKCAST Insurance Module V2 - Data Models
===========================================
Enterprise-Grade Insurtech Integration System
Version: 2.0.0
Date: January 15, 2026
"""

from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from enum import Enum
import json

from app.models.base import BaseModel


# ============================================================================
# ENUMS
# ============================================================================

class InsuranceProductCategory(str, Enum):
    CLASSICAL = "classical"
    PARAMETRIC = "parametric"
    SPECIALTY = "specialty"
    EMBEDDED = "embedded"


class InsuranceProductTier(str, Enum):
    A = "A"  # Classical Insurance
    B = "B"  # Parametric Products
    C = "C"  # Embedded Specialty
    D = "D"  # Transactional API-Backed
    E = "E"  # Future Risk Hedging


class ProductStatus(str, Enum):
    CONCEPT = "concept"
    API_PARAMETRIC = "api_parametric"
    TRANSACTIONAL = "transactional"
    FINANCIALIZED = "financialized"


class TransactionState(str, Enum):
    QUOTE_REQUESTED = "quote_requested"
    QUOTE_GENERATED = "quote_generated"
    CONFIGURING = "configuring"
    CONFIGURED = "configured"
    KYC_REQUIRED = "kyc_required"
    KYC_IN_PROGRESS = "kyc_in_progress"
    KYC_APPROVED = "kyc_approved"
    KYC_FAILED = "kyc_failed"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_PROCESSING = "payment_processing"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    BINDING = "binding"
    BOUND = "bound"
    POLICY_DELIVERED = "policy_delivered"
    ACTIVE = "active"
    CLAIM_FILED = "claim_filed"
    CLAIM_SETTLED = "claim_settled"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ClaimType(str, Enum):
    PARAMETRIC_AUTOMATIC = "parametric_automatic"
    CLASSICAL_MANUAL = "classical_manual"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    WIRE_TRANSFER = "wire_transfer"
    NET_30 = "net_30"
    NET_60 = "net_60"


class Carrier(str, Enum):
    ALLIANZ = "allianz"
    AXA_XL = "axa_xl"
    LLOYDS = "lloyds"
    SWISS_RE = "swiss_re"
    MUNICH_RE = "munich_re"
    TOKIO_MARINE = "tokio_marine"
    RISKCAST = "riskcast"  # For parametric products


# ============================================================================
# PRODUCT MODELS
# ============================================================================

@dataclass
class ParametricTrigger:
    """Parametric insurance trigger definition."""
    product_id: str
    trigger_type: Literal["weather", "port_congestion", "natcat", "strike", "routing"]
    
    location: Dict[str, Any]  # port_code, coordinates, radius_km, etc.
    metric: str  # e.g., "cumulative_rainfall_mm"
    threshold: float
    data_source: str  # e.g., "tomorrow_io"
    
    threshold_unit: Optional[str] = None
    calculation_method: Optional[str] = None
    observation_period: Optional[Dict[str, Any]] = None
    verification_requirement: Optional[str] = None
    secondary_data_source: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PayoutStructure:
    """Parametric payout structure definition."""
    type: Literal["per_mm_excess", "per_day_excess", "binary", "tiered"]
    payout_per_unit: Optional[float] = None
    minimum_payout: Optional[float] = None
    maximum_payout: Optional[float] = None
    maximum_days: Optional[int] = None
    franchise_deductible: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class InsuranceProduct:
    """Insurance product definition."""
    product_id: str
    name: str
    category: InsuranceProductCategory
    tier: InsuranceProductTier
    status: ProductStatus
    
    description: str
    coverage_type: str
    carrier: Optional[Carrier] = None
    
    base_rate: Optional[float] = None
    pricing_model: Literal["classical", "parametric", "hybrid"] = "classical"
    
    trigger: Optional[ParametricTrigger] = None
    payout_structure: Optional[PayoutStructure] = None
    
    min_sum_insured: Optional[float] = None
    max_sum_insured: Optional[float] = None
    default_deductible: Optional[float] = None
    
    available_regions: List[str] = field(default_factory=list)
    requires_kyc: bool = True
    requires_license: Optional[bool] = None
    documentation_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        if self.trigger:
            result["trigger"] = self.trigger.to_dict()
        if self.payout_structure:
            result["payout_structure"] = self.payout_structure.to_dict()
        return result


# ============================================================================
# QUOTE MODELS
# ============================================================================

@dataclass
class PremiumBreakdown:
    """Premium calculation breakdown."""
    base_premium: float
    risk_adjustment: float
    total_premium: float
    surcharges: List[Dict[str, Any]] = field(default_factory=list)
    currency: str = "USD"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CoverageDetails:
    """Insurance coverage details."""
    sum_insured: float
    deductible: float
    coverage_type: str
    territorial_scope: str
    effective_date: datetime
    expiry_date: datetime
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["effective_date"] = self.effective_date.isoformat()
        result["expiry_date"] = self.expiry_date.isoformat()
        return result


@dataclass
class PricingBreakdown:
    """Transparent pricing breakdown."""
    expected_loss: float
    load_factor: float
    administrative_costs: float
    risk_adjustments: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class InsuranceQuote:
    """Insurance quote model."""
    quote_id: str
    product_id: str
    transaction_id: Optional[str] = None
    
    premium: PremiumBreakdown = field(default_factory=lambda: PremiumBreakdown(
        base_premium=0, risk_adjustment=0, total_premium=0
    ))
    coverage: Optional[CoverageDetails] = None
    
    trigger: Optional[ParametricTrigger] = None
    payout_structure: Optional[PayoutStructure] = None
    expected_payout: Optional[float] = None
    trigger_probability: Optional[float] = None
    basis_risk_score: Optional[float] = None
    
    pricing_breakdown: Optional[PricingBreakdown] = None
    market_comparison: Optional[Dict[str, Any]] = None
    
    valid_until: Optional[datetime] = None
    bind_endpoint: Optional[str] = None
    
    carrier_quote_id: Optional[str] = None
    carrier: Optional[Carrier] = None
    
    def to_dict(self) -> Dict:
        result = {
            "quote_id": self.quote_id,
            "product_id": self.product_id,
            "transaction_id": self.transaction_id,
            "premium": self.premium.to_dict() if self.premium else None,
            "coverage": self.coverage.to_dict() if self.coverage else None,
            "expected_payout": self.expected_payout,
            "trigger_probability": self.trigger_probability,
            "basis_risk_score": self.basis_risk_score,
            "pricing_breakdown": self.pricing_breakdown.to_dict() if self.pricing_breakdown else None,
            "market_comparison": self.market_comparison,
            "carrier_quote_id": self.carrier_quote_id,
            "carrier": self.carrier.value if self.carrier else None,
        }
        
        if self.valid_until:
            result["valid_until"] = self.valid_until.isoformat()
        if self.trigger:
            result["trigger"] = self.trigger.to_dict()
        if self.payout_structure:
            result["payout_structure"] = self.payout_structure.to_dict()
        if self.bind_endpoint:
            result["bind_endpoint"] = self.bind_endpoint
            
        return result


# ============================================================================
# TRANSACTION MODELS
# ============================================================================

@dataclass
class InsuredParty:
    """Insured party information."""
    legal_name: str
    registration_number: str
    country: str
    address: Dict[str, str]
    contact: Dict[str, str]
    industry: Optional[str] = None
    beneficial_owner: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CoverageConfig:
    """Coverage configuration."""
    sum_insured: float
    deductible: float
    effective_date: datetime
    expiry_date: datetime
    
    trigger_threshold: Optional[float] = None
    payout_per_day: Optional[float] = None
    max_payout_days: Optional[int] = None
    max_payout_amount: Optional[float] = None
    extensions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["effective_date"] = self.effective_date.isoformat()
        result["expiry_date"] = self.expiry_date.isoformat()
        return result


@dataclass
class KYCResult:
    """KYC verification result."""
    status: Literal["approved", "requires_manual_review", "failed", "requires_enhanced_due_diligence"]
    risk_score: float
    flags: List[str] = field(default_factory=list)
    sanctions_matches: int = 0
    pep_matches: int = 0
    adverse_media: int = 0
    approved_at: Optional[datetime] = None
    reason: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        if self.approved_at:
            result["approved_at"] = self.approved_at.isoformat()
        return result


@dataclass
class PaymentResult:
    """Payment processing result."""
    status: Literal["completed", "failed", "requires_action"]
    payment_id: Optional[str] = None
    amount: float = 0.0
    currency: str = "USD"
    paid_at: Optional[datetime] = None
    payment_method_details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    client_secret: Optional[str] = None
    next_action: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        if self.paid_at:
            result["paid_at"] = self.paid_at.isoformat()
        return result


@dataclass
class StateTransition:
    """Transaction state transition."""
    from_state: TransactionState
    to_state: TransactionState
    timestamp: datetime
    reason: Optional[str] = None
    actor: Optional[str] = None  # 'system', 'user', 'carrier'
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class Transaction:
    """Insurance transaction model."""
    transaction_id: str
    state: TransactionState
    created_at: datetime
    updated_at: datetime
    
    riskcast_assessment_id: str
    shipment_reference: str
    
    product: InsuranceProduct
    coverage_config: CoverageConfig
    quote: InsuranceQuote
    
    insured: InsuredParty
    beneficiary: Optional[Dict[str, Any]] = None
    
    kyc_result: Optional[KYCResult] = None
    sanctions_check: Optional[Dict[str, Any]] = None
    
    payment_method: Optional[PaymentMethod] = None
    payment_result: Optional[PaymentResult] = None
    
    policy_number: Optional[str] = None
    policy_document_url: Optional[str] = None
    certificate_url: Optional[str] = None
    
    state_history: List[StateTransition] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = {
            "transaction_id": self.transaction_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "riskcast_assessment_id": self.riskcast_assessment_id,
            "shipment_reference": self.shipment_reference,
            "product": self.product.to_dict(),
            "coverage_config": self.coverage_config.to_dict(),
            "quote": self.quote.to_dict(),
            "insured": self.insured.to_dict(),
            "beneficiary": self.beneficiary,
            "sanctions_check": self.sanctions_check,
            "payment_method": self.payment_method.value if self.payment_method else None,
            "policy_number": self.policy_number,
            "policy_document_url": self.policy_document_url,
            "certificate_url": self.certificate_url,
            "state_history": [st.to_dict() for st in self.state_history],
        }
        
        if self.kyc_result:
            result["kyc_result"] = self.kyc_result.to_dict()
        if self.payment_result:
            result["payment_result"] = self.payment_result.to_dict()
            
        return result


# ============================================================================
# POLICY MODELS
# ============================================================================

@dataclass
class Policy:
    """Insurance policy model."""
    policy_number: str
    transaction_id: str
    product: InsuranceProduct
    coverage_config: CoverageConfig
    insured: InsuredParty
    premium: float
    effective_date: datetime
    expiry_date: datetime
    status: Literal["active", "expired", "cancelled", "claim_settled"]
    
    carrier: Optional[Carrier] = None
    carrier_policy_id: Optional[str] = None
    
    trigger: Optional[ParametricTrigger] = None
    payout_structure: Optional[PayoutStructure] = None
    monitoring_enabled: bool = False
    
    policy_document_url: Optional[str] = None
    certificate_url: Optional[str] = None
    
    container_reference: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict:
        result = {
            "policy_number": self.policy_number,
            "transaction_id": self.transaction_id,
            "product": self.product.to_dict(),
            "coverage_config": self.coverage_config.to_dict(),
            "insured": self.insured.to_dict(),
            "premium": self.premium,
            "effective_date": self.effective_date.isoformat(),
            "expiry_date": self.expiry_date.isoformat(),
            "status": self.status,
            "carrier": self.carrier.value if self.carrier else None,
            "carrier_policy_id": self.carrier_policy_id,
            "monitoring_enabled": self.monitoring_enabled,
            "policy_document_url": self.policy_document_url,
            "certificate_url": self.certificate_url,
            "container_reference": self.container_reference,
        }
        
        if self.trigger:
            result["trigger"] = self.trigger.to_dict()
        if self.payout_structure:
            result["payout_structure"] = self.payout_structure.to_dict()
            
        return result


# ============================================================================
# CLAIM MODELS
# ============================================================================

@dataclass
class Claim:
    """Insurance claim model."""
    claim_number: str
    policy_number: str
    claim_type: ClaimType
    
    incident_date: Optional[datetime] = None
    loss_type: Optional[str] = None
    estimated_loss: Optional[float] = None
    description: Optional[str] = None
    
    trigger_date: Optional[datetime] = None
    trigger_event: Optional[Dict[str, Any]] = None
    payout_amount: Optional[float] = None
    
    status: Literal["submitted", "under_review", "verified", "payout_initiated", "paid", "rejected"] = "submitted"
    
    evidence: Optional[Dict[str, Any]] = None
    
    adjuster_name: Optional[str] = None
    adjuster_contact: Optional[str] = None
    carrier_claim_number: Optional[str] = None
    carrier_claim_id: Optional[str] = None
    
    paid_at: Optional[datetime] = None
    payment_reference: Optional[str] = None
    payment_amount: Optional[float] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        result = {
            "claim_number": self.claim_number,
            "policy_number": self.policy_number,
            "claim_type": self.claim_type.value,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if self.incident_date:
            result["incident_date"] = self.incident_date.isoformat()
        if self.trigger_date:
            result["trigger_date"] = self.trigger_date.isoformat()
        if self.paid_at:
            result["paid_at"] = self.paid_at.isoformat()
            
        # Add other optional fields
        for field_name in ["loss_type", "estimated_loss", "description", "trigger_event", 
                          "payout_amount", "evidence", "adjuster_name", "adjuster_contact",
                          "carrier_claim_number", "carrier_claim_id", "payment_reference", 
                          "payment_amount"]:
            value = getattr(self, field_name, None)
            if value is not None:
                result[field_name] = value
                
        return result


# ============================================================================
# CARRIER API MODELS
# ============================================================================

@dataclass
class CarrierQuoteRequest:
    """Carrier quote request model."""
    request_id: str
    shipment: Dict[str, Any]
    coverage: Dict[str, Any]
    risk_data: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CarrierQuoteResponse:
    """Carrier quote response model."""
    quote_id: str
    status: str  # 'quoted' | 'declined'
    premium: Dict[str, Any]
    coverage_details: Dict[str, Any]
    valid_until: str
    bind_endpoint: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CarrierBindRequest:
    """Carrier bind request model."""
    quote_id: str
    payment_method: str
    insured_party: InsuredParty
    compliance: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["insured_party"] = self.insured_party.to_dict()
        return result


@dataclass
class CarrierBindResponse:
    """Carrier bind response model."""
    policy_number: str
    status: str  # 'bound' | 'failed'
    effective_date: str
    policy_document_url: Optional[str] = None
    certificate_of_insurance: Optional[str] = None
    payment_instructions: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
