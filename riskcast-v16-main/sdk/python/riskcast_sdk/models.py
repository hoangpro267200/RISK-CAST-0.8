"""
RISKCAST SDK Models

Data models for API responses.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Quote:
    """Quote model."""
    id: str
    quote_number: str
    status: str
    
    # Shipment
    origin_port: str
    destination_port: str
    cargo_type: str
    cargo_value_usd: float
    
    # Pricing
    total_premium_usd: float
    rate_per_mille: float
    risk_score: float
    risk_grade: str
    
    # Validity
    created_at: datetime
    valid_until: datetime
    
    # Additional fields
    breakdown: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Quote":
        """Create Quote from API response."""
        return cls(
            id=data["quote_id"],
            quote_number=data["quote_number"],
            status=data["status"],
            origin_port=data.get("origin_port", ""),
            destination_port=data.get("destination_port", ""),
            cargo_type=data.get("cargo_type", ""),
            cargo_value_usd=float(data.get("cargo_value_usd", 0)),
            total_premium_usd=float(data.get("total_premium_usd", 0)),
            rate_per_mille=float(data.get("rate_per_mille", 0)),
            risk_score=float(data.get("risk_score", 0)),
            risk_grade=data.get("risk_grade", "C"),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            valid_until=datetime.fromisoformat(data["valid_until"].replace("Z", "+00:00")),
            breakdown=data.get("breakdown", {})
        )


@dataclass
class Policy:
    """Policy model."""
    id: str
    policy_number: str
    status: str
    
    # Coverage
    coverage_limit_usd: float
    deductible_usd: float
    
    # Premium
    premium_usd: float
    
    # Dates
    effective_from: date
    effective_to: date
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Policy":
        """Create Policy from API response."""
        return cls(
            id=data["policy_id"],
            policy_number=data["policy_number"],
            status=data["status"],
            coverage_limit_usd=float(data.get("coverage_limit_usd", 0)),
            deductible_usd=float(data.get("deductible_usd", 0)),
            premium_usd=float(data.get("premium_usd", 0)),
            effective_from=date.fromisoformat(data["effective_from"]),
            effective_to=date.fromisoformat(data["effective_to"])
        )


@dataclass
class Claim:
    """Claim model."""
    id: str
    claim_number: str
    status: str
    
    # Amounts
    claimed_amount_usd: float
    approved_amount_usd: Optional[float]
    
    # Dates
    loss_date: date
    filed_at: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Claim":
        """Create Claim from API response."""
        return cls(
            id=data["claim_id"],
            claim_number=data["claim_number"],
            status=data["status"],
            claimed_amount_usd=float(data.get("claimed_amount_usd", 0)),
            approved_amount_usd=float(data["approved_amount_usd"]) if data.get("approved_amount_usd") else None,
            loss_date=date.fromisoformat(data["loss_date"]),
            filed_at=datetime.fromisoformat(data["filed_at"].replace("Z", "+00:00"))
        )


@dataclass
class RiskAssessment:
    """Risk assessment model."""
    id: str
    overall_risk_score: float
    risk_grade: str
    expected_loss_pct: float
    
    # Risk factors
    factors: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskAssessment":
        """Create RiskAssessment from API response."""
        return cls(
            id=data.get("assessment_id", ""),
            overall_risk_score=float(data.get("overall_risk_score", 0)),
            risk_grade=data.get("risk_grade", "C"),
            expected_loss_pct=float(data.get("expected_loss_pct", 0)),
            factors=data.get("factors", {})
        )
