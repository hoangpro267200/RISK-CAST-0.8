"""
Example: Integrating Monitoring into FastAPI Application

Shows how to integrate Prometheus metrics and OpenTelemetry tracing.
"""

from fastapi import FastAPI, Request
from fastapi.responses import Response
import os

# Import monitoring components
from app.monitoring import (
    setup_tracing,
    instrument_app,
    instrument_database,
    instrument_redis,
    metrics_endpoint,
    setup_app_info,
    track_request_metrics,
    REQUEST_COUNT,
    ACTIVE_POLICIES
)


def create_app() -> FastAPI:
    """Create and configure FastAPI application with monitoring."""
    
    app = FastAPI(
        title="RiskCast API",
        version="1.0.0",
        description="Marine Cargo Insurance Platform"
    )
    
    # =============================================================================
    # Initialize Tracing
    # =============================================================================
    
    tracing_enabled = os.getenv("ENABLE_TRACING", "true").lower() == "true"
    
    if tracing_enabled:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo:4317")
        environment = os.getenv("ENVIRONMENT", "production")
        
        # Setup OpenTelemetry
        setup_tracing(
            service_name="riskcast-api",
            otlp_endpoint=otlp_endpoint,
            environment=environment
        )
        
        # Instrument FastAPI
        instrument_app(app)
        
        # Instrument Redis (if initialized)
        try:
            instrument_redis()
        except Exception:
            pass  # Redis not configured
    
    # =============================================================================
    # Initialize Metrics
    # =============================================================================
    
    app_version = os.getenv("APP_VERSION", "1.0.0")
    environment = os.getenv("ENVIRONMENT", "production")
    
    setup_app_info(version=app_version, environment=environment)
    
    # =============================================================================
    # Metrics Endpoint
    # =============================================================================
    
    @app.get("/metrics", include_in_schema=False)
    async def get_metrics():
        """Prometheus metrics endpoint."""
        data, content_type = await metrics_endpoint()
        return Response(content=data, media_type=content_type)
    
    # =============================================================================
    # Middleware for Request Tracking
    # =============================================================================
    
    @app.middleware("http")
    async def track_requests(request: Request, call_next):
        """Middleware to track all HTTP requests."""
        import time
        
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        
        return response
    
    # =============================================================================
    # Health Checks
    # =============================================================================
    
    @app.get("/health/live")
    async def liveness():
        """Liveness probe."""
        return {"status": "alive"}
    
    @app.get("/health/ready")
    async def readiness():
        """Readiness probe."""
        # Check database, Redis, etc.
        return {"status": "ready"}
    
    @app.get("/health/startup")
    async def startup():
        """Startup probe."""
        return {"status": "started"}
    
    return app


# =============================================================================
# Example: Using Metrics in Endpoints
# =============================================================================

from fastapi import APIRouter
from app.monitoring import QUOTE_COUNT, QUOTE_PREMIUM, traced

router = APIRouter()


@router.post("/quotes/request")
@track_request_metrics("/quotes/request")
@traced("create_quote")
async def create_quote(quote_request: dict):
    """
    Create a new quote.
    
    This endpoint is automatically instrumented for:
    - Request metrics (count, latency)
    - Distributed tracing
    """
    # Business logic here
    quote = await process_quote(quote_request)
    
    # Record business metrics
    QUOTE_COUNT.labels(
        status="PENDING",
        coverage_type=quote.get("coverage_type", "STANDARD")
    ).inc()
    
    QUOTE_PREMIUM.observe(quote.get("premium_usd", 0))
    
    return quote


async def process_quote(quote_request: dict) -> dict:
    """Process quote (example)."""
    return {
        "quote_id": "Q-123",
        "premium_usd": 1500.00,
        "coverage_type": "STANDARD",
        "status": "PENDING"
    }


# =============================================================================
# Example: Instrumenting Database
# =============================================================================

from sqlalchemy import create_engine
from app.monitoring import instrument_database

def get_database_engine():
    """Create instrumented database engine."""
    engine = create_engine(
        os.getenv("DATABASE_URL"),
        pool_size=20,
        max_overflow=10
    )
    
    # Instrument for tracing
    instrument_database(engine)
    
    return engine


# =============================================================================
# Example: Tracking External Requests
# =============================================================================

import httpx
from app.monitoring import track_external_request, EXTERNAL_REQUEST_COUNT

class WeatherService:
    """External weather service client."""
    
    @track_external_request("tomorrow-io")
    async def get_weather(self, location: dict) -> dict:
        """Get weather data (automatically tracked)."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.tomorrow.io/v4/weather/realtime",
                params={"location": f"{location['lat']},{location['lon']}"}
            )
            return response.json()


# =============================================================================
# Example: Custom Traced Operations
# =============================================================================

from app.monitoring import TracedOperation

async def calculate_risk_score(data: dict) -> float:
    """Calculate risk score with tracing."""
    
    with TracedOperation("calculate_risk_score", {"cargo_type": data.get("cargo_type")}):
        # Complex calculation
        base_score = data.get("base_risk", 0.5)
        
        with TracedOperation("fetch_historical_data"):
            historical = await fetch_historical_data()
        
        with TracedOperation("apply_ml_model"):
            ml_score = await apply_ml_model(data)
        
        final_score = (base_score + ml_score) / 2
        
        return final_score


async def fetch_historical_data():
    """Fetch historical data (example)."""
    return {"avg_loss_ratio": 0.3}


async def apply_ml_model(data: dict):
    """Apply ML model (example)."""
    return 0.6
