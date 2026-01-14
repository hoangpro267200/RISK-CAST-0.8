# app/main.py
"""
RISKCAST Enterprise AI - FastAPI Application
Main entry point for the RISKCAST backend server
"""
import multiprocessing
import os
import importlib
import importlib.util
from pathlib import Path
from typing import Any, Dict

# Windows multiprocessing fix - MUST be at top level
multiprocessing.freeze_support()

# Load .env file FIRST before importing anything else
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[INFO] Loaded .env from: {env_file}")

# FastAPI imports
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, Response, JSONResponse  # type: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore

# Application routers
from app.api import router as api_router
from app.api.router import router as api_router_v60
from app.api_ai import router as ai_router
from app.routes.overview import router as overview_router
from app.routes.update_shipment_route_v33 import router as update_shipment_router
from app.routes.ai_endpoints_v33 import router as ai_endpoints_router
from app.core.services.risk_service import run_risk_engine_v14
from app.memory import memory_system

# Load app/api.py explicitly (there is also an app/api/ package)
_api_file = Path(__file__).parent / "api.py"
_api_spec = importlib.util.spec_from_file_location("api_file_module", _api_file)
_api_module = importlib.util.module_from_spec(_api_spec) if _api_spec and _api_spec.loader else None
if _api_module and _api_spec and _api_spec.loader:
    _api_spec.loader.exec_module(_api_module)
    LAST_RESULT = getattr(_api_module, "LAST_RESULT", None)
    build_riskcast_state_from_shipment = getattr(_api_module, "build_riskcast_state_from_shipment", lambda x: x)
else:
    LAST_RESULT = None
    def build_riskcast_state_from_shipment(x: Dict[str, Any]) -> Dict[str, Any]:
        return x

# Core modules
from app.core import build_helper
from app.core.templates import templates
from app.middleware.cache_headers import CacheHeadersMiddleware
from app.core.engine_state import get_last_result_v2

app = FastAPI(
    title="RISKCAST Enterprise AI",
    description="Enterprise Risk Analytics Engine with AI Adviser (Fuzzy AHP + MC + VaR/CVaR + Claude 3.5 Sonnet)",
    version="19.0.0"
)

# ============================
# MIDDLEWARE (Order matters - first added is outermost)
# ============================
# Request ID Middleware (outermost - generates request_id for tracing)
from app.middleware.request_id import RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)

# Error Handler v2 (catches all errors, uses StandardResponse)
# Uses StandardResponse and custom_exceptions for consistent error handling
from app.middleware.error_handler_v2 import ErrorHandlerMiddleware
app.add_middleware(ErrorHandlerMiddleware)

# Timeout Middleware (RC-C005): Prevents long-running requests
from app.middleware.timeout_middleware import TimeoutMiddleware
app.add_middleware(TimeoutMiddleware, default_timeout=30.0)

# Metrics Middleware (Phase 3): Prometheus metrics collection
from app.middleware.metrics_middleware import MetricsMiddleware
app.add_middleware(MetricsMiddleware)

# Rate Limiting Middleware (Phase 6 - Day 16): Prevents abuse
from app.middleware.rate_limiter import RateLimiterMiddleware
app.add_middleware(RateLimiterMiddleware)

# Security Headers Middleware
from app.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS Middleware (restricted origins)
# SECURITY: In production, restrict ALLOWED_ORIGINS to specific domains
# NEVER use "*" in production!
is_production = os.getenv("ENVIRONMENT", "development") == "production"
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")

if is_production:
    # Production: Require explicit ALLOWED_ORIGINS
    if not allowed_origins_env:
        raise ValueError(
            "ALLOWED_ORIGINS must be set in production! "
            "Set it in .env file with your actual domain(s)."
        )
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
    if not allowed_origins:
        raise ValueError("ALLOWED_ORIGINS cannot be empty in production!")
else:
    # Development: Default to localhost origins
    if allowed_origins_env:
        allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
    else:
        allowed_origins = [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "X-Request-ID"],
)

# Cache Headers Middleware (for production assets)
app.add_middleware(CacheHeadersMiddleware)

