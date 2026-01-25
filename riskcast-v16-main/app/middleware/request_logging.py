"""
Request/Response Logging Middleware

Logs all HTTP requests with timing and context.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import (
    get_logger,
    set_request_context,
    clear_request_context,
    mask_sensitive_data
)


logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.
    """
    
    # Paths to exclude from detailed logging
    EXCLUDE_PATHS = {
        '/health/live',
        '/health/ready',
        '/health/startup',
        '/metrics',
        '/favicon.ico'
    }
    
    # Headers to log (others are excluded for security)
    SAFE_HEADERS = {
        'content-type',
        'content-length',
        'accept',
        'accept-encoding',
        'accept-language',
        'user-agent',
        'x-request-id',
        'x-trace-id',
        'x-forwarded-for',
        'x-real-ip'
    }
    
    def __init__(self, app: ASGIApp, log_request_body: bool = False, log_response_body: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        trace_id = request.headers.get('X-Trace-ID') or request.headers.get('X-B3-TraceId')
        
        # Extract user context (if authenticated)
        user_id = getattr(request.state, 'user_id', None)
        tenant_id = getattr(request.state, 'tenant_id', None)
        
        # Set logging context
        set_request_context(
            request_id=request_id,
            trace_id=trace_id,
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        # Store request ID in request state
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.perf_counter()
        
        # Skip detailed logging for excluded paths
        if request.url.path in self.EXCLUDE_PATHS:
            response = await call_next(request)
            response.headers['X-Request-ID'] = request_id
            clear_request_context()
            return response
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        response = None
        error = None
        
        try:
            response = await call_next(request)
        except Exception as e:
            error = e
            raise
        finally:
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log response
            self._log_response(request, response, duration_ms, error)
            
            # Add headers to response
            if response:
                response.headers['X-Request-ID'] = request_id
                response.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"
            
            # Clear context
            clear_request_context()
        
        return response
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request."""
        # Extract client IP
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            client_ip = forwarded.split(',')[0].strip()
        
        # Safe headers
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() in self.SAFE_HEADERS
        }
        
        # Query params (masked)
        query_params = mask_sensitive_data(dict(request.query_params))
        
        log_data = {
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "query_params": query_params,
            "client_ip": client_ip,
            "headers": headers,
            "user_agent": request.headers.get('User-Agent', 'unknown'),
        }
        
        # Optionally log request body
        if self.log_request_body and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body and len(body) < 10000:  # Limit body size
                    import json
                    try:
                        body_json = json.loads(body)
                        log_data["body"] = mask_sensitive_data(body_json)
                    except json.JSONDecodeError:
                        log_data["body_size"] = len(body)
            except Exception:
                pass
        
        logger.info("Incoming request", **log_data)
    
    def _log_response(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        error: Exception = None
    ):
        """Log outgoing response."""
        log_data = {
            "event": "http_response",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code if response else 500,
            "duration_ms": round(duration_ms, 2),
        }
        
        if error:
            log_data["error"] = str(error)
            log_data["error_type"] = type(error).__name__
        
        # Determine log level based on status code
        status_code = response.status_code if response else 500
        
        if status_code >= 500:
            logger.error("Request failed", **log_data)
        elif status_code >= 400:
            logger.warning("Client error", **log_data)
        else:
            logger.info("Request completed", **log_data)


class SlowRequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log slow requests for performance monitoring.
    """
    
    def __init__(self, app: ASGIApp, threshold_ms: float = 1000):
        super().__init__(app)
        self.threshold_ms = threshold_ms
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        if duration_ms > self.threshold_ms:
            logger.warning(
                "Slow request detected",
                event="slow_request",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                threshold_ms=self.threshold_ms
            )
        
        return response
