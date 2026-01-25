"""
RISKCAST SDK Exceptions
"""


class RiskcastError(Exception):
    """Base exception for all RISKCAST SDK errors."""
    
    def __init__(self, message: str, code: str = None, status_code: int = None, details: dict = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(RiskcastError):
    """Authentication failed."""
    pass


class AuthorizationError(RiskcastError):
    """Authorization failed - insufficient permissions."""
    pass


class RateLimitError(RiskcastError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ValidationError(RiskcastError):
    """Request validation failed."""
    pass


class NotFoundError(RiskcastError):
    """Resource not found."""
    pass


class ServerError(RiskcastError):
    """Server error."""
    pass
