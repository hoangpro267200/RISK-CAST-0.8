"""
Claims State Machine
State machine for claims workflow with transition validation
RISKCAST V3 - Modular Monolith
"""
from typing import List, Dict, Any

from app.modules.claims.models import (
    Claim,
    ClaimStatus,
    PayoutStatus
)


class ClaimsStateMachine:
    """
    State machine for claims workflow.
    Validates transitions and enforces preconditions.
    """
    
    VALID_TRANSITIONS = {
        ClaimStatus.FNOL_RECEIVED: {ClaimStatus.UNDER_INVESTIGATION, ClaimStatus.WITHDRAWN},
        ClaimStatus.UNDER_INVESTIGATION: {
            ClaimStatus.AWAITING_EVIDENCE,
            ClaimStatus.APPROVED,
            ClaimStatus.DECLINED
        },
        ClaimStatus.AWAITING_EVIDENCE: {ClaimStatus.UNDER_INVESTIGATION, ClaimStatus.WITHDRAWN},
        ClaimStatus.APPROVED: {ClaimStatus.AUTHORIZED},
        ClaimStatus.AUTHORIZED: {ClaimStatus.PAID},
        ClaimStatus.PAID: {ClaimStatus.CLOSED},
        ClaimStatus.DECLINED: {ClaimStatus.CLOSED},
        ClaimStatus.CLOSED: set(),  # Terminal
        ClaimStatus.WITHDRAWN: set(),  # Terminal
    }
    
    @classmethod
    def can_transition(cls, from_status: ClaimStatus, to_status: ClaimStatus) -> bool:
        """
        Check if transition is allowed.
        
        Args:
            from_status: Current status
            to_status: Target status
            
        Returns:
            True if transition is valid, False otherwise
        """
        valid_targets = cls.VALID_TRANSITIONS.get(from_status, set())
        return to_status in valid_targets
    
    @classmethod
    def get_valid_transitions(cls, from_status: ClaimStatus) -> set:
        """Get all valid target states from current state."""
        return cls.VALID_TRANSITIONS.get(from_status, set())
    
    @classmethod
    def is_terminal(cls, status: ClaimStatus) -> bool:
        """Check if status is terminal."""
        return len(cls.VALID_TRANSITIONS.get(status, set())) == 0
    
    def validate_transition(
        self,
        claim: Claim,
        to_status: ClaimStatus,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Validate transition preconditions.
        
        Args:
            claim: Claim instance
            to_status: Target status
            context: Additional context (evidence_bundle_id, payout, etc.)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check if transition is allowed
        if not self.can_transition(claim.status, to_status):
            errors.append(
                f"Invalid transition from {claim.status.value} to {to_status.value}. "
                f"Valid transitions from {claim.status.value}: "
                f"{[s.value for s in self.VALID_TRANSITIONS.get(claim.status, [])]}"
            )
            return errors  # Return early if transition is invalid
        
        # Specific validations
        if to_status in [ClaimStatus.APPROVED, ClaimStatus.DECLINED]:
            if not context.get('evidence_bundle_id'):
                errors.append("Evidence bundle required for adjudication")
        
        if to_status == ClaimStatus.AUTHORIZED:
            if not context.get('payout_id'):
                errors.append("Payout must be created before authorization")
            
            # Verify payout exists and is in correct status
            payout = context.get('payout')
            if payout:
                if payout.status not in [PayoutStatus.PROPOSED, PayoutStatus.APPROVED]:
                    errors.append(
                        f"Payout must be PROPOSED or APPROVED before authorization. "
                        f"Current status: {payout.status.value}"
                    )
        
        if to_status == ClaimStatus.PAID:
            payout = context.get('payout')
            if not payout:
                errors.append("Payout must be provided for payment")
            elif payout.status != PayoutStatus.AUTHORIZED:
                errors.append(
                    f"Payout must be AUTHORIZED before payment. "
                    f"Current status: {payout.status.value}"
                )
        
        return errors
    
    
    @classmethod
    def get_transition_path(
        cls,
        from_status: ClaimStatus,
        to_status: ClaimStatus
    ) -> List[ClaimStatus]:
        """
        Get shortest path between two statuses (if possible).
        
        Uses BFS to find shortest path.
        
        Args:
            from_status: Starting status
            to_status: Target status
            
        Returns:
            List of statuses in transition path, or empty list if no path exists
        """
        if from_status == to_status:
            return [from_status]
        
        if cls.can_transition(from_status, to_status):
            return [from_status, to_status]
        
        # Simple BFS to find path
        from collections import deque
        
        queue = deque([(from_status, [from_status])])
        visited = {from_status}
        
        while queue:
            current, path = queue.popleft()
            
            for next_status in cls.get_valid_transitions(current):
                if next_status == to_status:
                    return path + [next_status]
                
                if next_status not in visited:
                    visited.add(next_status)
                    queue.append((next_status, path + [next_status]))
        
        return []  # No path found
