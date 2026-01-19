"""
RISKCAST - Request ID Middleware

Generates and propagates request_id for all requests.
Request ID is included in response headers and available in request.state
for use in logs and responses.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and propagate request_id
    
    Features:
    - Generates unique request_id for each request
    - Stores in request.state for access in handlers
    - Adds X-Request-ID header to response
    - Enables request tracing across services
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Store in request state for access in handlers
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response header
        response.headers["X-Request-ID"] = request_id
        
        return response

