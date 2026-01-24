"""
Policy management service.

Handles policy binding, lifecycle, and document generation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib
import json
import logging

from sqlalchemy.orm import Session

from app.modules.underwriting.models import Policy, PolicyEvent, PolicyStatus
from app.models.quote import Quote
from app.modules.underwriting.models import UnderwritingSubmission, SubmissionStatus
from app.modules.risk_runs.models import RiskRun
from app.models.evidence_bundle import EvidenceBundle
# EvidenceObject import - check if exists
try:
    from app.models.evidence import EvidenceObject
except ImportError:
    # Fallback if evidence model not found
    EvidenceObject = None
from app.modules.model_versioning.models import RiskModelVersion
from app.core.audit_ledger.ledger import AuditLedger
from app.services.evidence_service import EvidenceService

logger = logging.getLogger(__name__)


class PolicyService:
    """Service for managing policies."""
    
    def __init__(
        self,
        db: Session,
        audit: Optional[AuditLedger] = None,
        evidence_service: Optional[EvidenceService] = None,
        document_generator: Optional[PolicyDocumentGenerator] = None
    ):
        """
        Initialize policy service.
        
        Args:
            db: Database session
            audit: Optional audit ledger
            evidence_service: Optional evidence service
            document_generator: Optional document generator
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
        self.evidence_service = evidence_service
        from app.services.policy_document_generator import PolicyDocumentGenerator as DocGenerator
        self.document_generator = document_generator or DocGenerator()
    
    def bind_policy(
        self,
        tenant_id: str,
        quote_id: str,
        bound_by: str,
        effective_from: Optional[datetime] = None,
        effective_to: Optional[datetime] = None
    ) -> Policy:
        """
        Bind a policy from an accepted quote.
        
        This is the critical step that:
        1. Pins all references (quote, model, run, evidence)
        2. Creates immutable policy record
        3. Generates policy document
        4. Transitions submission to BOUND
        
        Args:
            tenant_id: Tenant ID (ULID string)
            quote_id: Accepted quote ID (UUID string)
            bound_by: User performing the binding (ULID string)
            effective_from: Coverage start (defaults to now)
            effective_to: Coverage end (defaults to 90 days from now)
            
        Returns:
            Created Policy instance
        """
        # 1. Get and validate quote
        quote = self.db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.tenant_id == tenant_id
        ).first()
        
        if not quote:
            raise QuoteNotFoundError(f"Quote {quote_id} not found")
        
        if quote.status != 'ACCEPTED':
            raise QuoteNotAcceptedError(
                f"Quote must be ACCEPTED to bind, current: {quote.status}"
            )
        
        # 2. Get submission and verify KYC
        submission = self.db.query(UnderwritingSubmission).filter(
            UnderwritingSubmission.id == quote.submission_id
        ).first()
        
        if not submission:
            raise SubmissionNotFoundError(f"Submission {quote.submission_id} not found")
        
        applicant = submission.applicant_json or {}
        if applicant.get('kyc_status') != 'COMPLETED':
            raise KYCNotCompletedError("KYC must be completed before binding")
        
        # 3. Verify evidence bundle is sealed
        if quote.evidence_bundle_id:
            bundle = self.db.query(EvidenceBundle).filter(
                EvidenceBundle.id == quote.evidence_bundle_id
            ).first()
            if not bundle or bundle.status != 'SEALED':
                raise EvidenceBundleNotSealedError(
                    "Evidence bundle must be sealed before binding"
                )
        
        # 4. Generate policy number
        policy_number = self._generate_policy_number(tenant_id)
        
        # 5. Determine coverage period
        if not effective_from:
            effective_from = datetime.utcnow()
        if not effective_to:
            # Default: 90 days or based on shipment
            effective_to = effective_from + timedelta(days=90)
        
        # 6. Build policy terms from quote
        terms = {
            "coverage_type": quote.coverage_terms_json.get('coverage_type'),
            "insured_value_cents": quote.pricing_snapshot_json.get('insured_value_cents'),
            "deductible_cents": quote.pricing_snapshot_json.get('deductible_cents'),
            "premium_cents": quote.pricing_snapshot_json.get('premium_cents'),
            "currency": quote.pricing_snapshot_json.get('currency'),
            "extensions": quote.coverage_terms_json.get('extensions', []),
            "exclusions": quote.coverage_terms_json.get('exclusions', []),
            "limits": quote.coverage_terms_json.get('limits', {}),
            "conditions": quote.coverage_terms_json.get('conditions', [])
        }
        
        # 7. Premium details
        premium = {
            "total_premium_cents": quote.pricing_snapshot_json.get('premium_cents'),
            "currency": quote.pricing_snapshot_json.get('currency'),
            "breakdown": quote.pricing_snapshot_json.get('premium_breakdown'),
            "payment_status": "PENDING",
            "paid_at": None
        }
        
        # 8. Create policy
        from app.shared.utils import generate_ulid
        
        policy = Policy(
            id=generate_ulid(),
            tenant_id=tenant_id,
            policy_number=policy_number,
            status=PolicyStatus.ACTIVE,
            
            # Pinned references
            submission_id=quote.submission_id,
            quote_id=quote.id,
            model_version_id=quote.model_version_id,
            risk_run_id=quote.risk_run_id,
            evidence_bundle_id=quote.evidence_bundle_id,
            
            # Terms and premium
            terms_json=terms,
            premium_json=premium,
            risk_snapshot_json=quote.risk_summary_json,
            
            # Coverage period
            effective_from=effective_from,
            effective_to=effective_to,
            
            # Policyholder
            policyholder_json=submission.applicant_json,
            policyholder_pii=submission.applicant_pii,
            
            # Shipment reference
            shipment_id=submission.shipment_id,
            corridor_id=submission.corridor_id,
            
            # Binding
            bound_by_user_id=bound_by,
            bound_at=datetime.utcnow(),
            
            # Hash computed after all fields set
            policy_hash='',
            
            created_at=datetime.utcnow()
        )
        
        self.db.add(policy)
        self.db.flush()  # Get policy ID
        
        # 9. Compute policy hash
        policy.policy_hash = self._compute_policy_hash(policy)
        
        # 10. Generate policy document
        document_content, document_hash = self.document_generator.generate(policy)
        
        # Store document as evidence (if evidence service available)
        if self.evidence_service:
            try:
                document_evidence = self.evidence_service.create_evidence(
                    tenant_id=tenant_id,
                    content=document_content,
                    content_type='application/pdf',
                    filename=f"policy_{policy_number}.pdf",
                    evidence_type='POLICY_DOCUMENT',
                    metadata={'policy_id': policy.id}
                )
                policy.policy_document_evidence_id = document_evidence.id
                policy.policy_document_hash = document_hash
            except Exception as e:
                logger.warning(f"Could not store policy document as evidence: {e}")
        else:
            # Store hash even if evidence service not available
            policy.policy_document_hash = document_hash
        
        # 11. Transition submission to BOUND
        submission.status = SubmissionStatus.BOUND
        submission.decision = 'APPROVED'
        submission.decision_by_user_id = bound_by
        submission.decision_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(policy)
        
        # 12. Record policy event
        self._record_event(
            policy_id=policy.id,
            event_type="BOUND",
            actor_type="USER",
            actor_id=bound_by,
            payload={
                "policy_hash": policy.policy_hash,
                "quote_id": quote.id,
                "model_version_id": quote.model_version_id
            }
        )
        
        # 13. Audit
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="POLICY",
            action="BOUND",
            entity_type="policy",
            entity_id=policy.id,
            actor_type="USER",
            actor_id=bound_by,
            payload={
                "policy_number": policy_number,
                "policy_hash": policy.policy_hash,
                "quote_id": quote.id,
                "quote_hash": quote.quote_hash,
                "model_version_id": quote.model_version_id,
                "risk_run_id": quote.risk_run_id,
                "evidence_bundle_id": quote.evidence_bundle_id if quote.evidence_bundle_id else None,
                "premium_cents": premium['total_premium_cents']
            }
        )
        
        # 14. Create loss experience record
        try:
            from app.services.loss_analytics_service import LossAnalyticsService
            loss_service = LossAnalyticsService(self.db)
            loss_service.create_record_from_policy(policy.id)
            logger.info(f"Created loss experience record for policy {policy.id}")
        except Exception as e:
            logger.warning(f"Could not create loss experience record: {e}")
            # Don't fail policy binding if loss tracking fails
        
        logger.info(f"Bound policy: {policy.id} ({policy_number})")
        
        return policy
    
    def record_payment(
        self,
        policy_id: str,
        payment_reference: str,
        paid_at: datetime,
        recorded_by: str
    ) -> Policy:
        """
        Record premium payment for a policy.
        
        Args:
            policy_id: Policy ID (ULID string)
            payment_reference: Payment reference
            paid_at: Payment timestamp
            recorded_by: User ID recording (ULID string)
            
        Returns:
            Updated Policy instance
        """
        policy = self._get_policy(policy_id)
        
        premium = policy.premium_json.copy() if policy.premium_json else {}
        premium['payment_status'] = 'PAID'
        premium['paid_at'] = paid_at.isoformat()
        premium['payment_reference'] = payment_reference
        
        policy.premium_json = premium
        
        self.db.commit()
        self.db.refresh(policy)
        
        # Record event
        self._record_event(
            policy_id=policy.id,
            event_type="PREMIUM_PAID",
            actor_type="USER",
            actor_id=recorded_by,
            payload={
                "payment_reference": payment_reference,
                "amount_cents": premium.get('total_premium_cents', 0)
            }
        )
        
        logger.info(f"Recorded payment for policy: {policy.id}")
        
        return policy
    
    def cancel_policy(
        self,
        policy_id: str,
        reason: str,
        cancelled_by: str,
        refund_amount_cents: Optional[int] = None
    ) -> Policy:
        """
        Cancel an active policy.
        
        Args:
            policy_id: Policy ID (ULID string)
            reason: Cancellation reason
            cancelled_by: User ID cancelling (ULID string)
            refund_amount_cents: Optional refund amount
            
        Returns:
            Updated Policy instance
        """
        policy = self._get_policy(policy_id)
        
        if policy.status != PolicyStatus.ACTIVE:
            raise PolicyNotActiveError(f"Policy is {policy.status.value}, cannot cancel")
        
        policy.status = PolicyStatus.CANCELED
        policy.cancelled_at = datetime.utcnow()
        policy.cancelled_by_user_id = cancelled_by
        policy.cancellation_reason = reason
        policy.refund_amount_cents = refund_amount_cents
        
        self.db.commit()
        self.db.refresh(policy)
        
        # Record event
        self._record_event(
            policy_id=policy.id,
            event_type="CANCELLED",
            actor_type="USER",
            actor_id=cancelled_by,
            payload={
                "reason": reason,
                "refund_amount_cents": refund_amount_cents
            }
        )
        
        # Audit
        self.audit.append_event(
            tenant_id=policy.tenant_id,
            event_type="POLICY",
            action="CANCELLED",
            entity_type="policy",
            entity_id=policy.id,
            actor_type="USER",
            actor_id=cancelled_by,
            payload={
                "reason": reason,
                "refund_amount_cents": refund_amount_cents
            }
        )
        
        logger.info(f"Cancelled policy: {policy.id}")
        
        return policy
    
    def get_policy_decision_pack(self, policy_id: str) -> Dict[str, Any]:
        """
        Get complete decision pack for a policy.
        
        This is for compliance/audit purposes - contains all
        information needed to reconstruct and verify the decision.
        
        Args:
            policy_id: Policy ID (ULID string)
            
        Returns:
            Dictionary with complete decision pack
        """
        policy = self._get_policy(policy_id)
        quote = self.db.query(Quote).filter(Quote.id == policy.quote_id).first()
        submission = self.db.query(UnderwritingSubmission).filter(
            UnderwritingSubmission.id == policy.submission_id
        ).first()
        
        # Get risk run details
        risk_run = self.db.query(RiskRun).filter(
            RiskRun.id == policy.risk_run_id
        ).first()
        
        # Get model version
        model_version = self.db.query(RiskModelVersion).filter(
            RiskModelVersion.id == policy.model_version_id
        ).first()
        
        # Get evidence bundle manifest
        bundle_manifest = None
        if policy.evidence_bundle_id:
            bundle = self.db.query(EvidenceBundle).filter(
                EvidenceBundle.id == policy.evidence_bundle_id
            ).first()
            if bundle:
                bundle_manifest = bundle.manifest_json
        
        # Get audit events (simplified - would need proper audit service method)
        audit_events = []
        
        return {
            "policy": {
                "id": policy.id,
                "policy_number": policy.policy_number,
                "policy_hash": policy.policy_hash,
                "status": policy.status.value,
                "bound_at": policy.bound_at.isoformat() if policy.bound_at else None,
                "terms": policy.terms_json,
                "premium": policy.premium_json
            },
            "quote": {
                "id": quote.id if quote else None,
                "quote_number": quote.quote_number if quote else None,
                "version": quote.version if quote else None,
                "quote_hash": quote.quote_hash if quote else None,
                "issued_at": quote.issued_at.isoformat() if quote and quote.issued_at else None
            },
            "risk_assessment": {
                "risk_run_id": risk_run.id if risk_run else None,
                "result_hash": risk_run.result_hash if risk_run else None,
                "seed": risk_run.seed if risk_run else None,
                "iterations": risk_run.iterations if risk_run else None,
                "risk_score": risk_run.result_json.get('overall_risk_score') if risk_run and risk_run.result_json else None
            },
            "model": {
                "model_version_id": model_version.id if model_version else None,
                "name": model_version.name if model_version else None,
                "version": model_version.version if model_version else None,
                "immutable_hash": model_version.immutable_hash if model_version else None
            },
            "evidence_bundle": {
                "id": policy.evidence_bundle_id,
                "manifest": bundle_manifest
            },
            "audit_trail": audit_events,
            "generated_at": datetime.utcnow().isoformat(),
            "verification": {
                "policy_hash_valid": self._verify_policy_hash(policy),
                "quote_hash_valid": quote.quote_hash == self._compute_quote_hash(quote) if quote else None
            }
        }
    
    def verify_policy_integrity(self, policy_id: str) -> Dict[str, Any]:
        """
        Verify policy hash integrity.
        
        Args:
            policy_id: Policy ID (ULID string)
            
        Returns:
            Dictionary with verification results
        """
        policy = self._get_policy(policy_id)
        computed = self._compute_policy_hash(policy)
        
        return {
            "valid": computed == policy.policy_hash,
            "stored_hash": policy.policy_hash,
            "computed_hash": computed,
            "verified_at": datetime.utcnow().isoformat()
        }
    
    def expire_policies(self) -> int:
        """
        Expire policies past their coverage end date.
        
        Should be run periodically (e.g., daily cron job).
        
        Returns:
            Count of expired policies
        """
        now = datetime.utcnow()
        
        expired = self.db.query(Policy).filter(
            Policy.status == PolicyStatus.ACTIVE,
            Policy.effective_to < now
        ).all()
        
        for policy in expired:
            policy.status = PolicyStatus.EXPIRED
            self._record_event(
                policy_id=policy.id,
                event_type="EXPIRED",
                actor_type="SYSTEM",
                actor_id=None,
                payload={}
            )
        
        self.db.commit()
        
        logger.info(f"Expired {len(expired)} policies")
        
        return len(expired)
    
    def _get_policy(self, policy_id: str) -> Policy:
        """
        Get policy by ID.
        
        Args:
            policy_id: Policy ID (ULID string)
            
        Returns:
            Policy instance
            
        Raises:
            PolicyNotFoundError: If policy not found
        """
        policy = self.db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise PolicyNotFoundError(f"Policy {policy_id} not found")
        return policy
    
    def _generate_policy_number(self, tenant_id: str) -> str:
        """
        Generate unique policy number.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            
        Returns:
            Policy number string
        """
        date_part = datetime.utcnow().strftime("%Y%m%d")
        count = self.db.query(Policy).filter(
            Policy.tenant_id == tenant_id
        ).count()
        return f"POL-{date_part}-{count + 1:06d}"
    
    def _compute_policy_hash(self, policy: Policy) -> str:
        """
        Compute deterministic hash of policy content.
        
        Args:
            policy: Policy instance
            
        Returns:
            SHA256 hash string
        """
        hashable = {
            "policy_number": policy.policy_number,
            "submission_id": policy.submission_id,
            "quote_id": policy.quote_id,
            "model_version_id": policy.model_version_id,
            "risk_run_id": policy.risk_run_id,
            "evidence_bundle_id": policy.evidence_bundle_id if policy.evidence_bundle_id else None,
            "terms": policy.terms_json,
            "premium": {k: v for k, v in (policy.premium_json or {}).items() if k != 'paid_at'},
            "effective_from": policy.effective_from.isoformat() if policy.effective_from else None,
            "effective_to": policy.effective_to.isoformat() if policy.effective_to else None
        }
        
        canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def _verify_policy_hash(self, policy: Policy) -> bool:
        """
        Verify policy hash.
        
        Args:
            policy: Policy instance
            
        Returns:
            True if hash is valid
        """
        return self._compute_policy_hash(policy) == policy.policy_hash
    
    def _compute_quote_hash(self, quote: Quote) -> str:
        """
        Compute quote hash (same logic as in quote service).
        
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
    
    def _record_event(
        self,
        policy_id: str,
        event_type: str,
        actor_type: str,
        actor_id: Optional[str],
        payload: Dict[str, Any]
    ):
        """
        Record a policy event.
        
        Args:
            policy_id: Policy ID (ULID string)
            event_type: Event type
            actor_type: Actor type (USER, SYSTEM)
            actor_id: Actor ID (ULID string)
            payload: Event payload
        """
        from app.shared.utils import generate_ulid
        
        event = PolicyEvent(
            id=generate_ulid(),
            policy_id=policy_id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            payload_json=payload,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        self.db.commit()


# Exception classes
class PolicyNotFoundError(Exception):
    """Policy not found"""
    pass


class QuoteNotFoundError(Exception):
    """Quote not found"""
    pass


class QuoteNotAcceptedError(Exception):
    """Quote not accepted"""
    pass


class SubmissionNotFoundError(Exception):
    """Submission not found"""
    pass


class KYCNotCompletedError(Exception):
    """KYC not completed"""
    pass


class EvidenceBundleNotSealedError(Exception):
    """Evidence bundle not sealed"""
    pass


class PolicyNotActiveError(Exception):
    """Policy not active"""
    pass
