"""
RISKCAST V3 - Main FastAPI Application
Modular Monolith Architecture
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import init_db
from app.api.v3 import router as v3_router
from app.modules.observability import (
    configure_logging,
    ObservabilityMiddleware,
    setup_tracing
)

# Configure structured logging
configure_logging(
    log_level=settings.LOG_LEVEL,
    json_output=settings.ENVIRONMENT == "production"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize database (verify connection only)
    try:
        init_db()
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.warning("Run 'alembic upgrade head' to create/update database tables")
        if settings.ENVIRONMENT == "production":
            raise
    
    # Initialize OpenTelemetry tracing
    if settings.ENABLE_OPENTELEMETRY:
        from app.database import engine
        setup_tracing(
            app=app,
            engine=engine,
            service_name=settings.APP_NAME.lower().replace(" ", "-"),
            service_version=settings.APP_VERSION,
            otlp_endpoint=getattr(settings, 'OTEL_EXPORTER_OTLP_ENDPOINT', None),
            enable_console_exporter=settings.DEBUG
        )
        logger.info("OpenTelemetry tracing initialized")
    
    # Prometheus metrics are exposed via /metrics endpoint
    # (if ENABLE_PROMETHEUS is True, add Prometheus exporter)
    if settings.ENABLE_PROMETHEUS:
        try:
            from prometheus_client import make_asgi_app
            metrics_app = make_asgi_app()
            app.mount("/metrics", metrics_app)
            logger.info("Prometheus metrics endpoint available at /metrics")
        except ImportError:
            logger.warning("Prometheus client not installed. Install with: pip install prometheus-client")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Observability middleware (must be first to capture all requests)
app.add_middleware(ObservabilityMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(v3_router, prefix=settings.API_V3_PREFIX, tags=["API v3"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else None,
        "api": settings.API_V3_PREFIX,
        "health": "/health"
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
