"""
Quote Management System

Manages the quote lifecycle:
1. Quote generation from pricing
2. Quote storage and retrieval
3. Quote modification and recalculation
4. Quote acceptance/rejection
5. Quote to policy conversion
6. Quote analytics
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4
from decimal import Decimal
import logging
import hashlib
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.pricing.pricing_engine import (
    PricingEngine, PricingResult, PricingInput,
    CoverageType, DeductibleType, PricingTier
)
from app.core.risk_engine.v16.risk_engine_calibrated import CalibratedRiskResult
from app.models.quote import Quote as QuoteModel
from app.core.audit.immutable_ledger import ImmutableAuditLedger


class QuoteStatus(Enum):
    """Quote lifecycle status."""
    DRAFT = "DRAFT"           # Being created
    PENDING = "PENDING"       # Awaiting customer response
    ACCEPTED = "ACCEPTED"     # Customer accepted
    DECLINED = "DECLINED"     # Customer declined
    EXPIRED = "EXPIRED"       # Validity period passed
    BOUND = "BOUND"           # Converted to policy
    CANCELLED = "CANCELLED"   # Cancelled by insurer
    ISSUED = "ISSUED"         # Issued to customer
    REPLACED = "REPLACED"     # Replaced by newer version


class DeclineReason(Enum):
    """Reasons for declining a quote."""
    PRICE_TOO_HIGH = "PRICE_TOO_HIGH"
    COVERAGE_INSUFFICIENT = "COVERAGE_INSUFFICIENT"
    DEDUCTIBLE_TOO_HIGH = "DEDUCTIBLE_TOO_HIGH"
    COMPETITOR_BETTER = "COMPETITOR_BETTER"
    NO_LONGER_NEEDED = "NO_LONGER_NEEDED"
    TERMS_UNACCEPTABLE = "TERMS_UNACCEPTABLE"
    OTHER = "OTHER"


@dataclass
class QuoteSummary:
    """Summary of a quote for listing."""
    quote_id: str
    quote_number: str
    status: QuoteStatus
    cargo_value_usd: Decimal
    total_premium_usd: Decimal
    risk_grade: str
    origin: str
    destination: str
    created_at: datetime
    valid_until: datetime
    customer_name: Optional[str] = None


@dataclass
class QuoteDetail:
    """Full quote details."""
    quote_id: str
    quote_number: str
    status: QuoteStatus
    
    # Pricing
    pricing_result: Optional[PricingResult]
    
    # Risk assessment
    risk_score: float
    risk_grade: str
    risk_factors: Dict[str, float]
    
    # Shipment details
    origin_port: str
    destination_port: str
    cargo_type: str
    cargo_value_usd: Decimal
    container_count: int
    transit_days: int
    
    # Coverage
    coverage_type: str
    coverage_limit_usd: Decimal
    deductible_amount: Decimal
    
    # Terms
    terms_and_conditions: Dict[str, Any]
    exclusions: List[str]
    
    # Customer
    customer_id: Optional[str]
    customer_name: Optional[str]
    
    # Timestamps
    created_at: datetime
    modified_at: datetime
    valid_from: datetime
    valid_until: datetime
    
    # History
    version: int
    previous_versions: List[str]


@dataclass
class QuoteModification:
    """A modification to an existing quote."""
    quote_id: str
    field: str
    old_value: Any
    new_value: Any
    modified_by: str
    modified_at: datetime
    requires_reprice: bool


class QuoteManager:
    """
    Manages quote lifecycle.
    
    Key operations:
    - Create quote from risk assessment
    - Retrieve and list quotes
    - Modify quote and recalculate
    - Accept/decline/expire quotes
    - Convert quote to policy
    """
    
    # Default quote validity
    DEFAULT_VALIDITY_DAYS = 7
    
    # Terms and conditions template
    DEFAULT_TERMS = {
        "coverage_basis": "Warehouse to Warehouse",
        "claims_basis": "First Loss",
        "survey_requirement": "None for losses under $10,000",
        "payment_terms": "Premium due within 30 days of inception",
        "cancellation": "30 days written notice required"
    }
    
    # Standard exclusions
    STANDARD_EXCLUSIONS = [
        "War and civil commotion (unless war risk purchased)",
        "Nuclear, chemical, biological events",
        "Willful misconduct of the assured",
        "Inherent vice or nature of cargo",
        "Delay, loss of market",
        "Insolvency of carrier",
        "Contamination (unless specified)",
        "Cyber events affecting navigation/cargo"
    ]
    
    def __init__(
        self,
        db: Session,
        pricing_engine: PricingEngine,
        audit: ImmutableAuditLedger,
        tenant_id: Optional[str] = None
    ):
        self.db = db
        self.pricing = pricing_engine
        self.audit = audit
        self.tenant_id = tenant_id
        self.logger = logging.getLogger(__name__)
    
    async def create_quote(
        self,
        risk_result: CalibratedRiskResult,
        shipment_details: Dict[str, Any],
        coverage_options: Dict[str, Any],
        submission_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        created_by_user_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> QuoteDetail:
        """
        Create a new quote from risk assessment.
        """
        self.logger.info("Creating new quote")
        
        # Use provided tenant_id or instance tenant_id
        effective_tenant_id = tenant_id or self.tenant_id
        if not effective_tenant_id:
            raise ValueError("tenant_id is required")
        
        # Build pricing input
        pricing_input = PricingInput(
            risk_result=risk_result,
            cargo_value_usd=Decimal(str(shipment_details["cargo_value_usd"])),
            cargo_type=shipment_details["cargo_type"],
            packaging_quality=shipment_details.get("packaging_quality", "STANDARD"),
            origin_port=shipment_details["origin_port"],
            destination_port=shipment_details["destination_port"],
            transit_days=shipment_details.get("transit_days", 14),
            coverage_type=coverage_options.get("coverage_type", CoverageType.ALL_RISKS),
            coverage_limit_usd=Decimal(str(coverage_options.get("coverage_limit_usd"))) if coverage_options.get("coverage_limit_usd") else None,
            deductible_type=coverage_options.get("deductible_type", DeductibleType.PERCENTAGE),
            deductible_value=Decimal(str(coverage_options.get("deductible_value", "0.01"))),
            policy_start_date=shipment_details.get("departure_date", datetime.utcnow().date()),
            policy_end_date=shipment_details.get("arrival_date", (datetime.utcnow() + timedelta(days=30)).date()),
            customer_id=customer_id,
            pricing_tier=self._get_customer_tier(customer_id)
        )
        
        # Calculate premium
        pricing_result = await self.pricing.calculate_premium(pricing_input)
        
        # Generate quote number
        quote_number = self._generate_quote_number()
        
        # Build terms
        terms = self._build_terms(coverage_options)
        exclusions = self._build_exclusions(coverage_options)
        
        # Build pricing snapshot
        pricing_snapshot = self._serialize_pricing_result(pricing_result)
        
        # Build risk summary
        risk_summary = {
            "overall_risk_score": risk_result.overall_risk_score,
            "risk_grade": pricing_result.risk_grade,
            "expected_loss_pct": risk_result.expected_loss_pct,
            "expected_loss_usd": float(risk_result.expected_loss_usd),
            "var_95": float(risk_result.var_95),
            "var_99": float(risk_result.var_99),
            "layer_scores": risk_result.layer_scores,
            "model_version_id": risk_result.model_version_id,
            "model_version_name": risk_result.model_version_name
        }
        
        # Calculate quote hash for integrity
        quote_data = json.dumps({
            "quote_number": quote_number,
            "pricing": pricing_snapshot,
            "risk": risk_summary,
            "terms": terms
        }, sort_keys=True, default=str)
        quote_hash = hashlib.sha256(quote_data.encode()).hexdigest()
        
        # Create database record
        # Note: submission_id is required by the model, so we need to create a placeholder or use existing
        if not submission_id:
            # In production, would create or find submission
            # For now, use a placeholder
            submission_id = "PLACEHOLDER_SUBMISSION_ID"
        
        quote_model = QuoteModel(
            id=str(uuid4()),
            tenant_id=effective_tenant_id,
            quote_number=quote_number,
            submission_id=submission_id,
            version=1,
            is_latest=True,
            status=QuoteStatus.PENDING.value,
            model_version_id=risk_result.model_version_id,
            risk_run_id=risk_result.input_hash[:26] if len(risk_result.input_hash) >= 26 else risk_result.input_hash,
            pricing_snapshot_json=pricing_snapshot,
            coverage_terms_json={
                "terms": terms,
                "exclusions": exclusions,
                "coverage_type": coverage_options.get("coverage_type", CoverageType.ALL_RISKS).value if isinstance(coverage_options.get("coverage_type"), CoverageType) else coverage_options.get("coverage_type", "ALL_RISKS"),
                "coverage_limit_usd": float(pricing_result.breakdown.coverage_limit),
                "deductible_amount": float(pricing_result.breakdown.deductible_amount),
                "deductible_type": coverage_options.get("deductible_type", DeductibleType.PERCENTAGE).value if isinstance(coverage_options.get("deductible_type"), DeductibleType) else coverage_options.get("deductible_type", "PERCENTAGE")
            },
            risk_summary_json=risk_summary,
            quote_hash=quote_hash,
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=self.DEFAULT_VALIDITY_DAYS),
            issued_at=datetime.utcnow(),
            issued_by_user_id=created_by_user_id
        )
        
        self.db.add(quote_model)
        self.db.commit()
        self.db.refresh(quote_model)
        
        # Build response
        quote_detail = self._to_quote_detail(quote_model, pricing_result)
        
        # Audit
        if self.audit:
            self.audit.append_event(
                event_type="QUOTE",
                action="QUOTE_CREATED",
                entity_type="quote",
                entity_id=str(quote_model.id),
                actor_type="USER" if created_by_user_id else "SYSTEM",
                actor_id=created_by_user_id,
                tenant_id=effective_tenant_id,
                payload={
                    "quote_number": quote_number,
                    "cargo_value": float(shipment_details["cargo_value_usd"]),
                    "premium": float(pricing_result.total_premium_usd),
                    "risk_grade": pricing_result.risk_grade
                }
            )
        
        return quote_detail
    
    async def get_quote(self, quote_id: str) -> Optional[QuoteDetail]:
        """Get quote by ID."""
        quote = self.db.query(QuoteModel).filter(
            QuoteModel.id == quote_id
        ).first()
        
        if not quote:
            return None
        
        # Check if expired
        if quote.status == QuoteStatus.PENDING.value and quote.valid_until < datetime.utcnow():
            quote.status = QuoteStatus.EXPIRED.value
            self.db.commit()
        
        return self._to_quote_detail(quote)
    
    async def list_quotes(
        self,
        customer_id: Optional[str] = None,
        status: Optional[QuoteStatus] = None,
        created_after: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
        limit: int = 50
    ) -> List[QuoteSummary]:
        """List quotes with filters."""
        effective_tenant_id = tenant_id or self.tenant_id
        query = self.db.query(QuoteModel)
        
        if effective_tenant_id:
            query = query.filter(QuoteModel.tenant_id == effective_tenant_id)
        if customer_id:
            # Would filter by customer_id if field exists
            pass
        if status:
            query = query.filter(QuoteModel.status == status.value)
        if created_after:
            query = query.filter(QuoteModel.created_at >= created_after)
        
        # Update expired quotes
        now = datetime.utcnow()
        self.db.query(QuoteModel).filter(
            QuoteModel.status == QuoteStatus.PENDING.value,
            QuoteModel.valid_until < now
        ).update({"status": QuoteStatus.EXPIRED.value})
        self.db.commit()
        
        quotes = query.order_by(QuoteModel.created_at.desc()).limit(limit).all()
        
        return [
            QuoteSummary(
                quote_id=str(q.id),
                quote_number=q.quote_number,
                status=QuoteStatus(q.status),
                cargo_value_usd=Decimal(str(q.pricing_snapshot_json.get("cargo_value", 0))),
                total_premium_usd=Decimal(str(q.pricing_snapshot_json.get("total_premium", 0))),
                risk_grade=q.risk_summary_json.get("risk_grade", "N/A") if q.risk_summary_json else "N/A",
                origin=q.coverage_terms_json.get("origin_port", "N/A") if q.coverage_terms_json else "N/A",
                destination=q.coverage_terms_json.get("destination_port", "N/A") if q.coverage_terms_json else "N/A",
                created_at=q.created_at,
                valid_until=q.valid_until,
                customer_name=None  # Would join with customer table
            )
            for q in quotes
        ]
    
    async def modify_quote(
        self,
        quote_id: str,
        modifications: Dict[str, Any],
        modified_by_user_id: str
    ) -> QuoteDetail:
        """
        Modify a quote and recalculate if needed.
        Note: The existing Quote model is immutable after ISSUED, so modifications create new versions.
        """
        quote = self.db.query(QuoteModel).filter(
            QuoteModel.id == quote_id
        ).first()
        
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")
        
        if quote.status not in [QuoteStatus.DRAFT.value, QuoteStatus.PENDING.value]:
            raise ValueError(f"Cannot modify quote in status {quote.status}")
        
        # For immutable model, create new version
        # This is simplified - in production would properly handle versioning
        quote.status = QuoteStatus.REPLACED.value
        quote.is_latest = False
        
        # Create new version (simplified - would properly copy and modify)
        new_quote = QuoteModel(
            id=str(uuid4()),
            tenant_id=quote.tenant_id,
            quote_number=quote.quote_number,  # Same quote number, new version
            submission_id=quote.submission_id,
            version=quote.version + 1,
            is_latest=True,
            replaces_quote_id=quote.id,
            status=QuoteStatus.PENDING.value,
            model_version_id=quote.model_version_id,
            risk_run_id=quote.risk_run_id,
            pricing_snapshot_json=quote.pricing_snapshot_json.copy(),
            coverage_terms_json=quote.coverage_terms_json.copy(),
            risk_summary_json=quote.risk_summary_json.copy() if quote.risk_summary_json else None,
            quote_hash=quote.quote_hash,  # Would recalculate
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=self.DEFAULT_VALIDITY_DAYS),
            issued_at=datetime.utcnow(),
            issued_by_user_id=modified_by_user_id
        )
        
        # Apply modifications to new quote
        # This is simplified - would properly rebuild pricing
        self.db.add(new_quote)
        self.db.commit()
        self.db.refresh(new_quote)
        
        # Audit
        if self.audit:
            self.audit.append_event(
                event_type="QUOTE",
                action="QUOTE_MODIFIED",
                entity_type="quote",
                entity_id=str(new_quote.id),
                actor_type="USER",
                actor_id=modified_by_user_id,
                tenant_id=quote.tenant_id,
                payload={
                    "old_quote_id": quote_id,
                    "new_version": new_quote.version,
                    "modifications": modifications
                }
            )
        
        return self._to_quote_detail(new_quote)
    
    async def accept_quote(
        self,
        quote_id: str,
        accepted_by_user_id: str,
        acceptance_notes: Optional[str] = None
    ) -> QuoteDetail:
        """
        Accept a quote (customer decision).
        """
        quote = self.db.query(QuoteModel).filter(
            QuoteModel.id == quote_id
        ).first()
        
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")
        
        if quote.status not in [QuoteStatus.PENDING.value, QuoteStatus.ISSUED.value]:
            raise ValueError(f"Cannot accept quote in status {quote.status}")
        
        if quote.valid_until < datetime.utcnow():
            quote.status = QuoteStatus.EXPIRED.value
            self.db.commit()
            raise ValueError("Quote has expired")
        
        quote.status = QuoteStatus.ACCEPTED.value
        quote.accepted_at = datetime.utcnow()
        # Note: accepted_by_user_id would need to be added to model if not exists
        self.db.commit()
        
        # Audit
        if self.audit:
            self.audit.append_event(
                event_type="QUOTE",
                action="QUOTE_ACCEPTED",
                entity_type="quote",
                entity_id=quote_id,
                actor_type="USER",
                actor_id=accepted_by_user_id,
                tenant_id=quote.tenant_id,
                payload={
                    "quote_number": quote.quote_number,
                    "premium": quote.pricing_snapshot_json.get("total_premium", 0)
                }
            )
        
        return self._to_quote_detail(quote)
    
    async def decline_quote(
        self,
        quote_id: str,
        declined_by_user_id: str,
        reason: DeclineReason,
        reason_details: Optional[str] = None
    ) -> QuoteDetail:
        """
        Decline a quote (customer decision).
        """
        quote = self.db.query(QuoteModel).filter(
            QuoteModel.id == quote_id
        ).first()
        
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")
        
        if quote.status not in [QuoteStatus.PENDING.value, QuoteStatus.ISSUED.value]:
            raise ValueError(f"Cannot decline quote in status {quote.status}")
        
        quote.status = QuoteStatus.DECLINED.value
        # Note: decline fields would need to be added to model
        # For now, store in coverage_terms_json
        if not quote.coverage_terms_json:
            quote.coverage_terms_json = {}
        quote.coverage_terms_json["decline_reason"] = reason.value
        quote.coverage_terms_json["decline_reason_details"] = reason_details
        
        self.db.commit()
        
        # Audit
        if self.audit:
            self.audit.append_event(
                event_type="QUOTE",
                action="QUOTE_DECLINED",
                entity_type="quote",
                entity_id=quote_id,
                actor_type="USER",
                actor_id=declined_by_user_id,
                tenant_id=quote.tenant_id,
                payload={
                    "quote_number": quote.quote_number,
                    "reason": reason.value,
                    "details": reason_details
                }
            )
        
        return self._to_quote_detail(quote)
    
    async def bind_quote_to_policy(
        self,
        quote_id: str,
        bound_by_user_id: str
    ) -> str:
        """
        Convert accepted quote to a policy.
        
        Returns policy_id.
        """
        quote = self.db.query(QuoteModel).filter(
            QuoteModel.id == quote_id
        ).first()
        
        if not quote:
            raise ValueError(f"Quote {quote_id} not found")
        
        if quote.status != QuoteStatus.ACCEPTED.value:
            raise ValueError(f"Can only bind accepted quotes. Current status: {quote.status}")
        
        # Create policy (would call policy service)
        # Placeholder - return quote id as policy id for now
        policy_id = str(uuid4())
        
        quote.status = QuoteStatus.BOUND.value
        # Note: policy_id would need to be added to model
        # For now, store in coverage_terms_json
        if not quote.coverage_terms_json:
            quote.coverage_terms_json = {}
        quote.coverage_terms_json["policy_id"] = policy_id
        
        self.db.commit()
        
        # Audit
        if self.audit:
            self.audit.append_event(
                event_type="QUOTE",
                action="QUOTE_BOUND",
                entity_type="quote",
                entity_id=quote_id,
                actor_type="USER",
                actor_id=bound_by_user_id,
                tenant_id=quote.tenant_id,
                payload={
                    "quote_number": quote.quote_number,
                    "policy_id": policy_id
                }
            )
        
        return policy_id
    
    def _generate_quote_number(self) -> str:
        """Generate unique quote number."""
        import random
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_part = random.randint(1000, 9999)
        return f"QT-{timestamp}-{random_part}"
    
    def _get_customer_tier(self, customer_id: Optional[str]) -> PricingTier:
        """Get customer pricing tier."""
        # Would look up customer tier from database
        return PricingTier.STANDARD
    
    def _build_terms(self, coverage_options: Dict[str, Any]) -> Dict[str, Any]:
        """Build terms and conditions."""
        terms = self.DEFAULT_TERMS.copy()
        
        # Add coverage-specific terms
        coverage_type = coverage_options.get("coverage_type")
        if isinstance(coverage_type, CoverageType):
            coverage_type = coverage_type.value
        
        if coverage_type == CoverageType.ALL_RISKS.value:
            terms["coverage_description"] = "All Risks of physical loss or damage"
        elif coverage_type == CoverageType.NAMED_PERILS.value:
            terms["coverage_description"] = "Named perils as specified in policy"
            terms["covered_perils"] = coverage_options.get("named_perils", [
                "Fire", "Explosion", "Vessel sinking/stranding",
                "Collision", "Jettison", "General average"
            ])
        
        return terms
    
    def _build_exclusions(self, coverage_options: Dict[str, Any]) -> List[str]:
        """Build exclusions list."""
        exclusions = self.STANDARD_EXCLUSIONS.copy()
        
        # Add coverage-specific exclusions
        if not coverage_options.get("include_war_risk"):
            exclusions.insert(0, "War, strikes, riots, civil commotion")
        
        return exclusions
    
    def _serialize_pricing_result(self, pricing_result: PricingResult) -> Dict[str, Any]:
        """Serialize pricing result for storage."""
        breakdown = pricing_result.breakdown
        return {
            "total_premium_usd": float(pricing_result.total_premium_usd),
            "rate_per_mille": float(pricing_result.premium_rate_per_mille),
            "cargo_value": float(breakdown.cargo_value),
            "coverage_limit": float(breakdown.coverage_limit),
            "base_rate": float(breakdown.base_rate),
            "base_premium": float(breakdown.base_premium),
            "risk_factor": float(breakdown.risk_factor),
            "risk_adjusted_premium": float(breakdown.risk_adjusted_premium),
            "cargo_factor": float(breakdown.cargo_factor),
            "route_factor": float(breakdown.route_factor),
            "duration_factor": float(breakdown.duration_factor),
            "coverage_factor": float(breakdown.coverage_factor),
            "loadings": [
                {"name": l.name, "amount": float(l.amount)}
                for l in breakdown.loadings
            ],
            "discounts": [
                {"name": d.name, "amount": float(d.amount)}
                for d in breakdown.discounts
            ],
            "net_premium": float(breakdown.net_premium),
            "expenses": float(breakdown.expenses_loading),
            "margin": float(breakdown.profit_margin),
            "deductible_amount": float(breakdown.deductible_amount)
        }
    
    def _to_quote_detail(
        self, 
        quote: QuoteModel,
        pricing_result: Optional[PricingResult] = None
    ) -> QuoteDetail:
        """Convert database model to detail."""
        pricing_snapshot = quote.pricing_snapshot_json or {}
        coverage_terms = quote.coverage_terms_json or {}
        risk_summary = quote.risk_summary_json or {}
        
        return QuoteDetail(
            quote_id=str(quote.id),
            quote_number=quote.quote_number,
            status=QuoteStatus(quote.status),
            pricing_result=pricing_result,
            risk_score=risk_summary.get("overall_risk_score", 0.0),
            risk_grade=risk_summary.get("risk_grade", "N/A"),
            risk_factors=risk_summary.get("layer_scores", {}),
            origin_port=coverage_terms.get("origin_port", "N/A"),
            destination_port=coverage_terms.get("destination_port", "N/A"),
            cargo_type=coverage_terms.get("cargo_type", "N/A"),
            cargo_value_usd=Decimal(str(pricing_snapshot.get("cargo_value", 0))),
            container_count=coverage_terms.get("container_count", 1),
            transit_days=coverage_terms.get("transit_days", 14),
            coverage_type=coverage_terms.get("coverage_type", "ALL_RISKS"),
            coverage_limit_usd=Decimal(str(pricing_snapshot.get("coverage_limit", 0))),
            deductible_amount=Decimal(str(pricing_snapshot.get("deductible_amount", 0))),
            terms_and_conditions=coverage_terms.get("terms", {}),
            exclusions=coverage_terms.get("exclusions", []),
            customer_id=None,  # Would extract from submission
            customer_name=None,
            created_at=quote.created_at,
            modified_at=quote.issued_at or quote.created_at,
            valid_from=quote.valid_from,
            valid_until=quote.valid_until,
            version=quote.version,
            previous_versions=[]  # Would query for previous versions
        )
