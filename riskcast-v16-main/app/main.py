"""
RISKCAST V3 - Main FastAPI Application
Modular Monolith Architecture
"""
from fastapi import FastAPI, Request
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


# Custom OpenAPI schema generation with error handling
def custom_openapi():
    """Generate OpenAPI schema with graceful error handling."""
    if app.openapi_schema:
        return app.openapi_schema
    
    try:
        from fastapi.openapi.utils import get_openapi
        openapi_schema = get_openapi(
            title=settings.API_TITLE,
            version=settings.APP_VERSION,
            description=settings.API_DESCRIPTION,
            routes=app.routes,
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    except Exception as e:
        logger.warning(f"Failed to generate full OpenAPI schema: {e}")
        # Return a minimal but valid schema
        app.openapi_schema = {
            "openapi": "3.1.0",
            "info": {
                "title": settings.API_TITLE,
                "version": settings.APP_VERSION,
                "description": "RISKCAST API - Schema generation encountered an error. Use /api/v3/* endpoints directly."
            },
            "paths": {
                "/": {
                    "get": {
                        "summary": "Root",
                        "operationId": "root__get",
                        "responses": {"200": {"description": "API info"}}
                    }
                },
                "/health": {
                    "get": {
                        "summary": "Health Check",
                        "operationId": "health_check_health_get",
                        "responses": {"200": {"description": "Health status"}}
                    }
                }
            },
            "servers": [
                {"url": "http://localhost:8000", "description": "Local development"}
            ]
        }
        return app.openapi_schema

app.openapi = custom_openapi

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

# Include API v2 routes
try:
    from app.api.v2 import get_v2_router
    v2_router = get_v2_router()
    app.include_router(v2_router, prefix="/api/v2", tags=["API v2"])
    logger.info("API v2 routes loaded at /api/v2")
except ImportError as e:
    logger.warning(f"API v2 routes not loaded: {e}")
except Exception as e:
    logger.warning(f"API v2 routes error: {e}")

# Include API v1 routes (risk analysis, scenarios, etc.)
try:
    from app.api.v1.risk_routes import router as risk_v1_router
    app.include_router(risk_v1_router, prefix="/api/v1", tags=["API v1 - Risk"])
    logger.info("API v1 Risk routes loaded at /api/v1")
except ImportError as e:
    logger.warning(f"API v1 Risk routes not loaded: {e}")

# Include API v1 analyze routes
try:
    from app.api.v1.analyze import router as analyze_router
    app.include_router(analyze_router, prefix="/api/v1", tags=["API v1 - Analyze"])
    logger.info("API v1 Analyze routes loaded")
except ImportError as e:
    logger.warning(f"API v1 Analyze routes not loaded: {e}")

# Include AI Advisor routes
try:
    from app.api.v1.ai_advisor_routes import router as ai_advisor_router
    app.include_router(ai_advisor_router, prefix="/api/v1", tags=["API v1 - AI Advisor"])
    logger.info("AI Advisor routes loaded at /api/v1/advisor")
except ImportError as e:
    logger.warning(f"AI Advisor routes not loaded: {e}")
except Exception as e:
    logger.warning(f"AI Advisor routes error: {e}")

# Include Authentication routes
try:
    from app.routers.auth import router as auth_router, account_router, api_key_router, admin_router
    app.include_router(auth_router, tags=["Authentication"])
    app.include_router(account_router, tags=["Account"])
    app.include_router(api_key_router, tags=["API Keys"])
    app.include_router(admin_router, tags=["Admin"])
    logger.info("Auth routes loaded at /api/auth, /api/account, /api/auth/keys, /api/admin")
except ImportError as e:
    logger.warning(f"Auth routes not loaded: {e}")
except Exception as e:
    logger.warning(f"Auth routes error: {e}")

# Include legacy API routes (for form submission)
try:
    import app.api as api_module
    if hasattr(api_module, 'router'):
        app.include_router(api_module.router, prefix="/api", tags=["API - Legacy"])
        logger.info("Legacy API routes loaded")
    else:
        logger.warning("Legacy API module has no router")
except ImportError as e:
    logger.warning(f"Legacy API routes not loaded: {e}")
except Exception as e:
    logger.warning(f"Legacy API routes error: {e}")

# Include UI/Frontend routes (Overview, Summary, Input pages)
try:
    from app.routes.overview import router as overview_router
    app.include_router(overview_router, tags=["UI - Overview"])
    logger.info("Overview routes loaded")
except ImportError as e:
    logger.warning(f"Overview routes not loaded: {e}")

try:
    from app.routes.shipment_summary import router as summary_router
    app.include_router(summary_router, tags=["UI - Summary"])
    logger.info("Summary routes loaded")
except ImportError as e:
    logger.warning(f"Summary routes not loaded: {e}")

try:
    from app.routes.ai_endpoints_v33 import router as ai_router
    app.include_router(ai_router, tags=["AI Endpoints"])
    logger.info("AI endpoints loaded")
except ImportError as e:
    logger.warning(f"AI endpoints not loaded: {e}")

# Mount static files for CSS/JS/Images
try:
    from fastapi.staticfiles import StaticFiles
    from pathlib import Path
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        logger.info(f"Static files mounted at /static from {static_path}")
except Exception as e:
    logger.warning(f"Static files not mounted: {e}")

# GraphQL API (Strawberry)
try:
    from app.graphql.router import graphql_app
    app.include_router(graphql_app, prefix="/graphql", tags=["GraphQL"])
    logger.info("GraphQL endpoint available at /graphql")
except ImportError as e:
    logger.warning("GraphQL not loaded: %s. Install strawberry-graphql[fastapi].", e)

# Setup documentation
# Disabled custom OpenAPI due to Pydantic serialization issues
# The default FastAPI docs work fine at /docs
# try:
#     from app.docs.openapi_customization import setup_docs
#     setup_docs(app)
# except ImportError:
#     pass

# ============================
# UI ROUTES - Home, Input, Summary, Results
# ============================
from fastapi.responses import HTMLResponse, RedirectResponse

# Import templates
try:
    from app.core.templates import templates
    TEMPLATES_AVAILABLE = True
except ImportError:
    TEMPLATES_AVAILABLE = False
    logger.warning("Templates not available - UI routes disabled")

def get_template_context():
    """Get common template context"""
    import os
    return {
        "CESIUM_TOKEN": os.getenv("CESIUM_ION_TOKEN") or os.getenv("CESIUM_TOKEN") or "",
        "API_BASE_URL": os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
    }

def get_auth_context(request: Request):
    """Get authentication context for templates"""
    import os
    from sqlalchemy.orm import Session
    
    auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    is_authenticated = False
    user = None
    user_name = None
    user_email = None
    
    if auth_enabled:
        try:
            from app.dependencies.auth import get_current_user
            from app.database import get_db
            # Try to get current user from session cookie
            session_token = request.cookies.get("session_token")
            if session_token:
                from app.models.auth import Session as SessionModel, AuthUser as User
                from app.database import SessionLocal
                db = SessionLocal()
                try:
                    token_hash = SessionModel.hash_token(session_token)
                    session = db.query(SessionModel).filter(
                        SessionModel.token_hash == token_hash
                    ).first()
                    if session and session.is_valid():
                        user = db.query(User).filter(User.id == session.user_id).first()
                        if user and user.is_active:
                            is_authenticated = True
                            user_name = user.name
                            user_email = user.email
                finally:
                    db.close()
        except Exception as e:
            logger.debug(f"Auth context error: {e}")
    
    return {
        "auth_enabled": auth_enabled,
        "is_authenticated": is_authenticated,
        "user": user,
        "user_name": user_name,
        "user_email": user_email,
    }

# Root/Home page
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Home page - RISKCAST FutureOS Landing Page"""
    if TEMPLATES_AVAILABLE:
        try:
            context = {"request": request}
            context.update(get_template_context())
            context.update(get_auth_context(request))
            return templates.TemplateResponse("home.html", context)
        except Exception as e:
            logger.warning(f"Template error: {e}")
    # Fallback to JSON response
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else None,
        "api": settings.API_V3_PREFIX,
        "graphql": "/graphql",
        "health": "/health",
        "ui": {
            "input": "/input_v20",
            "summary": "/summary",
            "results": "/results"
        }
    }

@app.get("/input")
async def input_redirect():
    """Redirect to main input page"""
    return RedirectResponse(url="/input_v20")

# ============================
# AUTH PAGES - Login, Signup
# ============================
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    from fastapi.responses import JSONResponse
    if TEMPLATES_AVAILABLE:
        try:
            context = {"request": request}
            context.update(get_template_context())
            return templates.TemplateResponse("auth/login.html", context)
        except Exception as e:
            logger.warning(f"Template error for /login: {e}")
            return JSONResponse({"error": f"Template error: {e}"})
    return JSONResponse({"error": "Template not available"})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup/Register page"""
    from fastapi.responses import JSONResponse
    if TEMPLATES_AVAILABLE:
        try:
            context = {"request": request}
            context.update(get_template_context())
            return templates.TemplateResponse("auth/signup.html", context)
        except Exception as e:
            logger.warning(f"Template error for /signup: {e}")
            return JSONResponse({"error": f"Template error: {e}"})
    return JSONResponse({"error": "Template not available"})

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Forgot password page - redirect to login for now"""
    return RedirectResponse(url="/login")

@app.get("/input_v19", response_class=HTMLResponse)
async def input_v19(request: Request):
    """Input page v19 - VisionOS Edition"""
    if TEMPLATES_AVAILABLE:
        try:
            context = {"request": request}
            context.update(get_template_context())
            return templates.TemplateResponse("input/input_v19.html", context)
        except Exception as e:
            logger.warning(f"Template error: {e}")
            return RedirectResponse(url="/input_v20")
    return RedirectResponse(url="/docs")

@app.get("/input_v20", response_class=HTMLResponse)
async def input_v20(request: Request):
    """Input page v20 - Premium VisionOS Edition"""
    from fastapi.responses import JSONResponse
    if TEMPLATES_AVAILABLE:
        try:
            context = {"request": request}
            context.update(get_template_context())
            context.update(get_auth_context(request))
            return templates.TemplateResponse("input/input_v20.html", context)
        except Exception as e:
            logger.warning(f"Template error for /input_v20: {e}")
            return JSONResponse({"error": f"Template error: {e}", "fallback": "/docs"})
    return JSONResponse({"error": "Template not available", "fallback": "/docs"})

@app.get("/input_modules_v30", response_class=HTMLResponse)
async def input_modules_v30(request: Request):
    """Modules selection page v30"""
    if TEMPLATES_AVAILABLE:
        try:
            context = {"request": request}
            context.update(get_template_context())
            return templates.TemplateResponse("input_modules_v30.html", context)
        except Exception as e:
            logger.warning(f"Template error: {e}")
    return RedirectResponse(url="/input_v20")

@app.post("/input_v20/submit")
async def input_v20_submit(request: Request):
    """
    Handle input form submission → normalize payload → store RISKCAST_STATE in session → redirect to overview.
    """
    from typing import Dict, Any
    
    try:
        form_data = await request.form()
    except Exception:
        form_data = {}

    # Allow JSON payload fallback (e.g., fetch submission)
    if not form_data:
        try:
            form_data = await request.json()
        except Exception:
            form_data = {}

    def _get(key: str, default: str = "") -> str:
        val = form_data.get(key)
        return str(val).strip() if val is not None else default

    def _to_float(key: str, default: float = 0.0) -> float:
        try:
            return float(form_data.get(key, default) or default)
        except (TypeError, ValueError):
            return default

    # Build a shipment-like payload that matches api.run_analysis expectations
    shipment_payload: Dict[str, Any] = {
        "transport_mode": _get("transport_mode", "ocean_fcl"),
        "cargo_type": _get("cargo_type", "general"),
        "route": _get("route") or f"{_get('pol_code', 'VNSGN')}_{_get('pod_code', 'CNSHA')}",
        "incoterm": _get("incoterm", "FOB"),
        "container": _get("container", "40HC"),
        "packaging": _get("packaging", "palletized"),
        "priority": _get("priority", "speed"),
        "packages": int(form_data.get("packages", 0) or 0),
        "etd": _get("etd"),
        "eta": _get("eta"),
        "transit_time": _to_float("transit_time", 0.0),
        "cargo_value": _to_float("cargo_value", 0.0),
        "distance": _to_float("distance", 0.0),
        "route_type": _get("route_type"),
        "carrier_rating": _to_float("carrier_rating", 0.0),
        "weather_risk": _to_float("weather_risk", 0.0),
        "port_risk": _to_float("port_risk", 0.0),
        "container_match": _to_float("container_match", 0.0),
        "shipment_value": _to_float("shipment_value", 0.0),
        # Ports
        "pol_code": _get("pol_code", _get("origin", "VNSGN")),
        "pod_code": _get("pod_code", _get("destination", "CNSHA")),
        # Parties
        "shipper": _get("shipper"),
        "consignee": _get("consignee"),
        "forwarder": _get("forwarder"),
        # Risk placeholders
        "risk_score": _to_float("risk_score", 7.2),
        "risk_level": _get("risk_level", "Medium"),
    }

    # Persist to memory for downstream pages
    try:
        from app.memory import memory_system
        from app.api import build_riskcast_state_from_shipment
        memory_system.set("latest_shipment", shipment_payload)
        # Also build and store RISKCAST_STATE
        riskcast_state = build_riskcast_state_from_shipment(shipment_payload)
        memory_system.set("RISKCAST_STATE", riskcast_state)
    except Exception as e:
        logger.warning(f"Failed to store shipment in memory: {e}")

    # Redirect to overview/summary page
    return RedirectResponse(url="/summary", status_code=303)

@app.get("/summary", response_class=HTMLResponse)
async def summary_page(request: Request):
    """Summary page - Redirect to React frontend (port 3000)"""
    # In development, always redirect to React dev server on port 3000
    # React server should be started with: npm run dev
    return RedirectResponse(url="http://localhost:3000/summary", status_code=302)

# NOTE: /results/data MUST be defined BEFORE /results to ensure proper routing
@app.get("/results/data")
async def results_data_api():
    """
    API endpoint to get analysis results for React frontend.
    
    Returns the latest Engine v2 analysis result from shared backend state.
    This is called by the React Results page to fetch data.
    """
    from fastapi.responses import JSONResponse
    try:
        from app.core.engine_state import get_last_result_v2
        
        v2_result = get_last_result_v2()
        
        if not v2_result:
            return JSONResponse(
                status_code=404,
                content={"error": "No analysis results available", "message": "Please run analysis from the Summary page first."}
            )
        
        # Return the result wrapped in standard format
        return JSONResponse(
            content={
                "success": True,
                "data": v2_result
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching results data: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

@app.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    """Results page - Redirect to React frontend (port 3000)"""
    # In development, always redirect to React dev server on port 3000
    return RedirectResponse(url="http://localhost:3000/results", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page"""
    from fastapi.responses import JSONResponse
    if TEMPLATES_AVAILABLE:
        try:
            context = {"request": request}
            context.update(get_template_context())
            context.update(get_auth_context(request))
            return templates.TemplateResponse("dashboard.html", context)
        except Exception as e:
            logger.warning(f"Template error for /dashboard: {e}")
            return JSONResponse({"error": f"Template error: {e}", "fallback": "/docs"})
    return JSONResponse({"error": "Template not available", "fallback": "/docs"})

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Favicon - prevent 404 error in browser console
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Return empty response for favicon to prevent 404"""
    from fastapi.responses import Response
    # Return a 1x1 transparent PNG
    return Response(
        content=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82',
        media_type="image/png"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
