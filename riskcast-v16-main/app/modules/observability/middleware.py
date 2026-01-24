"""
Observability Middleware
Request/response logging and correlation ID management
RISKCAST V3 - Modular Monolith
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import uuid
import time
from typing import Callable

from app.modules.observability.logging import (
    logger,
    set_request_context,
    clear_request_context
)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response logging and correlation ID management.
    
    Features:
    - Generates/extracts correlation IDs (request_id, trace_id)
    - Logs request start/end with timing
    - Adds correlation headers to responses
    - Sets context variables for structured logging
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation IDs
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        trace_id = request.headers.get('X-Trace-ID') or request.headers.get('X-Request-ID') or str(uuid.uuid4())
        
        # Set context variables for structured logging
        set_request_context(
            request_id=request_id,
            trace_id=trace_id,
            tenant_id=None,  # Will be set by resolve_tenant_context
            actor_id=None    # Will be set by resolve_tenant_context
        )
        
        # Store in request state (for use in dependencies)
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        
        # Get client IP
        client_ip = None
        if request.client:
            client_ip = request.client.host
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        logger.info(
            "request_started",
            method=request.method,
            path=str(request.url.path),
            query_params=str(request.url.query) if request.url.query else None,
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent"),
            content_type=request.headers.get("content-type"),
            content_length=request.headers.get("content-length")
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request completion
            logger.info(
                "request_completed",
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2)
            )
            
            # Add correlation headers to response
            response.headers['X-Request-ID'] = request_id
            response.headers['X-Trace-ID'] = trace_id
            
            return response
            
        except Exception as e:
            # Calculate duration even on error
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request error
            logger.error(
                "request_failed",
                method=request.method,
                path=str(request.url.path),
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=round(duration_ms, 2),
                exc_info=True
            )
            
            # Re-raise exception
            raise
            
        finally:
            # Clear context variables (important for async context)
            clear_request_context()
