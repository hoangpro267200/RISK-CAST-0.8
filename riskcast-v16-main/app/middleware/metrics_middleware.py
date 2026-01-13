"""
Prometheus Metrics Middleware (Phase 3 - Day 7)

CRITICAL: Collects metrics for observability:
- Request count (by endpoint, status)
- Request duration (p50, p95, p99)
- Error rate
- Active requests
"""
import time
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

# Try to import prometheus_client, but don't fail if not available
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not installed. Metrics will be disabled. Install with: pip install prometheus-client")


# Metrics (only create if prometheus_client is available)
if PROMETHEUS_AVAILABLE:
    # Request counter by endpoint and status
    request_counter = Counter(
        'riskcast_http_requests_total',
        'Total number of HTTP requests',
        ['method', 'endpoint', 'status_code']
    )
    
    # Request duration histogram
    request_duration = Histogram(
        'riskcast_http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['method', 'endpoint'],
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
    )
    
    # Active requests gauge
    active_requests = Gauge(
        'riskcast_http_active_requests',
        'Number of active HTTP requests',
        ['method', 'endpoint']
    )
    
    # Error counter
    error_counter = Counter(
        'riskcast_http_errors_total',
        'Total number of HTTP errors',
        ['method', 'endpoint', 'error_type']
    )
else:
    # Dummy metrics if prometheus_client not available
    request_counter = None
    request_duration = None
    active_requests = None
    error_counter = None


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that collects Prometheus metrics for all requests.
    
    Metrics collected:
    - Total requests (by method, endpoint, status)
    - Request duration (histogram)
    - Active requests (gauge)
    - Error count (by type)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Collect metrics for request.
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with metrics collected
        """
        if not PROMETHEUS_AVAILABLE:
            # If prometheus_client not available, just pass through
            return await call_next(request)
        
        # Extract endpoint (simplified path for grouping)
        endpoint = self._normalize_endpoint(request.url.path)
        method = request.method
        
        # Track active requests
        active_requests.labels(method=method, endpoint=endpoint).inc()
        
        # Start timer
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            status_code = response.status_code
            request_counter.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # Track errors (4xx and 5xx)
            if status_code >= 400:
                error_type = "client" if status_code < 500 else "server"
                error_counter.labels(
                    method=method,
                    endpoint=endpoint,
                    error_type=error_type
                ).inc()
            
            return response
            
        except Exception as e:
            # Record error
            duration = time.time() - start_time
            error_counter.labels(
                method=method,
                endpoint=endpoint,
                error_type="exception"
            ).inc()
            
            request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # Re-raise exception (error handler will catch it)
            raise
            
        finally:
            # Decrement active requests
            active_requests.labels(method=method, endpoint=endpoint).dec()
    
    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        """
        Normalize endpoint path for metrics grouping.
        
        Examples:
        - /api/v1/risk/v2/analyze -> /api/v1/risk/v2/analyze
        - /results/data -> /results/data
        - /assets/index-abc123.js -> /assets/*
        """
        # Normalize asset paths
        if path.startswith("/assets/"):
            return "/assets/*"
        if path.startswith("/static/"):
            return "/static/*"
        if path.startswith("/dist/"):
            return "/dist/*"
        
        # Keep API paths as-is (they're already normalized)
        return path


def get_metrics_endpoint():
    """
    Get FastAPI endpoint function for /metrics.
    
    Returns:
        FastAPI route handler function
    """
    if not PROMETHEUS_AVAILABLE:
        def metrics_endpoint():
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(
                "# Prometheus metrics not available. Install prometheus-client: pip install prometheus-client",
                status_code=503
            )
        return metrics_endpoint
    
    def metrics_endpoint():
        """Prometheus metrics endpoint"""
        from fastapi.responses import Response
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    return metrics_endpoint
