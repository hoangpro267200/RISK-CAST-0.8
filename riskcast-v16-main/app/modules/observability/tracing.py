"""
OpenTelemetry Tracing
RISKCAST V3 - Modular Monolith
"""
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Optional OpenTelemetry imports
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logger.warning(
        "OpenTelemetry not available. Install with: "
        "pip install opentelemetry-api opentelemetry-sdk "
        "opentelemetry-instrumentation-fastapi "
        "opentelemetry-instrumentation-sqlalchemy "
        "opentelemetry-instrumentation-requests"
    )
    
    # Create no-op classes for when OpenTelemetry is not available
    class NoOpTracer:
        def start_as_current_span(self, name, attributes=None):
            return NoOpSpan()
    
    class NoOpSpan:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def set_attribute(self, key, value):
            pass
    
    trace = type('trace', (), {
        'get_tracer': lambda name=None: NoOpTracer(),
        'set_tracer_provider': lambda provider: None,
        'NoOpTracer': NoOpTracer
    })()


def setup_tracing(
    app,
    engine,
    service_name: str = "riskcast-v3",
    service_version: str = "3.0.0",
    otlp_endpoint: Optional[str] = None,
    enable_console_exporter: bool = False
):
    """
    Setup OpenTelemetry tracing.
    
    Args:
        app: FastAPI application instance
        engine: SQLAlchemy engine instance
        service_name: Service name for traces
        service_version: Service version
        otlp_endpoint: OTLP endpoint URL (e.g., "http://localhost:4317")
        enable_console_exporter: Whether to enable console exporter for debugging
        
    Returns:
        Tracer instance
    """
    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry not available, tracing disabled")
        return trace.NoOpTracer()
    
    try:
        # Create resource with service information
        resource = Resource.create({
            "service.name": service_name,
            "service.version": service_version,
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add console exporter if enabled (for debugging)
        if enable_console_exporter:
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.info("OpenTelemetry console exporter enabled")
        
        # Add OTLP exporter if endpoint provided
        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                
                otlp_exporter = OTLPSpanExporter(
                    endpoint=otlp_endpoint,
                    insecure=True  # Use TLS in production (set insecure=False for production)
                )
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                logger.info(f"OpenTelemetry OTLP exporter configured: {otlp_endpoint}")
            except ImportError:
                logger.warning(
                    "OTLP exporter not available. Install with: pip install opentelemetry-exporter-otlp-proto-grpc"
                )
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Instrument FastAPI
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument FastAPI: {e}")
        
        # Instrument SQLAlchemy
        try:
            SQLAlchemyInstrumentor().instrument(engine=engine)
            logger.info("SQLAlchemy instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument SQLAlchemy: {e}")
        
        # Instrument requests library (for HTTP calls)
        try:
            RequestsInstrumentor().instrument()
            logger.info("Requests library instrumentation enabled")
        except Exception as e:
            logger.warning(f"Failed to instrument requests library: {e}")
        
        # Get tracer
        tracer = trace.get_tracer(__name__)
        logger.info("OpenTelemetry tracing initialized")
        
        return tracer
        
    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry tracing: {e}", exc_info=True)
        # Return a no-op tracer
        return trace.NoOpTracer()


def get_tracer(name: Optional[str] = None):
    """
    Get a tracer instance.
    
    Args:
        name: Tracer name (optional)
        
    Returns:
        Tracer instance
    """
    if not OPENTELEMETRY_AVAILABLE:
        return trace.NoOpTracer()
    return trace.get_tracer(name or __name__)


def create_span(name: str, attributes: Optional[dict] = None):
    """
    Create a span context manager.
    
    Usage:
        with create_span("operation_name", {"key": "value"}):
            # Your code here
    
    Args:
        name: Span name
        attributes: Optional span attributes
        
    Returns:
        Span context manager
    """
    tracer = get_tracer()
    span = tracer.start_as_current_span(name)
    
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
    
    return span
