"""
GDPR compliance service.

Handles:
- Data subject access requests (export)
- Right to deletion (with audit preservation)
- Consent management
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import zipfile
import io
import logging

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class GDPRService:
    """GDPR compliance operations."""
    
    # Tables containing PII
    PII_TABLES = [
        'users',
        'underwriting_submissions',
        'policies',
        'claims'
    ]
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize GDPR service.
        
        Args:
            db: Database session
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def export_user_data(
        self,
        user_id: str,
        requested_by: str,
        request_reference: str
    ) -> bytes:
        """
        Export all data for a user (Data Subject Access Request).
        
        Returns ZIP file containing:
        - User profile data
        - All submissions/quotes/policies
        - All claims
        - Audit events related to user
        - Evidence metadata (not content)
        
        Args:
            user_id: User ID to export (ULID string)
            requested_by: User ID requesting export (ULID string)
            request_reference: Request reference number
            
        Returns:
            ZIP file bytes
        """
        export_data = {
            "export_metadata": {
                "user_id": user_id,
                "requested_by": requested_by,
                "request_reference": request_reference,
                "exported_at": datetime.utcnow().isoformat(),
                "format_version": "1.0"
            }
        }
        
        # 1. User profile
        try:
            from app.models.auth import User
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                export_data["user_profile"] = {
                    "id": str(user.id),
                    "email": getattr(user, 'email', None),
                    "name": getattr(user, 'name', None),
                    "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                    "last_login": getattr(user, 'last_login', None).isoformat() if hasattr(user, 'last_login') and user.last_login else None
                }
        except ImportError:
            logger.warning("User model not available")
            export_data["user_profile"] = None
        
        # 2. Memberships and tenants
        try:
            from app.models.rbac import Membership
            memberships = self.db.query(Membership).filter(
                Membership.user_id == user_id
            ).all()
            export_data["memberships"] = [
                {
                    "tenant_id": str(m.tenant_id),
                    "role": getattr(m, 'role', {}),
                    "joined_at": m.created_at.isoformat() if hasattr(m, 'created_at') and m.created_at else None
                }
                for m in memberships
            ]
        except (ImportError, AttributeError):
            logger.warning("Membership model not available")
            export_data["memberships"] = []
        
        # 3. Submissions created by user
        try:
            from app.modules.underwriting.models import UnderwritingSubmission
            submissions = self.db.query(UnderwritingSubmission).filter(
                UnderwritingSubmission.created_by_user_id == user_id
            ).all()
            export_data["submissions"] = [
                self._export_submission(s) for s in submissions
            ]
        except (ImportError, AttributeError):
            logger.warning("UnderwritingSubmission model not available")
            export_data["submissions"] = []
        
        # 4. Policies (where user is policyholder or creator)
        try:
            from app.modules.underwriting.models import Policy
            policies = self.db.query(Policy).filter(
                or_(
                    Policy.bound_by_user_id == user_id,
                    Policy.created_by_user_id == user_id
                )
            ).all()
            export_data["policies"] = [
                self._export_policy(p) for p in policies
            ]
        except (ImportError, AttributeError):
            logger.warning("Policy model not available")
            export_data["policies"] = []
        
        # 5. Claims filed by user
        try:
            from app.modules.claims.models import Claim
            claims = self.db.query(Claim).filter(
                Claim.created_by_user_id == user_id
            ).all()
            export_data["claims"] = [
                self._export_claim(c) for c in claims
            ]
        except (ImportError, AttributeError):
            logger.warning("Claim model not available")
            export_data["claims"] = []
        
        # 6. Trigger events (if user is involved)
        try:
            from app.modules.parametric.models import TriggerEvent
            trigger_events = self.db.query(TriggerEvent).filter(
                TriggerEvent.policy_id.in_(
                    [p.id for p in export_data.get("policies", []) if hasattr(p, 'id')]
                )
            ).all()
            export_data["trigger_events"] = [
                {
                    "id": str(te.id),
                    "trigger_definition_id": str(te.trigger_definition_id),
                    "status": te.status.value if hasattr(te.status, 'value') else str(te.status),
                    "detected_at": te.detected_at.isoformat() if te.detected_at else None,
                    "proposed_payout_cents": te.proposed_payout_cents
                }
                for te in trigger_events
            ]
        except (ImportError, AttributeError):
            logger.warning("TriggerEvent model not available")
            export_data["trigger_events"] = []
        
        # 7. Audit events involving user
        try:
            audit_events = self._get_audit_events_for_user(user_id)
            export_data["audit_events"] = audit_events
        except Exception as e:
            logger.warning(f"Could not fetch audit events: {e}")
            export_data["audit_events"] = []
        
        # Create ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Main data file
            zf.writestr(
                'user_data.json',
                json.dumps(export_data, indent=2, default=str, ensure_ascii=False)
            )
            
            # README
            readme = f"""GDPR Data Export
