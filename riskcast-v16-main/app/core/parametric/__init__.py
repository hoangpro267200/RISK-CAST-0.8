"""
Parametric Core Module
Oracle gateway and provider interfaces for parametric triggers.
"""
from app.core.parametric.oracle_gateway import (
    OracleGateway,
    OracleProvider,
    OraclePayload,
    ValidationResult,
    OracleQuery,
)
from app.core.parametric.exceptions import (
    OracleNotConfiguredError,
    OracleValidationError,
    OracleFetchError,
)

__all__ = [
    'OracleGateway',
    'OracleProvider',
    'OraclePayload',
    'ValidationResult',
    'OracleQuery',
    'OracleNotConfiguredError',
    'OracleValidationError',
    'OracleFetchError',
]
