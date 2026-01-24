"""
Oracle Gateway Exceptions
Custom exceptions for oracle gateway operations.
"""
from __future__ import annotations


class OracleError(Exception):
    """Base exception for oracle gateway errors"""
    pass


class OracleNotConfiguredError(OracleError):
    """Raised when an oracle provider is not configured"""
    pass


class OracleValidationError(OracleError):
    """Raised when oracle payload validation fails"""
    pass


class OracleFetchError(OracleError):
    """Raised when fetching from oracle provider fails"""
    pass


class InvalidTriggerEvaluationError(OracleError):
    """Raised when trigger evaluation is invalid (e.g., uses stub data)"""
    pass


class PayoutBlockedError(OracleError):
    """Raised when payout is blocked due to safety guards"""
    pass
