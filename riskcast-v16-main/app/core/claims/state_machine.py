"""
Claims state machine.

Defines valid states, transitions, and invariants.
"""

from typing import Set, Dict, List, Tuple, Optional
from dataclasses import dataclass

from app.modules.claims.models import ClaimStatus


@dataclass
class ClaimTransitionRule:
    """Rule for claim state transitions."""
    from_status: ClaimStatus
    to_status: ClaimStatus
    required_fields: List[str]
    evidence_required: bool
    description: str


class ClaimStateMachine:
    """State machine for claims."""
    
    TRANSITIONS: Dict[ClaimStatus, Set[ClaimStatus]] = {
        ClaimStatus.FNOL_RECEIVED: {
            ClaimStatus.UNDER_INVESTIGATION, 
            ClaimStatus.WITHDRAWN
        },
        ClaimStatus.UNDER_INVESTIGATION: {
            ClaimStatus.AWAITING_EVIDENCE,
            ClaimStatus.APPROVED,
            ClaimStatus.DECLINED
        },
        ClaimStatus.AWAITING_EVIDENCE: {
            ClaimStatus.UNDER_INVESTIGATION,
            ClaimStatus.WITHDRAWN
        },
        ClaimStatus.APPROVED: {
            ClaimStatus.AUTHORIZED
        },
        ClaimStatus.DECLINED: {
            ClaimStatus.CLOSED
        },
        ClaimStatus.AUTHORIZED: {
            ClaimStatus.PAID
        },
        ClaimStatus.PAID: {
            ClaimStatus.CLOSED
        },
        ClaimStatus.CLOSED: set(),  # Terminal
        ClaimStatus.WITHDRAWN: set(),  # Terminal
    }
    
    RULES: List[ClaimTransitionRule] = [
        ClaimTransitionRule(
            from_status=ClaimStatus.FNOL_RECEIVED,
            to_status=ClaimStatus.UNDER_INVESTIGATION,
            required_fields=['assigned_adjuster_id'],
            evidence_required=False,
            description="Begin investigation requires adjuster assignment"
        ),
        ClaimTransitionRule(
            from_status=ClaimStatus.UNDER_INVESTIGATION,
            to_status=ClaimStatus.APPROVED,
            required_fields=['evidence_bundle_id', 'approved_amount_cents', 'adjudication_json'],
            evidence_required=True,
            description="Approval requires evidence bundle, amount, and adjudication"
        ),
        ClaimTransitionRule(
            from_status=ClaimStatus.UNDER_INVESTIGATION,
            to_status=ClaimStatus.DECLINED,
            required_fields=['decision_reason'],
            evidence_required=True,
            description="Decline requires reason and evidence review"
        ),
        ClaimTransitionRule(
            from_status=ClaimStatus.APPROVED,
            to_status=ClaimStatus.AUTHORIZED,
            required_fields=[],  # Authorization is separate control
            evidence_required=False,
            description="Authorization is payout approval step"
        ),
        ClaimTransitionRule(
            from_status=ClaimStatus.AUTHORIZED,
            to_status=ClaimStatus.PAID,
            required_fields=['payout_id'],
            evidence_required=False,
            description="Paid requires payout record"
        ),
    ]
    
    @classmethod
    def can_transition(cls, current: ClaimStatus, target: ClaimStatus) -> bool:
        """Check if transition is valid."""
        return target in cls.TRANSITIONS.get(current, set())
    
    @classmethod
    def get_valid_transitions(cls, current: ClaimStatus) -> Set[ClaimStatus]:
        """Get all valid target states from current state."""
        return cls.TRANSITIONS.get(current, set())
    
    @classmethod
    def validate_transition(
        cls,
        claim,
        target_status: ClaimStatus,
        context: Optional[Dict] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate transition with invariants.
        
        Args:
            claim: Claim instance
            target_status: Target status
            context: Optional context dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        context = context or {}
        
        current = ClaimStatus(claim.status)
        
        if not cls.can_transition(current, target_status):
            errors.append(f"Invalid transition: {current.value} → {target_status.value}")
            return False, errors
        
        # Check rules
        for rule in cls.RULES:
            if rule.from_status == current and rule.to_status == target_status:
                for field in rule.required_fields:
                    value = getattr(claim, field, None)
                    if value is None:
                        # Check context if field might be in context
                        if field not in context or context[field] is None:
                            errors.append(f"Missing required field: {field}")
                
                if rule.evidence_required and not claim.evidence_bundle_id:
                    errors.append("Evidence bundle required for this transition")
        
        return len(errors) == 0, errors
    
    @classmethod
    def is_terminal(cls, status: ClaimStatus) -> bool:
        """Check if status is terminal."""
        return len(cls.TRANSITIONS.get(status, set())) == 0
    
    @classmethod
    def requires_authorization(cls, status: ClaimStatus) -> bool:
        """Check if status requires authorization control."""
        return status == ClaimStatus.AUTHORIZED
