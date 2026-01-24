"""
Decision pack generation for regulatory compliance.

A decision pack contains all information needed to reconstruct
and verify an underwriting or claims decision.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import json
import hashlib
import zipfile
import io
import logging

from sqlalchemy.orm import Session

from app.core.audit_ledger.ledger import AuditLedger

logger = logging.getLogger(__name__)


class DecisionPackService:
    """Service for generating decision packs."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize decision pack service.
        
        Args:
            db: Database session
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def generate_policy_decision_pack(
        self,
        policy_id: str,
        generated_by: str,
        purpose: str = "AUDIT"
    ) -> bytes:
        """
        Generate a complete decision pack for a policy.
        
        Contains:
        - Policy details and hash
        - Quote details and hash
        - Risk assessment and model version
        - Evidence bundle manifest
        - Audit trail
        - Verification instructions
        
        Args:
            policy_id: Policy ID (ULID string)
            generated_by: User ID generating pack (ULID string)
            purpose: Purpose of pack (AUDIT, REGULATORY, etc.)
            
        Returns:
            ZIP file bytes
        """
        # Get policy
        try:
            from app.modules.underwriting.models import Policy
            policy = self.db.query(Policy).filter(Policy.id == policy_id).first()
            if not policy:
                raise PolicyNotFoundError(f"Policy {policy_id} not found")
        except ImportError:
            raise PolicyNotFoundError("Policy model not available")
        
        # Gather all related data
        quote = None
        if hasattr(policy, 'quote_id') and policy.quote_id:
            try:
                from app.models.quote import Quote
                quote = self.db.query(Quote).filter(Quote.id == policy.quote_id).first()
            except ImportError:
                logger.warning("Quote model not available")
        
        submission = None
        if hasattr(policy, 'submission_id') and policy.submission_id:
            try:
                from app.modules.underwriting.models import UnderwritingSubmission
                submission = self.db.query(UnderwritingSubmission).filter(
                    UnderwritingSubmission.id == policy.submission_id
                ).first()
            except ImportError:
                logger.warning("UnderwritingSubmission model not available")
        
        risk_run = None
        if hasattr(policy, 'risk_run_id') and policy.risk_run_id:
            try:
                from app.models.risk_run import RiskRun
                risk_run = self.db.query(RiskRun).filter(
                    RiskRun.id == policy.risk_run_id
                ).first()
            except ImportError:
                logger.warning("RiskRun model not available")
        
        model_version = None
        if hasattr(policy, 'model_version_id') and policy.model_version_id:
            try:
                from app.models.risk_model_version import RiskModelVersion
                model_version = self.db.query(RiskModelVersion).filter(
                    RiskModelVersion.id == policy.model_version_id
                ).first()
            except ImportError:
                logger.warning("RiskModelVersion model not available")
        
        # Build decision pack
        decision_pack = {
            "pack_metadata": {
                "pack_type": "POLICY_DECISION",
                "policy_id": policy_id,
                "generated_at": datetime.utcnow().isoformat(),
                "generated_by": generated_by,
                "purpose": purpose,
                "pack_version": "1.0"
            },
            
            "policy": {
                "id": str(policy.id),
                "policy_number": getattr(policy, 'policy_number', None),
                "status": policy.status.value if hasattr(policy.status, 'value') else str(policy.status),
                "policy_hash": getattr(policy, 'policy_hash', None),
                "terms": getattr(policy, 'terms_json', None),
                "premium": getattr(policy, 'premium_json', None),
                "effective_from": policy.effective_from.isoformat() if hasattr(policy, 'effective_from') and policy.effective_from else None,
                "effective_to": policy.effective_to.isoformat() if hasattr(policy, 'effective_to') and policy.effective_to else None,
                "bound_at": policy.bound_at.isoformat() if hasattr(policy, 'bound_at') and policy.bound_at else None,
                "bound_by": str(policy.bound_by_user_id) if hasattr(policy, 'bound_by_user_id') and policy.bound_by_user_id else None
            },
            
            "quote": None,
            "submission": None,
            "risk_assessment": None,
            "model_version": None,
            "evidence_bundle": None,
            "audit_trail": [],
            "verification": {
                "policy_hash_valid": None,
                "quote_hash_valid": None,
                "model_hash_valid": None,
                "verification_instructions": ""
            }
        }
        
        # Quote details
        if quote:
            decision_pack["quote"] = {
                "id": str(quote.id),
                "quote_number": getattr(quote, 'quote_number', None),
                "version": getattr(quote, 'version', None),
                "quote_hash": getattr(quote, 'quote_hash', None),
                "pricing_snapshot": getattr(quote, 'pricing_snapshot_json', None),
                "coverage_terms": getattr(quote, 'coverage_terms_json', None),
                "issued_at": quote.issued_at.isoformat() if hasattr(quote, 'issued_at') and quote.issued_at else None
            }
        
        # Submission details
        if submission:
            decision_pack["submission"] = {
                "id": str(submission.id),
                "submission_number": getattr(submission, 'submission_number', None),
                "status": submission.status.value if hasattr(submission.status, 'value') else str(submission.status),
                "requested_coverage": getattr(submission, 'requested_coverage_json', None),
                "submitted_at": submission.submitted_at.isoformat() if hasattr(submission, 'submitted_at') and submission.submitted_at else None
            }
        
        # Risk assessment
        if risk_run:
            risk_assessment = None
            if hasattr(risk_run, 'assessment_id') and risk_run.assessment_id:
                try:
                    from app.models.risk_assessment import RiskAssessment
                    risk_assessment = self.db.query(RiskAssessment).filter(
                        RiskAssessment.id == risk_run.assessment_id
                    ).first()
                except ImportError:
                    pass
            
            result_json = getattr(risk_run, 'result_json', {}) or {}
            decision_pack["risk_assessment"] = {
                "risk_run_id": str(risk_run.id),
                "input_hash": getattr(risk_assessment, 'input_hash', None) if risk_assessment else None,
                "result_hash": getattr(risk_run, 'result_hash', None),
                "seed": getattr(risk_run, 'seed', None),
                "iterations": getattr(risk_run, 'iterations', None),
                "engine_version": getattr(risk_run, 'engine_version', None),
                "risk_score": result_json.get('overall_risk_score'),
                "risk_factors": result_json.get('risk_factors'),
                "var_95": result_json.get('var_95'),
                "var_99": result_json.get('var_99')
            }
        
        # Model version
        if model_version:
            decision_pack["model_version"] = {
                "id": str(model_version.id),
                "name": getattr(model_version, 'name', None),
                "version": getattr(model_version, 'version', None),
                "immutable_hash": getattr(model_version, 'immutable_hash', None),
                "published_at": model_version.published_at.isoformat() if hasattr(model_version, 'published_at') and model_version.published_at else None
            }
        
        # Evidence bundle
        if hasattr(policy, 'evidence_bundle_id') and policy.evidence_bundle_id:
            try:
                from app.models.evidence_bundle import EvidenceBundle
                bundle = self.db.query(EvidenceBundle).filter(
                    EvidenceBundle.id == policy.evidence_bundle_id
                ).first()
                if bundle:
                    decision_pack["evidence_bundle"] = {
                        "id": str(bundle.id),
                        "status": getattr(bundle, 'status', None),
                        "manifest_hash": getattr(bundle, 'manifest_hash', None),
                        "item_count": len(bundle.items) if hasattr(bundle, 'items') and bundle.items else 0,
                        "sealed_at": bundle.sealed_at.isoformat() if hasattr(bundle, 'sealed_at') and bundle.sealed_at else None
                    }
            except ImportError:
                logger.warning("EvidenceBundle model not available")
        
        # Audit trail
        try:
            audit_events = self.audit.get_events(
                tenant_id=policy.tenant_id,
                entity_type="policy",
                entity_id=policy_id
            )
            decision_pack["audit_trail"] = [
                {
                    "event_type": e.event_type,
                    "action": e.action,
                    "actor_type": e.actor_type,
                    "actor_id": e.actor_id,
                    "created_at": e.created_at.isoformat() if hasattr(e, 'created_at') and e.created_at else None,
                    "event_hash": getattr(e, 'event_hash', None),
                    "prev_hash": getattr(e, 'prev_hash', None),
                    "sequence_num": getattr(e, 'sequence_num', None)
                }
                for e in audit_events
            ]
        except Exception as e:
            logger.warning(f"Could not fetch audit events: {e}")
            decision_pack["audit_trail"] = []
        
        # Verification
        decision_pack["verification"] = {
            "policy_hash_valid": self._verify_policy_hash(policy),
            "quote_hash_valid": self._verify_quote_hash(quote) if quote else None,
            "model_hash_valid": model_version.immutable_hash is not None if model_version else None,
            "verification_instructions": self._generate_verification_instructions()
        }
        
        # Compute pack hash
        pack_hash = self._compute_pack_hash(decision_pack)
        decision_pack["pack_metadata"]["pack_hash"] = pack_hash
        
        # Create ZIP
        zip_bytes = self._create_decision_pack_zip(decision_pack, policy)
        
        # Audit the export
        self.audit.append_event(
            tenant_id=policy.tenant_id,
            event_type="COMPLIANCE",
            action="DECISION_PACK_GENERATED",
            entity_type="policy",
            entity_id=policy_id,
            actor_type="USER",
            actor_id=generated_by,
            payload={
                "pack_hash": pack_hash,
                "purpose": purpose,
                "pack_type": "POLICY_DECISION"
            }
        )
        
        logger.info(
            f"Generated decision pack for policy {policy_id} "
            f"(hash: {pack_hash}, purpose: {purpose})"
        )
        
        return zip_bytes
    
    def generate_claim_decision_pack(
        self,
        claim_id: str,
        generated_by: str,
        purpose: str = "AUDIT"
    ) -> bytes:
        """
        Generate decision pack for a claim.
        
        Args:
            claim_id: Claim ID (ULID string)
            generated_by: User ID generating pack (ULID string)
            purpose: Purpose of pack (AUDIT, REGULATORY, etc.)
            
        Returns:
            ZIP file bytes
        """
        try:
            from app.modules.claims.models import Claim
            claim = self.db.query(Claim).filter(Claim.id == claim_id).first()
            if not claim:
                raise ClaimNotFoundError(f"Claim {claim_id} not found")
        except ImportError:
            raise ClaimNotFoundError("Claim model not available")
        
        # Get related data
        policy = None
        if claim.policy_id:
            try:
                from app.modules.underwriting.models import Policy
                policy = self.db.query(Policy).filter(Policy.id == claim.policy_id).first()
            except ImportError:
                pass
        
        # Build decision pack
        decision_pack = {
            "pack_metadata": {
                "pack_type": "CLAIM_DECISION",
                "claim_id": claim_id,
                "generated_at": datetime.utcnow().isoformat(),
                "generated_by": generated_by,
                "purpose": purpose,
                "pack_version": "1.0"
            },
            
            "claim": {
                "id": str(claim.id),
                "claim_number": getattr(claim, 'claim_number', None),
                "status": claim.status.value if hasattr(claim.status, 'value') else str(claim.status),
                "fnol": getattr(claim, 'fnol_json', None),
                "decision": getattr(claim, 'decision', None),
                "decision_reason": getattr(claim, 'decision_reason', None),
                "approved_amount_cents": getattr(claim, 'approved_amount_cents', None),
                "adjudication": getattr(claim, 'adjudication_json', None)
            },
            
            "policy": None,
            "evidence_bundle": None,
            "audit_trail": [],
            "verification": {
                "verification_instructions": self._generate_verification_instructions()
            }
        }
        
        # Policy details
        if policy:
            decision_pack["policy"] = {
                "id": str(policy.id),
                "policy_number": getattr(policy, 'policy_number', None),
                "status": policy.status.value if hasattr(policy.status, 'value') else str(policy.status)
            }
        
        # Evidence bundle
        if hasattr(claim, 'evidence_bundle_id') and claim.evidence_bundle_id:
            try:
                from app.models.evidence_bundle import EvidenceBundle
                bundle = self.db.query(EvidenceBundle).filter(
                    EvidenceBundle.id == claim.evidence_bundle_id
                ).first()
                if bundle:
                    decision_pack["evidence_bundle"] = {
                        "id": str(bundle.id),
                        "status": getattr(bundle, 'status', None),
                        "manifest_hash": getattr(bundle, 'manifest_hash', None)
                    }
            except ImportError:
                pass
        
        # Audit trail
        try:
            audit_events = self.audit.get_events(
                tenant_id=claim.tenant_id,
                entity_type="claim",
                entity_id=claim_id
            )
            decision_pack["audit_trail"] = [
                {
                    "event_type": e.event_type,
                    "action": e.action,
                    "actor_type": e.actor_type,
                    "actor_id": e.actor_id,
                    "created_at": e.created_at.isoformat() if hasattr(e, 'created_at') and e.created_at else None,
                    "event_hash": getattr(e, 'event_hash', None),
                    "prev_hash": getattr(e, 'prev_hash', None)
                }
                for e in audit_events
            ]
        except Exception as e:
            logger.warning(f"Could not fetch audit events: {e}")
        
        # Compute pack hash
        pack_hash = self._compute_pack_hash(decision_pack)
        decision_pack["pack_metadata"]["pack_hash"] = pack_hash
        
        # Create ZIP
        zip_bytes = self._create_claim_decision_pack_zip(decision_pack, claim)
        
        # Audit
        self.audit.append_event(
            tenant_id=claim.tenant_id,
            event_type="COMPLIANCE",
            action="DECISION_PACK_GENERATED",
            entity_type="claim",
            entity_id=claim_id,
            actor_type="USER",
            actor_id=generated_by,
            payload={
                "pack_hash": pack_hash,
                "purpose": purpose,
                "pack_type": "CLAIM_DECISION"
            }
        )
        
        return zip_bytes
    
    def _verify_policy_hash(self, policy) -> Optional[bool]:
        """
        Verify policy hash.
        
        Args:
            policy: Policy instance
            
        Returns:
            True if valid, False if invalid, None if cannot verify
        """
        if not hasattr(policy, 'policy_hash') or not policy.policy_hash:
            return None
        
        try:
            # Recompute hash using same method as PolicyService
            hashable = {
                "policy_number": getattr(policy, 'policy_number', ''),
                "quote_id": str(policy.quote_id) if hasattr(policy, 'quote_id') and policy.quote_id else None,
                "model_version_id": str(policy.model_version_id) if hasattr(policy, 'model_version_id') and policy.model_version_id else None,
                "risk_run_id": str(policy.risk_run_id) if hasattr(policy, 'risk_run_id') and policy.risk_run_id else None,
                "evidence_bundle_id": str(policy.evidence_bundle_id) if hasattr(policy, 'evidence_bundle_id') and policy.evidence_bundle_id else None,
                "terms_json": getattr(policy, 'terms_json', {}),
                "premium_json": getattr(policy, 'premium_json', {}),
                "risk_snapshot_json": getattr(policy, 'risk_snapshot_json', {}),
                "effective_from": policy.effective_from.isoformat() if hasattr(policy, 'effective_from') and policy.effective_from else None,
                "effective_to": policy.effective_to.isoformat() if hasattr(policy, 'effective_to') and policy.effective_to else None
            }
            canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'), default=str)
            computed = hashlib.sha256(canonical.encode()).hexdigest()
            return computed == policy.policy_hash
        except Exception as e:
            logger.warning(f"Could not verify policy hash: {e}")
            return None
    
    def _verify_quote_hash(self, quote) -> Optional[bool]:
        """
        Verify quote hash.
        
        Args:
            quote: Quote instance
            
        Returns:
            True if valid, False if invalid, None if cannot verify
        """
        if not quote or not hasattr(quote, 'quote_hash') or not quote.quote_hash:
            return None
        
        try:
            # Recompute hash using same method as QuoteService
            hashable = {
                "quote_number": getattr(quote, 'quote_number', ''),
                "version": getattr(quote, 'version', 1),
                "submission_id": str(quote.submission_id) if hasattr(quote, 'submission_id') and quote.submission_id else None,
                "pricing_snapshot_json": getattr(quote, 'pricing_snapshot_json', {}),
                "coverage_terms_json": getattr(quote, 'coverage_terms_json', {}),
                "risk_summary_json": getattr(quote, 'risk_summary_json', {}),
                "valid_from": quote.valid_from.isoformat() if hasattr(quote, 'valid_from') and quote.valid_from else None,
                "valid_until": quote.valid_until.isoformat() if hasattr(quote, 'valid_until') and quote.valid_until else None
            }
            canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'), default=str)
            computed = hashlib.sha256(canonical.encode()).hexdigest()
            return computed == quote.quote_hash
        except Exception as e:
            logger.warning(f"Could not verify quote hash: {e}")
            return None
    
    def _generate_verification_instructions(self) -> str:
        """
        Generate verification instructions.
        
        Returns:
            Verification instructions text
        """
        return """
VERIFICATION INSTRUCTIONS
=========================

To verify this decision pack:

1. POLICY HASH VERIFICATION
   - Extract policy data from decision_pack.json
   - Compute SHA256 of canonical policy JSON
   - Compare with stored policy_hash

2. QUOTE HASH VERIFICATION
   - Extract quote data
   - Compute SHA256 of canonical quote JSON
   - Compare with stored quote_hash

3. MODEL HASH VERIFICATION
   - Model parameters are immutable after publishing
   - Hash stored at publish time

4. AUDIT CHAIN VERIFICATION
   - Each audit event includes prev_hash
   - Verify chain integrity by recomputing hashes
   - Check sequence_num is sequential

5. EVIDENCE BUNDLE VERIFICATION
   - Download evidence files using manifest
   - Verify each file's content_hash
   - Verify manifest_hash

6. PACK HASH VERIFICATION
   - Recompute pack_hash from decision_pack.json
   - Compare with pack_metadata.pack_hash

For questions: compliance@example.com
        """.strip()
    
    def _compute_pack_hash(self, pack: Dict[str, Any]) -> str:
        """
        Compute hash of decision pack.
        
        Args:
            pack: Decision pack dictionary
            
        Returns:
            SHA256 hash string
        """
        # Exclude pack_hash from computation
        hashable = {k: v for k, v in pack.items() if k != 'pack_metadata'}
        # Also exclude pack_hash from metadata
        metadata = pack.get('pack_metadata', {}).copy()
        metadata.pop('pack_hash', None)
        hashable['pack_metadata'] = metadata
        
        canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'), default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def _create_decision_pack_zip(self, pack: Dict[str, Any], policy) -> io.BytesIO:
        """
        Create ZIP file for decision pack.
        
        Args:
            pack: Decision pack dictionary
            policy: Policy instance
            
        Returns:
            BytesIO buffer with ZIP content
        """
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Main decision pack JSON
            zf.writestr(
                'decision_pack.json',
                json.dumps(pack, indent=2, default=str, ensure_ascii=False)
            )
            
            # Verification instructions
            zf.writestr(
                'VERIFICATION.txt',
                pack["verification"]["verification_instructions"]
            )
            
            # Policy document if available (would need to fetch from evidence service)
            if hasattr(policy, 'policy_document_evidence_id') and policy.policy_document_evidence_id:
                # In production, would fetch actual PDF here
                zf.writestr(
                    'policy_document_info.txt',
                    f"Policy document evidence ID: {policy.policy_document_evidence_id}\n"
                    f"Document hash: {getattr(policy, 'policy_document_hash', 'N/A')}\n"
                    f"Note: Actual document stored in evidence system"
                )
            
            # README
            policy_number = getattr(policy, 'policy_number', 'N/A')
            readme = f"""
POLICY DECISION PACK
====================

Policy Number: {policy_number}
Generated: {pack['pack_metadata']['generated_at']}
Pack Hash: {pack['pack_metadata'].get('pack_hash', 'N/A')}
Purpose: {pack['pack_metadata'].get('purpose', 'AUDIT')}

This archive contains the complete audit trail for this policy decision.

Files:
- decision_pack.json: Complete decision data
- VERIFICATION.txt: Instructions for verifying integrity

Contents:
- Policy details and hash
- Quote details and hash
- Risk assessment results
- Model version information
- Evidence bundle manifest
- Complete audit trail

For compliance inquiries: compliance@example.com
            """
            zf.writestr('README.txt', readme)
        
        buffer.seek(0)
        return buffer
    
    def _create_claim_decision_pack_zip(self, pack: Dict[str, Any], claim) -> bytes:
        """
        Create ZIP file for claim decision pack.
        
        Args:
            pack: Decision pack dictionary
            claim: Claim instance
            
        Returns:
            ZIP file bytes
        """
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Main decision pack JSON
            zf.writestr(
                'decision_pack.json',
                json.dumps(pack, indent=2, default=str, ensure_ascii=False)
            )
            
            # Verification instructions
            zf.writestr(
                'VERIFICATION.txt',
                pack["verification"]["verification_instructions"]
            )
            
            # README
            claim_number = getattr(claim, 'claim_number', 'N/A')
            readme = f"""
CLAIM DECISION PACK
===================

Claim Number: {claim_number}
Generated: {pack['pack_metadata']['generated_at']}
Pack Hash: {pack['pack_metadata'].get('pack_hash', 'N/A')}
Purpose: {pack['pack_metadata'].get('purpose', 'AUDIT')}

This archive contains the complete audit trail for this claim decision.

Files:
- decision_pack.json: Complete decision data
- VERIFICATION.txt: Instructions for verifying integrity

For compliance inquiries: compliance@example.com
            """
            zf.writestr('README.txt', readme)
        
        buffer.seek(0)
        return buffer.getvalue()


# Exception classes
class PolicyNotFoundError(Exception):
    """Policy not found"""
    pass


class ClaimNotFoundError(Exception):
    """Claim not found"""
    pass