# Session Middleware (for storing shipment data between pages)
from starlette.middleware.sessions import SessionMiddleware  # type: ignore
# CRITICAL: Fail if SESSION_SECRET_KEY is not set in production
# This prevents using default/weak secrets
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError(
            "SESSION_SECRET_KEY environment variable is required in production. "
            "Set a strong random secret (32+ characters)."
        )
    else:
        # Development: Use a warning but allow fallback
        import warnings
        warnings.warn(
            "SESSION_SECRET_KEY not set. Using temporary development secret. "
            "Set SESSION_SECRET_KEY in .env for production.",
            UserWarning
        )
        SESSION_SECRET_KEY = "riskcast-dev-secret-change-in-production"

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

# ============================
# TEMPLATES PATH - Use shared instance
# ============================
BASE_DIR = Path(__file__).resolve().parent  # nằm trong /app

# ============================
# TEMPLATE CONTEXT (Build Helper)
# ============================
def get_template_context():
    """Get global template context variables"""
    from app.core import build_helper
    return {
        "cdn_url": build_helper.get_cdn_url(),
        "build_version": build_helper.get_build_version(),
        "get_js_bundle": build_helper.get_js_bundle,
        "get_css_bundle": build_helper.get_css_bundle,
        "is_production": os.getenv("ENVIRONMENT", "development") == "production"
    }

# ============================
# STATIC FILES
# ============================
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ============================
# DIST (PRODUCTION BUNDLES)
# ============================
# CRITICAL: Mount /assets BEFORE any routes to ensure static files are served correctly
# FastAPI matches mounts BEFORE routes, so this order is correct
DIST_DIR = BASE_DIR.parent / "dist"
ASSETS_DIR = DIST_DIR / "assets" if DIST_DIR.exists() else None

if ASSETS_DIR and ASSETS_DIR.exists():
    # Mount /assets FIRST - before /dist and before any routes
    # html=False ensures it doesn't try to serve index.html for missing files
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR), html=False), name="assets")
    print(f"[INFO] Mounted /assets from {ASSETS_DIR}")
    print(f"[INFO] Assets directory contains {len(list(ASSETS_DIR.iterdir()))} files")
else:
    print(f"[WARNING] ASSETS_DIR not found! DIST_DIR: {DIST_DIR}, exists: {DIST_DIR.exists() if DIST_DIR else False}")

if DIST_DIR.exists():
    app.mount("/dist", StaticFiles(directory=str(DIST_DIR)), name="dist")

# ============================
# REACT APP STATIC FILES (for dev mode)
# ============================
# NOTE: TypeScript/TSX files should be served by Vite dev server (port 3000), not FastAPI
# FastAPI cannot serve .tsx files with correct MIME types for ES modules
# In dev mode, use Vite dev server. In production, use built dist/ folder.
# SRC_DIR = BASE_DIR.parent / "src"
# if SRC_DIR.exists():
#     app.mount("/src", StaticFiles(directory=str(SRC_DIR)), name="src")

# Mount node_modules for Vite client (dev mode only)
NODE_MODULES_DIR = BASE_DIR.parent / "node_modules"
if NODE_MODULES_DIR.exists():
    try:
        app.mount("/node_modules", StaticFiles(directory=str(NODE_MODULES_DIR)), name="node_modules")
    except Exception:
        pass  # Ignore if already mounted

# ============================
# HANDLE BROWSER REQUESTS (Ignore 404 for common browser requests)
# ============================
@app.get("/.well-known/{path:path}")
async def well_known_handler(path: str):
    """Handle browser DevTools requests - return 204 No Content to avoid 404 logs"""
    return Response(status_code=204)

@app.get("/favicon.ico")
async def favicon_handler():
    """Handle favicon requests - return 204 No Content to avoid 404 logs"""
    return Response(status_code=204)

