"""
Quote management service with versioning.

Quotes are immutable after issuance. Any change creates a new version.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.quote import Quote
from app.modules.underwriting.models import UnderwritingSubmission
from app.modules.risk_runs.models import RiskRun
from app.models.evidence_bundle import EvidenceBundle
from app.core.audit_ledger.ledger import AuditLedger

logger = logging.getLogger(__name__)


class QuoteService:
    """Service for managing quotes."""
    
    DEFAULT_VALIDITY_DAYS = 30
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize quote service.
        
        Args:
            db: Database session
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def create_quote(
        self,
        tenant_id: str,
        submission_id: str,
        risk_run_id: str,
        pricing_input: Dict[str, Any],
        coverage_terms: Dict[str, Any],
        created_by: str,
        evidence_bundle_id: Optional[str] = None,
        validity_days: Optional[int] = None
    ) -> Quote:
        """
        Create a new quote in DRAFT status.
        
        Quote is not yet issued - can still be modified by creating new drafts.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            submission_id: Submission ID (ULID string)
            risk_run_id: Risk run ID (ULID string)
            pricing_input: Pricing input dictionary
            coverage_terms: Coverage terms dictionary
            created_by: User ID creating (ULID string)
            evidence_bundle_id: Optional evidence bundle ID (UUID string)
            validity_days: Optional validity period in days (default 30)
            
        Returns:
            Created Quote instance
        """
        # Verify submission exists and is in valid state
        submission = self.db.query(UnderwritingSubmission).filter(
            UnderwritingSubmission.id == submission_id,
            UnderwritingSubmission.tenant_id == tenant_id
        ).first()
        
        if not submission:
            raise SubmissionNotFoundError(f"Submission {submission_id} not found")
        
        if submission.status.value not in ['UNDER_REVIEW', 'QUOTED']:
            raise InvalidSubmissionStateError(
                f"Cannot create quote for submission in {submission.status.value} status"
            )
        
        # Get risk run and verify
        risk_run = self.db.query(RiskRun).filter(
            RiskRun.id == risk_run_id
        ).first()
        
        if not risk_run or risk_run.status.value != 'SUCCEEDED':
            raise InvalidRiskRunError(f"Risk run {risk_run_id} not found or not succeeded")
        
        # Generate quote number
        quote_number = self._generate_quote_number(tenant_id, submission)
        
        # Get version number
        existing_versions = self.db.query(Quote).filter(
            Quote.submission_id == submission_id
        ).count()
        version = existing_versions + 1
        
        # Calculate pricing
        pricing_snapshot = self._calculate_pricing(pricing_input, risk_run)
        
        # Build risk summary from run
        result_json = risk_run.result_json or {}
        risk_summary = {
            "overall_risk_score": result_json.get('overall_risk_score', 0.5),
            "risk_factors": result_json.get('risk_factors', {}),
            "var_95": result_json.get('var_95', 0.0),
            "var_99": result_json.get('var_99', 0.0),
            "expected_loss_cents": int(
                result_json.get('expected_loss', 0.05) * pricing_input.get('insured_value_cents', 0)
            )
        }
        
        # Validity period
        validity_days = validity_days or self.DEFAULT_VALIDITY_DAYS
        valid_from = datetime.utcnow()
        valid_until = valid_from + timedelta(days=validity_days)
        
        # Mark previous versions as not latest
        self.db.query(Quote).filter(
            Quote.submission_id == submission_id,
            Quote.is_latest == True
        ).update({'is_latest': False})
        
        # Create quote
        import uuid
        quote = Quote(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            quote_number=quote_number,
            submission_id=submission_id,
            version=version,
            is_latest=True,
            status='DRAFT',
            model_version_id=risk_run.model_version_id,
            risk_run_id=risk_run_id,
            evidence_bundle_id=evidence_bundle_id,
            pricing_snapshot_json=pricing_snapshot,
            coverage_terms_json=coverage_terms,
            risk_summary_json=risk_summary,
            quote_hash='',  # Computed on issue
            valid_from=valid_from,
            valid_until=valid_until,
            created_at=datetime.utcnow()
        )
        
        self.db.add(quote)
        self.db.commit()
        self.db.refresh(quote)
        
        # Audit
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="QUOTE",
            action="CREATED",
            entity_type="quote",
            entity_id=quote.id,
            actor_type="USER",
            actor_id=created_by,
            payload={
                "quote_number": quote_number,
                "version": version,
                "premium_cents": pricing_snapshot.get('premium_cents', 0)
            }
        )
        
        logger.info(f"Created quote: {quote.id} ({quote_number} v{version})")
        
        return quote
    
    def issue_quote(
        self,
        quote_id: str,
        issued_by: str
    ) -> Quote:
        """
        Issue a quote, making it immutable.
        
        Computes quote_hash and transitions to ISSUED status.
        After issuance, quote cannot be modified - only replaced.
        
        Args:
            quote_id: Quote ID (UUID string)
            issued_by: User ID issuing (ULID string)
            
        Returns:
            Updated Quote instance
        """
        quote = self._get_quote(quote_id)
        
        if quote.status != 'DRAFT':
            raise QuoteAlreadyIssuedError(f"Quote is already {quote.status}")
        
        # Verify evidence bundle is sealed (if present)
        if quote.evidence_bundle_id:
            bundle = self.db.query(EvidenceBundle).filter(
                EvidenceBundle.id == quote.evidence_bundle_id
            ).first()
            if not bundle or bundle.status != 'SEALED':
                raise EvidenceBundleNotSealedError(
                    "Evidence bundle must be sealed before issuing quote"
                )
        
        # Compute quote hash
        quote_hash = self._compute_quote_hash(quote)
        
        # Update quote
        quote.status = 'ISSUED'
        quote.quote_hash = quote_hash
        quote.issued_at = datetime.utcnow()
        quote.issued_by_user_id = issued_by
        
        self.db.commit()
        self.db.refresh(quote)
        
        # Audit
        self.audit.append_event(
            tenant_id=quote.tenant_id,
            event_type="QUOTE",
            action="ISSUED",
            entity_type="quote",
            entity_id=quote.id,
            actor_type="USER",
            actor_id=issued_by,
            payload={
                "quote_hash": quote_hash,
                "model_version_id": quote.model_version_id,
                "risk_run_id": quote.risk_run_id
            }
        )
        
        logger.info(f"Issued quote: {quote.id} (hash: {quote_hash[:16]}...)")
        
        return quote
    
    def revise_quote(
        self,
        quote_id: str,
        new_pricing_input: Dict[str, Any],
        new_coverage_terms: Optional[Dict[str, Any]],
        revised_by: str,
        revision_reason: str
    ) -> Quote:
        """
        Create a new version of an issued quote.
        
        The original quote is marked as REPLACED.
        Returns the new quote in DRAFT status.
        
        Args:
            quote_id: Original quote ID (UUID string)
            new_pricing_input: New pricing input dictionary
            new_coverage_terms: Optional new coverage terms (uses original if None)
            revised_by: User ID revising (ULID string)
            revision_reason: Reason for revision
            
        Returns:
            New Quote instance (DRAFT status)
        """
        original = self._get_quote(quote_id)
        
        if original.status not in ['ISSUED', 'DRAFT']:
            raise CannotReviseQuoteError(
                f"Cannot revise quote in {original.status} status"
            )
        
        # Get risk run for pricing calculation
        risk_run = self.db.query(RiskRun).filter(
            RiskRun.id == original.risk_run_id
        ).first()
        
        if not risk_run:
            raise InvalidRiskRunError(f"Risk run {original.risk_run_id} not found")
        
        # Mark original as replaced (if issued)
        if original.status == 'ISSUED':
            original.status = 'REPLACED'
            original.is_latest = False
        
        # Calculate new pricing
        pricing_snapshot = self._calculate_pricing(new_pricing_input, risk_run)
        
        # Use new coverage terms or original
        coverage_terms = new_coverage_terms or original.coverage_terms_json
        
        # Build risk summary
        result_json = risk_run.result_json or {}
        risk_summary = {
            "overall_risk_score": result_json.get('overall_risk_score', 0.5),
            "risk_factors": result_json.get('risk_factors', {}),
            "var_95": result_json.get('var_95', 0.0),
            "var_99": result_json.get('var_99', 0.0),
            "expected_loss_cents": int(
                result_json.get('expected_loss', 0.05) * new_pricing_input.get('insured_value_cents', 0)
            )
        }
        
        # Get version number
        existing_versions = self.db.query(Quote).filter(
            Quote.submission_id == original.submission_id
        ).count()
        version = existing_versions + 1
        
        # Mark previous versions as not latest
        self.db.query(Quote).filter(
            Quote.submission_id == original.submission_id,
            Quote.is_latest == True
        ).update({'is_latest': False})
        
        # Create new version
        import uuid
        new_quote = Quote(
            id=str(uuid.uuid4()),
            tenant_id=original.tenant_id,
            quote_number=original.quote_number,
            submission_id=original.submission_id,
            version=version,
            is_latest=True,
            status='DRAFT',
            replaces_quote_id=original.id,
            model_version_id=original.model_version_id,
            risk_run_id=original.risk_run_id,
            evidence_bundle_id=original.evidence_bundle_id,
            pricing_snapshot_json=pricing_snapshot,
            coverage_terms_json=coverage_terms,
            risk_summary_json=risk_summary,
            quote_hash='',  # Computed on issue
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=self.DEFAULT_VALIDITY_DAYS),
            created_at=datetime.utcnow()
        )
        
        self.db.add(new_quote)
        self.db.commit()
        self.db.refresh(new_quote)
        
        # Audit
        self.audit.append_event(
            tenant_id=original.tenant_id,
            event_type="QUOTE",
            action="REVISED",
            entity_type="quote",
            entity_id=new_quote.id,
            actor_type="USER",
            actor_id=revised_by,
            payload={
                "original_quote_id": original.id,
                "original_version": original.version,
                "new_version": new_quote.version,
                "revision_reason": revision_reason
            }
        )
        
        logger.info(
            f"Revised quote: {original.id} v{original.version} -> {new_quote.id} v{new_quote.version}"
        )
        
        return new_quote
    
    def accept_quote(
        self,
        quote_id: str,
        accepted_by: str
    ) -> Quote:
        """
        Accept a quote (customer acceptance).
        
        This prepares the quote for binding into a policy.
        
        Args:
            quote_id: Quote ID (UUID string)
            accepted_by: User ID accepting (ULID string)
            
        Returns:
            Updated Quote instance
        """
        quote = self._get_quote(quote_id)
        
        if quote.status != 'ISSUED':
            raise QuoteNotIssuedError(f"Can only accept ISSUED quotes, current: {quote.status}")
        
        if datetime.utcnow() > quote.valid_until:
            raise QuoteExpiredError("Quote has expired")
        
        quote.status = 'ACCEPTED'
        quote.accepted_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(quote)
        
        # Audit
        self.audit.append_event(
            tenant_id=quote.tenant_id,
            event_type="QUOTE",
            action="ACCEPTED",
            entity_type="quote",
            entity_id=quote.id,
            actor_type="USER",
            actor_id=accepted_by,
            payload={}
        )
        
        logger.info(f"Accepted quote: {quote.id}")
        
        return quote
    
    def get_quote_with_versions(self, submission_id: str) -> List[Quote]:
        """
        Get all quote versions for a submission.
        
        Args:
            submission_id: Submission ID (ULID string)
            
        Returns:
            List of Quote instances ordered by version descending
        """
        return self.db.query(Quote).filter(
            Quote.submission_id == submission_id
        ).order_by(Quote.version.desc()).all()
    
    def get_latest_quote(self, submission_id: str) -> Optional[Quote]:
        """
        Get the latest quote for a submission.
        
        Args:
            submission_id: Submission ID (ULID string)
            
        Returns:
            Latest Quote instance or None
        """
        return self.db.query(Quote).filter(
            Quote.submission_id == submission_id,
            Quote.is_latest == True
        ).first()
    
    def verify_quote_integrity(self, quote_id: str) -> Dict[str, Any]:
        """
        Verify quote hash integrity.
        
        Args:
            quote_id: Quote ID (UUID string)
            
        Returns:
            Dictionary with verification results
        """
        quote = self._get_quote(quote_id)
        
        if quote.status == 'DRAFT':
            return {
                "valid": None,
                "message": "Quote not yet issued",
                "stored_hash": None,
                "computed_hash": None,
                "verified_at": datetime.utcnow().isoformat()
            }
        
        computed_hash = self._compute_quote_hash(quote)
        
        return {
            "valid": computed_hash == quote.quote_hash,
            "stored_hash": quote.quote_hash,
            "computed_hash": computed_hash,
            "verified_at": datetime.utcnow().isoformat()
        }
    
    def expire_quotes(self) -> int:
        """
        Expire quotes past their validity date.
        
        Should be run periodically (e.g., daily cron job).
        
        Returns:
            Count of expired quotes
        """
        now = datetime.utcnow()
        
        expired = self.db.query(Quote).filter(
            Quote.status == 'ISSUED',
            Quote.valid_until < now
        ).all()
        
        for quote in expired:
            quote.status = 'EXPIRED'
        
        self.db.commit()
        
        logger.info(f"Expired {len(expired)} quotes")
        
        return len(expired)
    
    def _get_quote(self, quote_id: str) -> Quote:
        """
        Get quote by ID.
        
        Args:
            quote_id: Quote ID (UUID string)
            
        Returns:
            Quote instance
            
        Raises:
            QuoteNotFoundError: If quote not found
        """
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise QuoteNotFoundError(f"Quote {quote_id} not found")
        return quote
    
    def _generate_quote_number(self, tenant_id: str, submission: UnderwritingSubmission) -> str:
        """
        Generate quote number based on submission.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            submission: UnderwritingSubmission instance
            
        Returns:
            Quote number string
        """
        # Format: QTE-{submission_number suffix}
        if submission.submission_number:
            sub_suffix = submission.submission_number.split('-')[-1]
            return f"QTE-{sub_suffix}"
        else:
            # Fallback if submission_number not set
            date_part = datetime.utcnow().strftime("%Y%m%d")
            count = self.db.query(Quote).filter(
                Quote.tenant_id == tenant_id,
                Quote.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            return f"QTE-{date_part}-{count + 1:05d}"
    
    def _calculate_pricing(
        self,
        pricing_input: Dict[str, Any],
        risk_run: RiskRun
    ) -> Dict[str, Any]:
        """
        Calculate premium based on risk and input parameters.
        
        Args:
            pricing_input: Pricing input dictionary
            risk_run: RiskRun instance
            
        Returns:
            Pricing snapshot dictionary
        """
        result_json = risk_run.result_json or {}
        
        # Base premium calculation
        risk_score = result_json.get('overall_risk_score', 0.5)
        expected_loss = result_json.get('expected_loss', 0.05)
        insured_value_cents = pricing_input.get('insured_value_cents', 0)
        
        # Simple pricing model (should be more sophisticated in production)
        base_rate = expected_loss * 1.5  # 50% margin over expected loss
        risk_loading = risk_score * 0.02  # Additional loading based on risk
        
        total_rate = base_rate + risk_loading
        base_premium = int(insured_value_cents * total_rate)
        
        # Apply minimum premium
        min_premium = pricing_input.get('minimum_premium_cents', 10000)  # $100 minimum
        base_premium = max(base_premium, min_premium)
        
        # Taxes and fees (simplified)
        taxes_fees = int(base_premium * 0.05)
        
        total_premium = base_premium + taxes_fees
        
        return {
            "premium_cents": total_premium,
            "currency": pricing_input.get('currency', 'USD'),
            "premium_breakdown": {
                "base_premium_cents": base_premium,
                "risk_loading_cents": int(insured_value_cents * risk_loading),
                "taxes_fees_cents": taxes_fees
            },
            "insured_value_cents": insured_value_cents,
            "deductible_cents": pricing_input.get('deductible_cents', 0),
            "rate_per_mille": round(total_premium / insured_value_cents * 1000, 2) if insured_value_cents > 0 else 0.0,
            "risk_score_used": risk_score,
            "expected_loss_rate": expected_loss
        }
    
    def _compute_quote_hash(self, quote: Quote) -> str:
        """
        Compute deterministic hash of quote content.
        
        Args:
            quote: Quote instance
            
        Returns:
            SHA256 hash string
        """
        hashable = {
            "quote_number": quote.quote_number,
            "version": quote.version,
            "submission_id": quote.submission_id,
            "model_version_id": quote.model_version_id,
            "risk_run_id": quote.risk_run_id,
            "pricing_snapshot": quote.pricing_snapshot_json,
            "coverage_terms": quote.coverage_terms_json,
            "risk_summary": quote.risk_summary_json,
            "valid_from": quote.valid_from.isoformat() if quote.valid_from else None,
            "valid_until": quote.valid_until.isoformat() if quote.valid_until else None
        }
        
        canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()


# Exception classes
class QuoteNotFoundError(Exception):
    """Quote not found"""
    pass


class SubmissionNotFoundError(Exception):
    """Submission not found"""
    pass


class InvalidSubmissionStateError(Exception):
    """Invalid submission state for quote creation"""
    pass


class InvalidRiskRunError(Exception):
    """Invalid risk run"""
    pass


class QuoteAlreadyIssuedError(Exception):
    """Quote already issued"""
    pass


class EvidenceBundleNotSealedError(Exception):
    """Evidence bundle not sealed"""
    pass


class CannotReviseQuoteError(Exception):
    """Cannot revise quote"""
    pass


class QuoteNotIssuedError(Exception):
    """Quote not issued"""
    pass


class QuoteExpiredError(Exception):
    """Quote expired"""
    pass
