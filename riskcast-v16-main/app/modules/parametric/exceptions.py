"""
Parametric Module Exceptions
Custom exceptions for parametric insurance
RISKCAST V3 - Modular Monolith
"""
from fastapi import HTTPException, status
from typing import List


class TriggerDefinitionNotFoundError(HTTPException):
    """Trigger definition not found"""
    def __init__(self, trigger_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trigger definition not found: {trigger_id}"
        )


class TriggerAlreadyPublishedError(HTTPException):
    """Trigger definition already published"""
    def __init__(self, trigger_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trigger definition already published: {trigger_id}"
        )


class TriggerEventNotFoundError(HTTPException):
    """Trigger event not found"""
    def __init__(self, trigger_event_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trigger event not found: {trigger_event_id}"
        )


class InvalidTransitionError(HTTPException):
    """Invalid state transition"""
    def __init__(self, errors: List[str]):
        error_message = "; ".join(errors)
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: {error_message}"
        )
