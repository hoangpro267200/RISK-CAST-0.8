"""
Shared Exception Classes
RISKCAST V3 - Modular Monolith
"""
from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class RISKCASTException(HTTPException):
    """Base exception for RISKCAST application"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.metadata = metadata or {}


class ValidationError(RISKCASTException):
    """Validation error"""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
            metadata={"field": field} if field else {}
        )


class NotFoundError(RISKCASTException):
    """Resource not found"""
    
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        detail = f"{resource} not found"
        if resource_id:
            detail += f": {resource_id}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
            metadata={"resource": resource, "resource_id": resource_id}
        )


class UnauthorizedError(RISKCASTException):
    """Unauthorized access"""
    
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )


class ForbiddenError(RISKCASTException):
    """Forbidden access"""
    
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )


class ConflictError(RISKCASTException):
    """Resource conflict"""
    
    def __init__(self, detail: str, resource: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT",
            metadata={"resource": resource} if resource else {}
        )


class InternalServerError(RISKCASTException):
    """Internal server error"""
    
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="INTERNAL_ERROR"
        )
