"""
RiskCast Monitoring Module

Provides metrics, tracing, and observability capabilities.
"""

import logging

_logger = logging.getLogger(__name__)

# Import metrics (should always work)
from .metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    RISK_ASSESSMENT_COUNT,
    QUOTE_COUNT,
    ACTIVE_POLICIES,
    track_request_metrics,
    track_risk_assessment,
    track_external_request,
    metrics_endpoint,
    setup_app_info
)

# Import tracing with graceful fallback
try:
    from .tracing import (
        setup_tracing,
        instrument_app,
        instrument_database,
        instrument_redis,
        get_tracer,
        TracedOperation,
        traced
    )
    TRACING_AVAILABLE = True
except ImportError as e:
    _logger.warning(f"Tracing module not available: {e}. Using no-op fallbacks.")
    TRACING_AVAILABLE = False
    
    # Create no-op fallback implementations
    def setup_tracing(*args, **kwargs):
        _logger.debug("Tracing not available - setup_tracing is no-op")
        return None
    
    def instrument_app(app):
        _logger.debug("Tracing not available - instrument_app is no-op")
        pass
    
    def instrument_database(engine):
        _logger.debug("Tracing not available - instrument_database is no-op")
        pass
    
    def instrument_redis():
        _logger.debug("Tracing not available - instrument_redis is no-op")
        pass
    
    def get_tracer(name: str = __name__):
        return None
    
    class TracedOperation:
        """No-op context manager when tracing is unavailable."""
        def __init__(self, name: str, attributes=None):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
    
    def traced(name=None, attributes=None):
        """No-op decorator when tracing is unavailable."""
        def decorator(func):
            return func
        return decorator

__all__ = [
    # Metrics
    'REQUEST_COUNT',
    'REQUEST_LATENCY',
    'RISK_ASSESSMENT_COUNT',
    'QUOTE_COUNT',
    'ACTIVE_POLICIES',
    'track_request_metrics',
    'track_risk_assessment',
    'track_external_request',
    'metrics_endpoint',
    'setup_app_info',
    
    # Tracing
    'setup_tracing',
    'instrument_app',
    'instrument_database',
    'instrument_redis',
    'get_tracer',
    'TracedOperation',
    'traced',
    
    # Availability flag
    'TRACING_AVAILABLE',
]
