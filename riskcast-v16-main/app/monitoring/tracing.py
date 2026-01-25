"""
Distributed Tracing Configuration

OpenTelemetry integration for distributed tracing.
"""

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat


def setup_tracing(
    service_name: str = "riskcast-api",
    otlp_endpoint: Optional[str] = None,
    environment: str = "production"
):
    """
    Initialize OpenTelemetry tracing.
    
    Args:
        service_name: Name of the service
        otlp_endpoint: OTLP collector endpoint
        environment: Deployment environment
    """
    # Get endpoint from env if not provided
    otlp_endpoint = otlp_endpoint or os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4317"
    )
    
    # Create resource with service info
    resource = Resource.create({
        SERVICE_NAME: service_name,
        "service.version": os.getenv("APP_VERSION", "1.0.0"),
        "deployment.environment": environment,
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True  # Use TLS in production
    )
    
    # Add batch processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    # Set up B3 propagation for compatibility with other systems
    set_global_textmap(B3MultiFormat())
    
    return provider


def instrument_app(app):
    """
    Instrument FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument HTTP clients
    HTTPXClientInstrumentor().instrument()


def instrument_database(engine):
    """
    Instrument SQLAlchemy database.
    
    Args:
        engine: SQLAlchemy engine
    """
    SQLAlchemyInstrumentor().instrument(
        engine=engine,
        enable_commenter=True
    )


def instrument_redis():
    """Instrument Redis client."""
    RedisInstrumentor().instrument()


def get_tracer(name: str = __name__):
    """Get a tracer instance."""
    return trace.get_tracer(name)


# Context manager for creating spans
class TracedOperation:
    """Context manager for tracing operations."""
    
    def __init__(self, name: str, attributes: Optional[dict] = None):
        self.name = name
        self.attributes = attributes or {}
        self.tracer = get_tracer()
        self.span = None
    
    def __enter__(self):
        self.span = self.tracer.start_span(self.name)
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.span.record_exception(exc_val)
            self.span.set_status(trace.Status(trace.StatusCode.ERROR))
        self.span.end()
        return False


# Decorator for tracing functions
def traced(name: Optional[str] = None, attributes: Optional[dict] = None):
    """Decorator to trace function execution."""
    def decorator(func):
        span_name = name or f"{func.__module__}.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            with TracedOperation(span_name, attributes):
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            with TracedOperation(span_name, attributes):
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