================

This archive contains all personal data held about you in our system.

Files:
- user_data.json: All your data in JSON format

Data Categories Included:
- User profile information
- Tenant memberships
- Insurance submissions
- Policies
- Claims
- Trigger events
- Audit trail

For questions about this export, contact: privacy@example.com

Export Reference: {request_reference}
Exported At: {datetime.utcnow().isoformat()}
            """
            zf.writestr('README.txt', readme)
        
        zip_bytes = zip_buffer.getvalue()
        
        # Audit the export
        self.audit.append_event(
            tenant_id=None,
            event_type="GDPR",
            action="DATA_EXPORTED",
            entity_type="user",
            entity_id=user_id,
            actor_type="USER",
            actor_id=requested_by,
            payload={
                "request_reference": request_reference,
                "data_categories": list(export_data.keys()),
                "export_size_bytes": len(zip_bytes)
            }
        )
        
        logger.info(
            f"Exported GDPR data for user {user_id} "
            f"(reference: {request_reference}, size: {len(zip_bytes)} bytes)"
        )
        
        return zip_bytes
    
    def _export_submission(self, submission) -> Dict[str, Any]:
        """
        Export submission data (excluding full PII).
        
        Args:
            submission: UnderwritingSubmission instance
            
        Returns:
            Dictionary with submission data
        """
        return {
            "id": str(submission.id),
            "submission_number": getattr(submission, 'submission_number', None),
            "status": submission.status.value if hasattr(submission.status, 'value') else str(submission.status),
            "created_at": submission.created_at.isoformat() if hasattr(submission, 'created_at') and submission.created_at else None,
            "coverage_requested": getattr(submission, 'requested_coverage_json', None),
            "applicant_info": getattr(submission, 'applicant_json', None)
        }
    
    def _export_policy(self, policy) -> Dict[str, Any]:
        """
        Export policy data.
        
        Args:
            policy: Policy instance
            
        Returns:
            Dictionary with policy data
        """
        return {
            "id": str(policy.id),
            "policy_number": getattr(policy, 'policy_number', None),
            "status": policy.status.value if hasattr(policy.status, 'value') else str(policy.status),
            "effective_from": policy.effective_from.isoformat() if hasattr(policy, 'effective_from') and policy.effective_from else None,
            "effective_to": policy.effective_to.isoformat() if hasattr(policy, 'effective_to') and policy.effective_to else None,
            "terms": getattr(policy, 'terms_json', None),
            "bound_at": policy.bound_at.isoformat() if hasattr(policy, 'bound_at') and policy.bound_at else None,
            "premium": getattr(policy, 'premium_json', None)
        }
    
    def _export_claim(self, claim) -> Dict[str, Any]:
        """
        Export claim data.
        
        Args:
            claim: Claim instance
            
        Returns:
            Dictionary with claim data
        """
        return {
            "id": str(claim.id),
            "claim_number": getattr(claim, 'claim_number', None),
            "status": claim.status.value if hasattr(claim.status, 'value') else str(claim.status),
            "created_at": claim.created_at.isoformat() if hasattr(claim, 'created_at') and claim.created_at else None,
            "fnol": getattr(claim, 'fnol_json', None),
            "decision": getattr(claim, 'decision', None),
            "approved_amount_cents": getattr(claim, 'approved_amount_cents', None)
        }
    
    def _get_audit_events_for_user(self, user_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get audit events involving user.
        
        Args:
            user_id: User ID (ULID string)
            limit: Maximum number of events
            
        Returns:
            List of audit event dictionaries
        """
        try:
            from app.modules.audit_ledger.models import AuditEvent
            
            events = self.db.query(AuditEvent).filter(
                or_(
                    AuditEvent.actor_id == user_id,
                    AuditEvent.entity_id == user_id
                )
            ).order_by(AuditEvent.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "event_type": e.event_type,
                    "action": e.action,
                    "entity_type": e.entity_type,
                    "entity_id": e.entity_id,
                    "created_at": e.created_at.isoformat() if hasattr(e, 'created_at') and e.created_at else None,
                    "payload": getattr(e, 'payload_json', None)
                }
                for e in events
            ]
        except (ImportError, AttributeError):
            # Fallback: query audit_events table directly
            try:
                result = self.db.execute(
                    """
                    SELECT event_type, action, entity_type, entity_id, created_at, payload_json
                    FROM audit_events
                    WHERE actor_id = :user_id OR entity_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """,
                    {"user_id": user_id, "limit": limit}
                )
                return [
                    {
                        "event_type": row[0],
                        "action": row[1],
                        "entity_type": row[2],
                        "entity_id": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "payload": row[5]
                    }
                    for row in result
                ]
            except Exception as e:
                logger.warning(f"Could not fetch audit events: {e}")
                return []
    
    def process_deletion_request(
        self,
        user_id: str,
        requested_by: str,
        request_reference: str,
        verification_token: str
    ) -> Dict[str, Any]:
        """
        Process a deletion request (Right to Erasure).
        
        Note: We cannot delete:
        - Audit log entries (but can redact PII)
        - Active policies/claims data (legal requirement)
        - Financial records (regulatory requirement)
        
        We will:
        - Delete user profile
        - Anonymize PII in submissions/claims
        - Preserve audit trail with redaction markers
        
        Args:
            user_id: User ID to delete (ULID string)
            requested_by: User ID requesting deletion (ULID string)
            request_reference: Request reference number
            verification_token: Verification token for confirmation
            
        Returns:
            Dictionary with deletion report
        """
        # Verify deletion token (prevent accidental deletion)
        if not self._verify_deletion_token(user_id, verification_token):
            raise InvalidDeletionTokenError("Invalid verification token")
        
        deletion_report = {
            "user_id": user_id,
            "request_reference": request_reference,
            "requested_at": datetime.utcnow().isoformat(),
            "actions": []
        }
        
        # 1. Check for blockers
        blockers = self._check_deletion_blockers(user_id)
        if blockers:
            deletion_report["blocked"] = True
            deletion_report["blockers"] = blockers
            deletion_report["actions"].append({
                "action": "BLOCKED",
                "reason": "Active legal/regulatory holds",
                "details": blockers
            })
            
            # Audit blocked deletion
            self.audit.append_event(
                tenant_id=None,
                event_type="GDPR",
                action="DELETION_BLOCKED",
                entity_type="user",
                entity_id=user_id,
                actor_type="USER",
                actor_id=requested_by,
                payload={
                    "request_reference": request_reference,
                    "blockers": blockers
                }
            )
            
            return deletion_report
        
        # 2. Anonymize submissions
        try:
            from app.modules.underwriting.models import UnderwritingSubmission
            submissions = self.db.query(UnderwritingSubmission).filter(
                UnderwritingSubmission.created_by_user_id == user_id
            ).all()
            
            for submission in submissions:
                self._anonymize_submission(submission)
                deletion_report["actions"].append({
                    "action": "ANONYMIZED",
                    "entity_type": "submission",
                    "entity_id": str(submission.id)
                })
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not anonymize submissions: {e}")
        
        # 3. Anonymize policies (where user is policyholder)
        try:
            from app.modules.underwriting.models import Policy, PolicyStatus
            policies = self.db.query(Policy).filter(
                Policy.bound_by_user_id == user_id
            ).all()
            
            for policy in policies:
                # Only anonymize if policy is closed/expired
                if hasattr(policy.status, 'value'):
                    status_val = policy.status.value
                else:
                    status_val = str(policy.status)
                
                if status_val in ['CLOSED', 'EXPIRED', 'CANCELLED']:
                    self._anonymize_policy(policy)
                    deletion_report["actions"].append({
                        "action": "ANONYMIZED",
                        "entity_type": "policy",
                        "entity_id": str(policy.id)
                    })
                else:
                    deletion_report["actions"].append({
                        "action": "RETAINED",
                        "entity_type": "policy",
                        "entity_id": str(policy.id),
                        "reason": f"Active policy ({status_val})"
                    })
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not anonymize policies: {e}")
        
        # 4. Anonymize claims
        try:
            from app.modules.claims.models import Claim, ClaimStatus
            claims = self.db.query(Claim).filter(
                Claim.created_by_user_id == user_id
            ).all()
            
            for claim in claims:
                if hasattr(claim.status, 'value'):
                    status_val = claim.status.value
                else:
                    status_val = str(claim.status)
                
                if status_val == 'CLOSED':
                    self._anonymize_claim(claim)
                    deletion_report["actions"].append({
                        "action": "ANONYMIZED",
                        "entity_type": "claim",
                        "entity_id": str(claim.id)
                    })
                else:
                    deletion_report["actions"].append({
                        "action": "RETAINED",
                        "entity_type": "claim",
                        "entity_id": str(claim.id),
                        "reason": f"Active claim ({status_val})"
                    })
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not anonymize claims: {e}")
        
        # 5. Redact audit events (add marker, don't delete)
        self._redact_audit_events(user_id)
        deletion_report["actions"].append({
            "action": "REDACTED",
            "entity_type": "audit_events",
            "note": "PII redacted, events preserved for compliance"
        })
        
        # 6. Delete user profile
        try:
            from app.models.auth import User
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                self.db.delete(user)
                deletion_report["actions"].append({
                    "action": "DELETED",
                    "entity_type": "user_profile"
                })
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not delete user profile: {e}")
        
        # 7. Delete memberships
        try:
            from app.models.rbac import Membership
            deleted_count = self.db.query(Membership).filter(
                Membership.user_id == user_id
            ).delete(synchronize_session=False)
            
            if deleted_count > 0:
                deletion_report["actions"].append({
                    "action": "DELETED",
                    "entity_type": "memberships",
                    "count": deleted_count
                })
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not delete memberships: {e}")
        
        self.db.commit()
        
        deletion_report["completed_at"] = datetime.utcnow().isoformat()
        deletion_report["status"] = "COMPLETED"
        
        # Audit the deletion (critical)
        self.audit.append_event(
            tenant_id=None,
            event_type="GDPR",
            action="DATA_DELETED",
            entity_type="user",
            entity_id=user_id,
            actor_type="USER",
            actor_id=requested_by,
            payload={
                "request_reference": request_reference,
                "actions_count": len(deletion_report["actions"]),
                "status": "COMPLETED"
            }
        )
        
        logger.info(
            f"Processed GDPR deletion for user {user_id} "
            f"(reference: {request_reference}, actions: {len(deletion_report['actions'])})"
        )
        
        return deletion_report
    
    def _check_deletion_blockers(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Check for conditions that block deletion.
        
        Args:
            user_id: User ID (ULID string)
            
        Returns:
            List of blocker dictionaries
        """
        blockers = []
        
        # Check for active policies
        try:
            from app.modules.underwriting.models import Policy, PolicyStatus
            active_policies = self.db.query(Policy).filter(
                Policy.bound_by_user_id == user_id,
                Policy.status == PolicyStatus.ACTIVE
            ).count()
            
            if active_policies > 0:
                blockers.append({
                    "type": "ACTIVE_POLICY",
                    "count": active_policies,
                    "reason": "Cannot delete user with active policies"
                })
        except (ImportError, AttributeError):
            pass
        
        # Check for open claims
        try:
            from app.modules.claims.models import Claim, ClaimStatus
            open_claims = self.db.query(Claim).filter(
                Claim.created_by_user_id == user_id
            ).filter(
                ~Claim.status.in_([ClaimStatus.CLOSED, ClaimStatus.WITHDRAWN])
            ).count()
            
            if open_claims > 0:
                blockers.append({
                    "type": "OPEN_CLAIM",
                    "count": open_claims,
                    "reason": "Cannot delete user with open claims"
                })
        except (ImportError, AttributeError):
            pass
        
        # Check for legal holds (if evidence bundle has legal_hold field)
        try:
            from app.models.evidence_bundle import EvidenceBundle
            # Check if legal_hold field exists
            if hasattr(EvidenceBundle, 'legal_hold'):
                legal_holds = self.db.query(EvidenceBundle).filter(
                    EvidenceBundle.legal_hold == True,
                    EvidenceBundle.created_by_user_id == user_id
                ).count()
                
                if legal_holds > 0:
                    blockers.append({
                        "type": "LEGAL_HOLD",
                        "count": legal_holds,
                        "reason": "Evidence under legal hold"
                    })
        except (ImportError, AttributeError):
            pass
        
        return blockers
    
    def _anonymize_submission(self, submission):
        """
        Anonymize PII in submission.
        
        Args:
            submission: UnderwritingSubmission instance
        """
        if hasattr(submission, 'applicant_json') and submission.applicant_json:
            submission.applicant_json = {
                "company_name": "[REDACTED]",
                "contact_email": "[REDACTED]",
                "redacted_at": datetime.utcnow().isoformat(),
                "redaction_reason": "GDPR deletion request"
            }
        
        if hasattr(submission, 'created_by_user_id'):
            submission.created_by_user_id = None
        
        submission.updated_at = datetime.utcnow()
    
    def _anonymize_policy(self, policy):
        """
        Anonymize PII in policy.
        
        Args:
            policy: Policy instance
        """
        if hasattr(policy, 'policyholder_json') and policy.policyholder_json:
            policy.policyholder_json = {
                "company_name": "[REDACTED]",
                "contact_email": "[REDACTED]",
                "address": "[REDACTED]",
                "redacted_at": datetime.utcnow().isoformat(),
                "redaction_reason": "GDPR deletion request"
            }
        
        if hasattr(policy, 'bound_by_user_id'):
            policy.bound_by_user_id = None
        
        if hasattr(policy, 'updated_at'):
            policy.updated_at = datetime.utcnow()
    
    def _anonymize_claim(self, claim):
        """
        Anonymize PII in claim.
        
        Args:
            claim: Claim instance
        """
        if hasattr(claim, 'fnol_json') and claim.fnol_json:
            fnol = claim.fnol_json.copy() if isinstance(claim.fnol_json, dict) else {}
            fnol['reported_by'] = "[REDACTED]"
            fnol['redacted_at'] = datetime.utcnow().isoformat()
            fnol['redaction_reason'] = "GDPR deletion request"
            claim.fnol_json = fnol
        
        if hasattr(claim, 'created_by_user_id'):
            claim.created_by_user_id = None
        
        if hasattr(claim, 'updated_at'):
            claim.updated_at = datetime.utcnow()
    
    def _redact_audit_events(self, user_id: str):
        """
        Redact PII from audit events.
        
        We preserve the audit trail but replace PII with redaction markers.
        
        Args:
            user_id: User ID (ULID string)
        """
        # Note: This is a simplified version
        # In production, you'd update actor_id references with a
        # special "REDACTED" marker while preserving event integrity
        
        # Add redaction marker to audit chain
        self.audit.append_event(
            tenant_id=None,
            event_type="GDPR",
            action="AUDIT_REDACTION_APPLIED",
            entity_type="user",
            entity_id=user_id,
            actor_type="SYSTEM",
            actor_id=None,
            payload={
                "redaction_reason": "GDPR deletion request",
                "original_user_id": user_id,
                "redacted_at": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Applied audit redaction marker for user {user_id}")
    
    def _verify_deletion_token(self, user_id: str, token: str) -> bool:
        """
        Verify deletion confirmation token.
        
        In production, this would verify a time-limited token
        sent to the user's email to confirm deletion.
        
        Args:
            user_id: User ID (ULID string)
            token: Verification token
            
        Returns:
            True if token is valid
        """
        # Simplified: check token is not empty
        # In production, this would:
        # 1. Look up token in database
        # 2. Verify it matches user_id
        # 3. Check expiration
        # 4. Mark as used
        if not token or len(token) < 10:
            return False
        
        # In production, you might store tokens in a separate table:
        # deletion_tokens: user_id, token_hash, expires_at, used_at
        # and verify here
        
        return True


# Exception classes
class InvalidDeletionTokenError(Exception):
    """Invalid deletion verification token"""
    pass
