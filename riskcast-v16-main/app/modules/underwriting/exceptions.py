"""
Underwriting Module Exceptions
Custom exceptions for underwriting
RISKCAST V3 - Modular Monolith
"""
from fastapi import HTTPException, status


class SubmissionNotFoundError(HTTPException):
    """Underwriting submission not found"""
    def __init__(self, submission_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Underwriting submission not found: {submission_id}"
        )


class InvalidTransitionError(HTTPException):
    """Invalid state transition"""
    def __init__(self, errors: list):
        error_message = "; ".join(errors)
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: {error_message}"
        )
