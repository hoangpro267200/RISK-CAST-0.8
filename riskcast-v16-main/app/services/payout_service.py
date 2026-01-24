"""
Payout management service.

Handles payout lifecycle with dual-control approvals.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
import json
import logging

from sqlalchemy.orm import Session

from app.modules.claims.models import Payout, PayoutStatus, Claim, ClaimStatus
from app.modules.underwriting.models import Policy
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class PayoutService:
    """Service for managing payouts."""
    
    # Threshold for requiring additional authorization
    AUTHORIZATION_THRESHOLD_CENTS = 10000_00  # $10,000
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize payout service.
        
        Args:
            db: Database session
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def create_claim_payout(
        self,
        claim_id: str,
        proposed_by: str
    ) -> Payout:
        """
        Create a payout proposal for an approved claim.
        
        Args:
            claim_id: Claim ID (ULID string)
            proposed_by: User ID proposing (ULID string)
            
        Returns:
            Created Payout instance
        """
        claim = self.db.query(Claim).filter(Claim.id == claim_id).first()
        
        if not claim:
            raise ClaimNotFoundError(f"Claim {claim_id} not found")
        
        if claim.status != ClaimStatus.APPROVED:
            raise InvalidClaimStateError("Claim must be APPROVED for payout")
        
        if not claim.approved_amount_cents:
            raise InvalidClaimStateError("Claim has no approved amount")
        
        # Get policy
        policy = self.db.query(Policy).filter(Policy.id == claim.policy_id).first()
        
        # Build calculation snapshot
        calculation = {
            "gross_amount_cents": claim.fnol_json.get('estimated_loss_cents', 0),
            "deductible_cents": (policy.terms_json or {}).get('deductible_cents', 0),
            "net_amount_cents": claim.approved_amount_cents,
            "calculation_method": "ADJUDICATED",
            "adjudication": claim.adjudication_json,
            "adjustments": (claim.adjudication_json or {}).get('adjustments', [])
        }
        calculation_hash = self._compute_calculation_hash(calculation)
        
        # Generate payout number
        payout_number = self._generate_payout_number(claim.tenant_id)
        
        payout = Payout(
            id=generate_ulid(),
            tenant_id=claim.tenant_id,
            payout_number=payout_number,
            payout_type='CLAIM',
            policy_id=claim.policy_id,
            claim_id=claim_id,
            status=PayoutStatus.PROPOSED,
            amount_cents=claim.approved_amount_cents,
            currency=claim.approved_currency or 'USD',
            calculation_snapshot_json=calculation,
            calculation_hash=calculation_hash,
            recipient_json=policy.policyholder_json,
            proposed_by_user_id=proposed_by,
            proposed_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        self.db.add(payout)
        self.db.commit()
        self.db.refresh(payout)
        
        # Audit
        self.audit.append_event(
            tenant_id=claim.tenant_id,
            event_type="PAYOUT",
            action="PROPOSED",
            entity_type="payout",
            entity_id=payout.id,
            actor_type="USER",
            actor_id=proposed_by,
            payload={
                "payout_number": payout_number,
                "claim_id": claim_id,
                "amount_cents": claim.approved_amount_cents,
                "calculation_hash": calculation_hash
            }
        )
        
        logger.info(f"Created payout proposal: {payout.id} ({payout_number})")
        
        return payout
    
    def approve_payout(
        self,
        payout_id: str,
        approved_by: str
    ) -> Payout:
        """
        Approve a payout proposal.
        
        For amounts below threshold, this also authorizes.
        For amounts above threshold, separate authorization required.
        
        Args:
            payout_id: Payout ID (ULID string)
            approved_by: User ID approving (ULID string)
            
        Returns:
            Updated Payout instance
        """
        payout = self._get_payout(payout_id)
        
        if payout.status != PayoutStatus.PROPOSED:
            raise InvalidPayoutStateError(f"Payout is {payout.status.value}, must be PROPOSED")
        
        # Cannot approve your own proposal
        if payout.proposed_by_user_id == approved_by:
            raise DualControlViolationError(
                "Cannot approve your own payout proposal"
            )
        
        payout.status = PayoutStatus.APPROVED
        payout.approved_by_user_id = approved_by
        payout.approved_at = datetime.utcnow()
        payout.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(payout)
        
        # Audit
        self.audit.append_event(
            tenant_id=payout.tenant_id,
            event_type="PAYOUT",
            action="APPROVED",
            entity_type="payout",
            entity_id=payout.id,
            actor_type="USER",
            actor_id=approved_by,
            payload={"amount_cents": payout.amount_cents}
        )
        
        # Auto-authorize if below threshold
        if payout.amount_cents < self.AUTHORIZATION_THRESHOLD_CENTS:
            return self.authorize_payout(payout_id, approved_by)
        
        logger.info(f"Approved payout: {payout.id}")
        
        return payout
    
    def authorize_payout(
        self,
        payout_id: str,
        authorized_by: str
    ) -> Payout:
        """
        Authorize a payout for processing.
        
        This is the final approval step before payment.
        
        Args:
            payout_id: Payout ID (ULID string)
            authorized_by: User ID authorizing (ULID string)
            
        Returns:
            Updated Payout instance
        """
        payout = self._get_payout(payout_id)
        
        if payout.status != PayoutStatus.APPROVED:
            raise InvalidPayoutStateError(
                f"Payout must be APPROVED for authorization, is {payout.status.value}"
            )
        
        # For high amounts, require different person from approver
        if payout.amount_cents >= self.AUTHORIZATION_THRESHOLD_CENTS:
            if payout.approved_by_user_id == authorized_by:
                raise DualControlViolationError(
                    "High-value payouts require different authorizer"
                )
        
        payout.status = PayoutStatus.AUTHORIZED
        payout.authorized_by_user_id = authorized_by
        payout.authorized_at = datetime.utcnow()
        payout.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(payout)
        
        # Audit (critical - authorization)
        self.audit.append_event(
            tenant_id=payout.tenant_id,
            event_type="PAYOUT",
            action="AUTHORIZED",
            entity_type="payout",
            entity_id=payout.id,
            actor_type="USER",
            actor_id=authorized_by,
            payload={
                "amount_cents": payout.amount_cents,
                "proposed_by": payout.proposed_by_user_id,
                "approved_by": payout.approved_by_user_id,
                "authorized_by": authorized_by
            }
        )
        
        logger.info(f"Authorized payout: {payout.id}")
        
        return payout
    
    def process_payment(
        self,
        payout_id: str,
        payment_method: str,
        processed_by: str
    ) -> Payout:
        """
        Begin payment processing.
        
        Args:
            payout_id: Payout ID (ULID string)
            payment_method: Payment method (e.g., "WIRE", "ACH")
            processed_by: User ID processing (ULID string)
            
        Returns:
            Updated Payout instance
        """
        payout = self._get_payout(payout_id)
        
        if payout.status != PayoutStatus.AUTHORIZED:
            raise InvalidPayoutStateError("Payout must be AUTHORIZED")
        
        payout.status = PayoutStatus.PROCESSING
        payout.payment_method = payment_method
        payout.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(payout)
        
        logger.info(f"Processing payment for payout: {payout.id}")
        
        return payout
    
    def confirm_payment(
        self,
        payout_id: str,
        payment_reference: str,
        confirmation_data: Dict[str, Any],
        confirmed_by: str
    ) -> Payout:
        """
        Confirm payment completion.
        
        Args:
            payout_id: Payout ID (ULID string)
            payment_reference: Payment reference number
            confirmation_data: Payment confirmation data
            confirmed_by: User ID confirming (ULID string)
            
        Returns:
            Updated Payout instance
        """
        payout = self._get_payout(payout_id)
        
        if payout.status != PayoutStatus.PROCESSING:
            raise InvalidPayoutStateError("Payout must be PROCESSING")
        
        payout.status = PayoutStatus.PAID
        payout.payment_reference = payment_reference
        payout.payment_confirmation_json = confirmation_data
        payout.paid_at = datetime.utcnow()
        payout.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(payout)
        
        # Update linked claim
        if payout.claim_id:
            claim = self.db.query(Claim).filter(Claim.id == payout.claim_id).first()
            if claim:
                claim.payout_id = payout.id
                # Claims service will transition to PAID
                self.db.commit()
        
        # Audit
        self.audit.append_event(
            tenant_id=payout.tenant_id,
            event_type="PAYOUT",
            action="PAID",
            entity_type="payout",
            entity_id=payout.id,
            actor_type="USER",
            actor_id=confirmed_by,
            payload={
                "payment_reference": payment_reference,
                "amount_cents": payout.amount_cents
            }
        )
        
        # Update loss experience record
        try:
            from app.services.loss_analytics_service import LossAnalyticsService
            loss_service = LossAnalyticsService(self.db)
            loss_service.update_from_payout(payout.id)
        except Exception as e:
            logger.warning(f"Could not update loss experience from payout: {e}")
        
        logger.info(f"Confirmed payment for payout: {payout.id}")
        
        return payout
    
    def fail_payment(
        self,
        payout_id: str,
        failure_reason: str,
        failed_by: str
    ) -> Payout:
        """
        Record payment failure.
        
        Args:
            payout_id: Payout ID (ULID string)
            failure_reason: Reason for failure
            failed_by: User ID recording failure (ULID string)
            
        Returns:
            Updated Payout instance
        """
        payout = self._get_payout(payout_id)
        
        payout.status = PayoutStatus.FAILED
        payout.failure_reason = failure_reason
        payout.retry_count = (payout.retry_count or 0) + 1
        payout.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(payout)
        
        # Audit
        self.audit.append_event(
            tenant_id=payout.tenant_id,
            event_type="PAYOUT",
            action="FAILED",
            entity_type="payout",
            entity_id=payout.id,
            actor_type="USER",
            actor_id=failed_by,
            payload={
                "failure_reason": failure_reason,
                "retry_count": payout.retry_count
            }
        )
        
        logger.warning(f"Payment failed for payout: {payout.id}, reason: {failure_reason}")
        
        return payout
    
    def cancel_payout(
        self,
        payout_id: str,
        reason: str,
        cancelled_by: str
    ) -> Payout:
        """
        Cancel a payout (before payment).
        
        Args:
            payout_id: Payout ID (ULID string)
            reason: Cancellation reason
            cancelled_by: User ID cancelling (ULID string)
            
        Returns:
            Updated Payout instance
        """
        payout = self._get_payout(payout_id)
        
        if payout.status in [PayoutStatus.PAID, PayoutStatus.PROCESSING]:
            raise InvalidPayoutStateError(
                f"Cannot cancel payout in {payout.status.value} status"
            )
        
        payout.status = PayoutStatus.CANCELLED
        payout.failure_reason = reason
        payout.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(payout)
        
        # Audit
        self.audit.append_event(
            tenant_id=payout.tenant_id,
            event_type="PAYOUT",
            action="CANCELLED",
            entity_type="payout",
            entity_id=payout.id,
            actor_type="USER",
            actor_id=cancelled_by,
            payload={"reason": reason}
        )
        
        logger.info(f"Cancelled payout: {payout.id}")
        
        return payout
    
    def _get_payout(self, payout_id: str) -> Payout:
        """
        Get payout by ID.
        
        Args:
            payout_id: Payout ID (ULID string)
            
        Returns:
            Payout instance
            
        Raises:
            PayoutNotFoundError: If payout not found
        """
        payout = self.db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            raise PayoutNotFoundError(f"Payout {payout_id} not found")
        return payout
    
    def _generate_payout_number(self, tenant_id: str) -> str:
        """
        Generate unique payout number.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            
        Returns:
            Payout number string
        """
        date_part = datetime.utcnow().strftime("%Y%m%d")
        count = self.db.query(Payout).filter(
            Payout.tenant_id == tenant_id
        ).count()
        return f"PAY-{date_part}-{count + 1:06d}"
    
    def _compute_calculation_hash(self, calculation: Dict[str, Any]) -> str:
        """
        Compute hash of calculation snapshot.
        
        Args:
            calculation: Calculation dictionary
            
        Returns:
            SHA256 hash string
        """
        canonical = json.dumps(calculation, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()


# Exception classes
class PayoutNotFoundError(Exception):
    """Payout not found"""
    pass


class ClaimNotFoundError(Exception):
    """Claim not found"""
    pass


class InvalidClaimStateError(Exception):
    """Invalid claim state for operation"""
    pass


class InvalidPayoutStateError(Exception):
    """Invalid payout state for operation"""
    pass


class DualControlViolationError(Exception):
    """Dual control violation"""
    pass