# ============================
# PAGES
# ============================

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Home page - RISKCAST FutureOS Landing Page"""
    context = {"request": request}
    context.update(get_template_context())
    return templates.TemplateResponse("home.html", context)

@app.get("/input")
async def input_redirect():
    return RedirectResponse(url="/input_v20")

@app.get("/input_v19", response_class=HTMLResponse)
async def input_v19(request: Request):
    """Input page v19 - VisionOS Edition"""
    context = {"request": request}
    context.update(get_template_context())
    return templates.TemplateResponse("input/input_v19.html", context)

@app.get("/input_v20", response_class=HTMLResponse)
async def input_v20(request: Request):
    """Input page v20 - Premium VisionOS Edition with Luxurious Glow"""
    context = {"request": request}
    context.update(get_template_context())
    return templates.TemplateResponse("input/input_v20.html", context)

@app.get("/input_modules_v30", response_class=HTMLResponse)
async def input_modules_v30(request: Request):
    """Modules selection page v30 - VisionOS Edition"""
    context = {"request": request}
    context.update(get_template_context())
    return templates.TemplateResponse("input_modules_v30.html", context)


@app.get("/overview")
async def overview_redirect():
    """
    Redirect legacy /overview to /summary to remove dependency on deleted template.
    """
    return RedirectResponse(url="/summary")

@app.post("/input_v20/submit")
async def input_v20_submit(request: Request):
    """
    Handle input form submission → normalize payload → store RISKCAST_STATE in session → redirect to overview.
    """
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
        # cargo_value: check multiple field names (cargo_value, insuranceValue, shipment_value)
        "cargo_value": _to_float("cargo_value", 0.0) or _to_float("insuranceValue", 0.0) or _to_float("shipment_value", 0.0),
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

    # Persist to session + memory for downstream pages
    if hasattr(request, "session"):
        request.session["shipment_state"] = shipment_payload
        request.session["RISKCAST_STATE"] = build_riskcast_state_from_shipment(shipment_payload)
    memory_system.set("latest_shipment", shipment_payload)

    # Redirect to latest Overview (v36 IBM-style). Keep backward compatibility by
    # using the existing /overview endpoint which now serves the new UI.
    return RedirectResponse(url="/overview", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page - Shipment Tracking & Management"""
    context = {"request": request}
    context.update(get_template_context())
    return templates.TemplateResponse("dashboard.html", context)

@app.get("/summary", response_class=HTMLResponse)
async def summary_page(request: Request):
    """Summary page - Redirect to new Shipment Summary page."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/shipments/summary", status_code=303)

# IMPORTANT: /results/data must be defined BEFORE /results to avoid route conflicts
# CRITICAL: This route uses exact match "/results/data" - will NOT match /assets/* or /results/*
# This route will ONLY match the exact path "/results/data", not "/results/data/anything"
@app.get("/results/data", tags=["results"])
async def get_results_data():
    """
    Provide a structured JSON payload for Results page.
    
    ARCHITECTURE: ENGINE-FIRST
    - Priority 1: Return LAST_RESULT_V2 (from Engine v2 via /api/v1/risk/v2/analyze)
    - Priority 2: Fall back to LAST_RESULT (legacy, from old /api/analyze endpoint)
    - Priority 3: Return empty dict (frontend will handle empty state)
    
    CRITICAL: This endpoint MUST return data that has passed through the engine.
    Results page depends on this for ENGINE-FIRST compliance.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("GET /results/data endpoint called")
    
    try:
        # Priority 1: Engine v2 result (authoritative)
        v2_result = get_last_result_v2()
        if v2_result and isinstance(v2_result, dict) and len(v2_result) > 0:
            logger.info(f"Returning LAST_RESULT_V2 (keys: {list(v2_result.keys())[:5]}...)")
            return v2_result  # FastAPI automatically converts dict to JSON
        
        # Priority 2: Legacy result (for backward compatibility)
        if LAST_RESULT and isinstance(LAST_RESULT, dict) and len(LAST_RESULT) > 0:
            logger.info("Returning LAST_RESULT (legacy)")
            return LAST_RESULT
    except Exception as e:
        # Log error but continue to fallback
        logger.warning(f"Error in get_results_data: {str(e)}")
        import traceback
        logger.warning(traceback.format_exc())
    
    # Priority 3: Return empty dict - frontend will handle empty state
    logger.info("Returning empty dict (no data available)")
    return {}

