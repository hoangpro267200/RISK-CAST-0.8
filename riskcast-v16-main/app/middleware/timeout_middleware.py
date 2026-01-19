"""
Request Timeout Middleware (RC-C005)

CRITICAL: Prevents long-running requests from blocking the server.
Applies timeout to all API requests to ensure system responsiveness.
"""
import asyncio
from typing import Callable
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

# Default timeout: 30 seconds for API requests
# Risk analysis can take longer, so we use a generous timeout
DEFAULT_TIMEOUT = 30.0  # seconds

# Per-endpoint timeouts (in seconds)
ENDPOINT_TIMEOUTS = {
    "/api/v1/risk/v2/analyze": 60.0,  # Risk analysis can take up to 60s
    "/api/v1/risk/v2/simulate": 45.0,  # Simulation can take up to 45s
    "/api/v1/risk/v2/report/pdf": 90.0,  # PDF generation can take up to 90s
}


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies timeout to requests.
    
    If a request takes longer than the configured timeout, it will be cancelled
    and a 504 Gateway Timeout response will be returned.
    """
    
    def __init__(self, app, default_timeout: float = DEFAULT_TIMEOUT):
        super().__init__(app)
        self.default_timeout = default_timeout
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Apply timeout to request processing.
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response (or 504 if timeout exceeded)
        """
        # Determine timeout for this endpoint
        path = request.url.path
        timeout = ENDPOINT_TIMEOUTS.get(path, self.default_timeout)
        
        # Skip timeout for static files (they're fast)
        if path.startswith(("/assets/", "/static/", "/dist/")):
            return await call_next(request)
        
        try:
            # Run request with timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=timeout
            )
            return response
            
        except asyncio.TimeoutError:
            # Request exceeded timeout
            logger.warning(
                f"Request timeout: {request.method} {path} exceeded {timeout}s",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "path": path,
                    "timeout": timeout
                }
            )
            
            # Return 504 Gateway Timeout
            from app.utils.standard_responses import StandardResponse
            return StandardResponse.error(
                message=f"Request timeout: operation exceeded {timeout} seconds",
                error_code="REQUEST_TIMEOUT",
                status_code=504,
                error_type="server",
                request=request
            )
        except Exception as e:
            # Re-raise other exceptions (they'll be handled by error handler)
            raise
