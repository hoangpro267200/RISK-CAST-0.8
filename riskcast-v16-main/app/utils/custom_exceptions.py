"""
RISKCAST - Custom Exceptions
Custom exception classes for better error handling
"""
from typing import Any, Dict, Optional


class RISKCASTException(Exception):
    """Base exception for RISKCAST application"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "RISKCAST_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(RISKCASTException):
    """Validation error exception"""
    
    def __init__(
        self,
        message: str = "Validation error",
        field_errors: Optional[Dict[str, list]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.field_errors = field_errors or {}
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details or {}
        )


class RiskCalculationError(RISKCASTException):
    """Risk calculation error"""
    
    def __init__(
        self,
        message: str = "Risk calculation failed",
        calculation_step: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.calculation_step = calculation_step
        super().__init__(
            message=message,
            error_code="RISK_CALCULATION_ERROR",
            details=details or {}
        )


class DataNotFoundError(RISKCASTException):
    """Data not found error"""
    
    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
            
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details=details or {}
        )


class ConfigurationError(RISKCASTException):
    """Configuration error"""
    
    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.config_key = config_key
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details or {}
        )


class ExternalAPIError(RISKCASTException):
    """External API error"""
    
    def __init__(
        self,
        message: str = "External API error",
        api_name: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            details=details or {}
        )