@app.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    """Results page - React app for displaying risk analysis results."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("GET /results endpoint called")
    
    # Serve the built React app from dist/index.html
    dist_index = BASE_DIR.parent / "dist" / "index.html"
    if dist_index.exists():
        try:
            # Read and return the HTML file
            with open(dist_index, 'r', encoding='utf-8') as f:
                html_content = f.read()
            logger.info(f"Serving dist/index.html from {dist_index}")
            return HTMLResponse(content=html_content)
        except Exception as e:
            logger.error(f"Error reading dist/index.html: {e}")
            # Fall through to fallback
    
    # Fallback: return a simple HTML page with instructions
    # Production build is required - dist/index.html must exist
    logger.warning("dist/index.html not found - serving fallback HTML with instructions")
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>RISKCAST Results - Build Required</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0f172a;
                color: #e2e8f0;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                padding: 2rem;
            }
            .container {
                max-width: 600px;
                background: #1e293b;
                border-radius: 8px;
                padding: 2rem;
                border: 1px solid #334155;
            }
            h1 {
                color: #fbbf24;
                margin-top: 0;
            }
            code {
                background: #0f172a;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
            }
            .step {
                margin: 1.5rem 0;
                padding: 1rem;
                background: #0f172a;
                border-radius: 4px;
                border-left: 3px solid #3b82f6;
            }
            .step-title {
                font-weight: 600;
                color: #60a5fa;
                margin-bottom: 0.5rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚠️ Production Build Required</h1>
            <p>The Results page requires a production build to be served.</p>
            
            <div class="step">
                <div class="step-title">Step 1: Install terser (if needed)</div>
                <code>npm install --save-dev terser</code>
            </div>
            
            <div class="step">
                <div class="step-title">Step 2: Build the React app</div>
                <code>npm run build</code>
            </div>
            
            <div class="step">
                <div class="step-title">Step 3: Restart FastAPI server</div>
                <p>After building, restart your FastAPI server and refresh this page.</p>
            </div>
            
            <p style="margin-top: 2rem; color: #94a3b8; font-size: 0.9em;">
                <strong>Note:</strong> The build will create a <code>dist/</code> folder with the compiled React app.
            </p>
        </div>
    </body>
    </html>
    """)

# ============================
# API ROUTES
# ============================

# Prometheus Metrics Endpoint (Phase 3 - Observability)
from app.middleware.metrics_middleware import get_metrics_endpoint
@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics_endpoint()()

# Health Check Endpoint (for monitoring)
@app.get("/health", tags=["monitoring"])
async def health():
    """
    Health check endpoint for monitoring systems.
    
    Returns:
        - 200: System is healthy
        - 503: System is unhealthy (if checks fail)
    """
    health_status = {
        "status": "healthy",
        "version": "v16",
        "checks": {
            "api": "ok",
            "database": "ok"  # TODO: Add actual database health check
        }
    }
    
    # TODO: Add actual health checks
    # - Database connectivity
    # - External API availability (Anthropic)
    # - Disk space
    # - Memory usage
    
    return health_status

# Include new v1 API router
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(api_router_v60, tags=["api-v60"])

# Include AI Adviser router
app.include_router(ai_router, prefix="/api/ai", tags=["AI Adviser"])

# Include Overview router
app.include_router(overview_router)

# Include Shipment Summary router (New Vanilla JS implementation)
from app.routes.shipment_summary import router as shipment_summary_router
app.include_router(shipment_summary_router)

# Include Overview v33 routes (FutureOS Edition)
app.include_router(update_shipment_router)  # PATCH /api/update_shipment
app.include_router(ai_endpoints_router)  # POST /api/ai/*

# v34.4/v34.5 routes removed in favor of basic overview
api_py_path = Path(__file__).parent / "api.py"
if api_py_path.exists():
    spec = importlib.util.spec_from_file_location("legacy_api", api_py_path)
    if spec is not None and spec.loader is not None:
        legacy_api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(legacy_api)
        app.include_router(legacy_api.router, prefix="/api", tags=["legacy"])
