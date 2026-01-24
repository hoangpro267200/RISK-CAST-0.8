"""
Claims Module Exceptions
Custom exceptions for claims management
RISKCAST V3 - Modular Monolith
"""
from fastapi import HTTPException, status
from typing import Optional, List


class ClaimNotFoundError(HTTPException):
    """Claim not found"""
    def __init__(self, claim_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim not found: {claim_id}"
        )


class PolicyNotFoundError(HTTPException):
    """Policy not found"""
    def __init__(self, policy_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy not found: {policy_id}"
        )


class InvalidPolicyStatusError(HTTPException):
    """Invalid policy status for operation"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid policy status: {message}"
        )


class InvalidActionError(HTTPException):
    """Invalid action for claim"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {message}"
        )


class InvalidTransitionError(HTTPException):
    """Invalid state transition"""
    def __init__(self, errors: List[str]):
        error_message = "; ".join(errors)
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: {error_message}"
        )


class PayoutNotFoundError(HTTPException):
    """Payout not found"""
    def __init__(self, payout_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payout not found: {payout_id}"
        )
