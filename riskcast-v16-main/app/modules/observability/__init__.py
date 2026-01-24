"""
Observability Module
Logging, metrics, and tracing
RISKCAST V3 - Modular Monolith
"""
from app.modules.observability.logging import (
    logger,
    get_logger,
    configure_logging,
    set_request_context,
    clear_request_context
)
from app.modules.observability.middleware import ObservabilityMiddleware
from app.modules.observability.metrics import (
    record_api_request,
    record_api_error,
    record_risk_run,
    record_risk_assessment,
    record_audit_event,
    record_worker_job,
    update_queue_depth,
    update_worker_queue_depth
)
# Optional tracing imports
try:
    from app.modules.observability.tracing import (
        setup_tracing,
        get_tracer,
        create_span
    )
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Tracing module not available: {e}")
    # Create no-op functions
    def setup_tracing(*args, **kwargs):
        return None
    def get_tracer(*args, **kwargs):
        return None
    def create_span(*args, **kwargs):
        class NoOpSpan:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return NoOpSpan()

__all__ = [
    # Logging
    'logger',
    'get_logger',
    'configure_logging',
    'set_request_context',
    'clear_request_context',
    # Middleware
    'ObservabilityMiddleware',
    # Metrics
    'record_api_request',
    'record_api_error',
    'record_risk_run',
    'record_risk_assessment',
    'record_audit_event',
    'record_worker_job',
    'update_queue_depth',
    'update_worker_queue_depth',
    # Tracing
    'setup_tracing',
    'get_tracer',
    'create_span',
]
