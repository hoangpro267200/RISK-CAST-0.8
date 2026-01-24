"""
Observability Service
Logging, metrics, and tracing setup
"""
import logging
import structlog
from typing import Optional

from app.config import settings


def init_telemetry():
    """Initialize OpenTelemetry"""
    if not settings.ENABLE_OPENTELEMETRY:
        return
    
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        
        # Set up tracer provider
        resource = Resource.create({"service.name": settings.APP_NAME})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        
        # Add OTLP exporter if endpoint provided
        if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT))
            provider.add_span_processor(processor)
        
        logging.info("OpenTelemetry initialized")
    except ImportError:
        logging.warning("OpenTelemetry packages not installed")


def init_prometheus():
    """Initialize Prometheus metrics"""
    if not settings.ENABLE_PROMETHEUS:
        return
    
    try:
        from prometheus_client import Counter, Histogram, Gauge
        
        # Define metrics (will be used by middleware)
        request_counter = Counter(
            'riskcast_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        request_duration = Histogram(
            'riskcast_http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        
        logging.info("Prometheus metrics initialized")
    except ImportError:
        logging.warning("Prometheus client not installed")


def setup_structured_logging():
    """Setup structured logging with structlog"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
