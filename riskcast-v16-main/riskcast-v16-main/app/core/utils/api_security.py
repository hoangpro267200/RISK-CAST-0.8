"""
RISKCAST Security - API Security Utilities
Common security functions for API routes
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import os

from app.core.utils.sanitizer import sanitize_input
from app.core.utils.rate_limiter import rate_limiter, ai_rate_limit
from app.core.utils.audit import log_api_call, log_security_event
from app.core.utils.auth import optional_auth


def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    if request.client:
        return request.client.host
    
    return "unknown"


def validate_payload_size(request: Request, max_size_mb: int = 5) -> None:
    """
    Validate request payload size
    
    Args:
        request: FastAPI request
        max_size_mb: Maximum payload size in MB
        
    Raises:
        HTTPException: If payload too large
    """
    content_length = request.headers.get("content-length")
    if content_length:
        size_bytes = int(content_length)
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb > max_size_mb:
            log_security_event("PAYLOAD_TOO_LARGE", {
                "size_mb": size_mb,
                "max_mb": max_size_mb,
                "endpoint": request.url.path
            }, ip=get_client_ip(request))
            
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Payload too large. Maximum size is {max_size_mb}MB"
            )


def sanitize_request_data(data: Any) -> Any:
    """
    Sanitize request data
    
    Args:
        data: Request data (dict, list, or string)
        
    Returns:
        Sanitized data
    """
    return sanitize_input(data)


async def secure_api_endpoint(
    request: Request,
    require_auth: bool = False,
    rate_limit_per_minute: Optional[int] = None,
    max_payload_mb: int = 5,
    sanitize: bool = True
) -> Dict[str, Any]:
    """
    Apply all security checks to an API endpoint
    
    Args:
        request: FastAPI request
        require_auth: Whether authentication is required
        rate_limit_per_minute: Custom rate limit (None = default)
        max_payload_mb: Maximum payload size in MB
        sanitize: Whether to sanitize input
        
    Returns:
        Dictionary with security context
        
    Raises:
        HTTPException: If security check fails
    """
    client_ip = get_client_ip(request)
    
    # Validate payload size
    validate_payload_size(request, max_payload_mb)
    
    # Check rate limit
    if rate_limit_per_minute:
        rate_limiter.check_rate_limit(request, limit=rate_limit_per_minute)
    else:
        rate_limiter.check_rate_limit(request)
    
    # Optional authentication
    user_id = None
    if hasattr(request.state, 'user_id'):
        user_id = request.state.user_id
    
    # Return security context
    return {
        "client_ip": client_ip,
        "user_id": user_id,
        "request": request
    }


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error messages to prevent information leakage
    
    Args:
        error: Exception object
        
    Returns:
        Safe error message
    """
    error_msg = str(error)
    
    # Remove API keys
    import re
    error_msg = re.sub(
        r'api[_-]?key["\']?\s*[:=]\s*["\']?[^\s"\']+',
        'api_key=***HIDDEN***',
        error_msg,
        flags=re.IGNORECASE
    )
    
    # Remove secrets
    error_msg = re.sub(
        r'secret["\']?\s*[:=]\s*["\']?[^\s"\']+',
        'secret=***HIDDEN***',
        error_msg,
        flags=re.IGNORECASE
    )
    
    # Remove file paths (potential information leakage)
    if os.getenv("ENVIRONMENT") == "production":
        error_msg = re.sub(r'[a-zA-Z]:\\.*?\\', '***\\', error_msg)
        error_msg = re.sub(r'/.*?/', '***/', error_msg)
    
    return error_msg





















