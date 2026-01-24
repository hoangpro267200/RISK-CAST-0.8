"""
Structured Logging with Correlation IDs
RISKCAST V3 - Modular Monolith
"""
import structlog
import logging
from contextvars import ContextVar
from typing import Optional

# Context variables for correlation
request_id_ctx: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
trace_id_ctx: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
tenant_id_ctx: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)
actor_id_ctx: ContextVar[Optional[str]] = ContextVar('actor_id', default=None)


def add_context(logger, method_name, event_dict):
    """Add context variables to log entries"""
    request_id = request_id_ctx.get()
    trace_id = trace_id_ctx.get()
    tenant_id = tenant_id_ctx.get()
    actor_id = actor_id_ctx.get()
    
    if request_id:
        event_dict['request_id'] = request_id
    if trace_id:
        event_dict['trace_id'] = trace_id
    if tenant_id:
        event_dict['tenant_id'] = tenant_id
    if actor_id:
        event_dict['actor_id'] = actor_id
    
    return event_dict


def configure_logging(log_level: str = "INFO", json_output: bool = True):
    """
    Configure structlog for structured JSON output.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Whether to use JSON output (True) or console output (False)
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=open('/dev/null', 'w') if json_output else None,
        level=getattr(logging, log_level.upper(), logging.INFO)
    )
    
    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        add_context,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend([
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.dev.ConsoleRenderer()
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None):
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (optional)
        
    Returns:
        structlog logger instance
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


# Default logger instance
logger = get_logger(__name__)


def set_request_context(
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    actor_id: Optional[str] = None
):
    """
    Set correlation context variables.
    
    Args:
        request_id: Request ID
        trace_id: Trace ID
        tenant_id: Tenant ID
        actor_id: Actor ID (user or API key)
    """
    if request_id is not None:
        request_id_ctx.set(request_id)
    if trace_id is not None:
        trace_id_ctx.set(trace_id)
    if tenant_id is not None:
        tenant_id_ctx.set(tenant_id)
    if actor_id is not None:
        actor_id_ctx.set(actor_id)


def clear_request_context():
    """Clear all correlation context variables"""
    request_id_ctx.set(None)
    trace_id_ctx.set(None)
    tenant_id_ctx.set(None)
    actor_id_ctx.set(None)
