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
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, Response  # type: ignore
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

app = FastAPI(
    title="RISKCAST Enterprise AI",
    description="Enterprise Risk Analytics Engine with AI Adviser (Fuzzy AHP + MC + VaR/CVaR + Claude 3.5 Sonnet)",
    version="19.0.0"
)

# ============================
# MIDDLEWARE (Order matters - first added is outermost)
# ============================
# Error Handler (outermost - catches all errors)
from app.middleware.error_handler import ErrorHandlerMiddleware
app.add_middleware(ErrorHandlerMiddleware)

# Security Headers Middleware
from app.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS Middleware (restricted origins)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Cache Headers Middleware (for production assets)
app.add_middleware(CacheHeadersMiddleware)

# Session Middleware (for storing shipment data between pages)
from starlette.middleware.sessions import SessionMiddleware  # type: ignore
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "riskcast-session-secret-key-change-in-production"))

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
# ENGINE-FIRST ARCHITECTURE: Shared Backend State for v2 Results
# ============================
# CRITICAL: This is the SINGLE SOURCE OF TRUTH for ResultsOS v4000
# Results page MUST always render data that has passed through the CORE RISK ENGINE
# Storage (localStorage/sessionStorage) is ONLY a fallback for legacy support
# ============================
from app.core.engine_state import get_last_result_v2

# ============================
# RESULTS OS v4000 DATA SOURCE
# ============================
def compute_results():
    """
    Provide a structured JSON payload for ResultsOS v4000.
    
    ARCHITECTURE: ENGINE-FIRST
    - Priority 1: Return LAST_RESULT_V2 (from Engine v2 via /api/v1/risk/v2/analyze)
    - Priority 2: Fall back to LAST_RESULT (legacy, from old /api/analyze endpoint)
    - Priority 3: Return demo data (only if no analysis has been run)
    
    CRITICAL: This endpoint MUST return data that has passed through the engine.
    Results page depends on this for ENGINE-FIRST compliance.
    """
    # Priority 1: Engine v2 result (authoritative)
    v2_result = get_last_result_v2()
    if v2_result:
        return v2_result
    
    # Priority 2: Legacy result (for backward compatibility)
    if LAST_RESULT:
        return LAST_RESULT

    # Priority 3: Demo payload (only if no analysis has been run)
    return {
        "shipment": {
            "id": "RC-SGN-LAX-2024-0012",
            "origin": {"code": "VNSGN", "name": "Ho Chi Minh City"},
            "destination": {"code": "USLAX", "name": "Port of Los Angeles"},
            "mode": "Ocean",
            "carrier": "Maersk Line",
            "vessel": "Maersk Edinburgh",
            "etd": "2024-12-12",
            "eta": "2024-12-28",
            "transitDays": 16,
            "container": "40ft High Cube",
            "cargo": "Electronics – Smartphones",
            "incoterm": "FOB",
            "value": 220000,
            "distanceKm": 13200,
            "tradeLane": "VN-US",
        },
        "risk": {
            "score": 0.72,
            "level": "HIGH",
            "expectedLoss": 45000,
            "var95": 67500,
            "cvar95": 81000,
        },
        "miniGauges": [
            {"label": "Expected Loss", "value": 45000, "format": "usd"},
            {"label": "VaR 95%", "value": 67500, "format": "usd"},
            {"label": "CVaR 95%", "value": 81000, "format": "usd"},
            {"label": "Carrier Reliability", "value": 0.92, "format": "pct"},
            {"label": "Climate Risk", "value": 0.68, "format": "pct"},
            {"label": "Avg Delay", "value": 4.2, "format": "days"},
        ],
        "radar": {
            "labels": ["Transport", "Cargo", "Route", "Incoterm", "Container", "Packaging", "Priority", "Climate"],
            "values": [0.6, 0.7, 0.5, 0.5, 0.7, 0.4, 0.6, 0.5],
        },
        "layers": [
            {"name": "Transport", "score": 0.6},
            {"name": "Cargo", "score": 0.7},
            {"name": "Route", "score": 0.5},
            {"name": "Incoterm", "score": 0.5},
            {"name": "Container", "score": 0.7},
            {"name": "Packaging", "score": 0.4},
            {"name": "Priority", "score": 0.6},
            {"name": "Climate", "score": 0.5},
        ],
        "riskFactors": [
            {"name": "Pacific Storm Season", "score": 8.2, "contribution": 0.26},
            {"name": "LAX Port Congestion", "score": 7.5, "contribution": 0.19},
            {"name": "Electronics Theft Risk", "score": 6.8, "contribution": 0.15},
            {"name": "Container Shortage", "score": 6.2, "contribution": 0.12},
            {"name": "Customs Delays", "score": 5.0, "contribution": 0.07},
            {"name": "Carrier Reliability", "score": 4.8, "contribution": 0.06},
            {"name": "Documentation Issues", "score": 4.2, "contribution": 0.04},
        ],
        "financial": {
            "distribution": [2, 5, 9, 15, 22, 18, 12, 7, 3, 1],
            "lossAxis": [0, 20000, 40000, 60000, 80000, 100000, 120000],
        },
        "lossCurve": {
            "points": [
                {"x": 0, "y": 0},
                {"x": 25, "y": 12000},
                {"x": 50, "y": 24000},
                {"x": 75, "y": 42000},
                {"x": 90, "y": 58000},
                {"x": 95, "y": 67500},
                {"x": 99, "y": 90000},
            ],
            "var95": 67500,
            "cvar95": 81000,
        },
        "climate": {
            "hazardIndex": 6.8,
            "var95": 0.18,
            "cvar95": 0.22,
            "notes": [
                "Elevated Pacific storm activity through Q4",
                "Monitor LAX port congestion advisories",
                "Route crosses medium piracy watchlist zone",
            ],
        },
        "scenarios": [
            {"name": "Expected", "risk": 0.72, "loss": 45000, "color": "moderate"},
            {"name": "Best Case", "risk": 0.55, "loss": 31500, "color": "low"},
            {"name": "Worst Case", "risk": 0.88, "loss": 67500, "color": "critical"},
        ],
        "timeline": [
            {"label": "POL Gate-In", "status": "completed", "date": "2024-12-10", "risk": 0.2},
            {"label": "CY Cutoff", "status": "completed", "date": "2024-12-11", "risk": 0.3},
            {"label": "Vessel Departure", "status": "completed", "date": "2024-12-12", "risk": 0.4},
            {"label": "Ocean Crossing", "status": "current", "date": "2024-12-20", "risk": 0.7},
            {"label": "POD Arrival", "status": "future", "date": "2024-12-28", "risk": 0.5},
            {"label": "Customs Clearance", "status": "future", "date": "2024-12-29", "risk": 0.35},
            {"label": "Final Delivery", "status": "future", "date": "2024-12-31", "risk": 0.25},
        ],
        "globe": {
            "origin": {"lat": 10.7769, "lon": 106.7009, "label": "VNSGN"},
            "destination": {"lat": 33.7506, "lon": -118.2677, "label": "USLAX"},
            "route": [
                {"lat": 10.7769, "lon": 106.7009},
                {"lat": 14.0, "lon": 115.0},
                {"lat": 25.0, "lon": 150.0},
                {"lat": 33.7506, "lon": -118.2677},
            ],
        },
        "ai": {
            "insights": [
                "Primary driver: Pacific Storm Season (26% contribution).",
                "Port congestion at LAX may extend dwell time by 1-3 days.",
                "Carrier reliability at 92% mitigates some schedule risk.",
            ],
            "actions": [
                "Consider slight departure shift to avoid peak storm window.",
                "Pre-book terminal appointment to reduce congestion delays.",
                "Enable enhanced cargo tracking for high-value electronics.",
            ],
        },
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
DIST_DIR = BASE_DIR.parent / "dist"
if DIST_DIR.exists():
    app.mount("/dist", StaticFiles(directory=str(DIST_DIR)), name="dist")

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

@app.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    """Results page - ENGINE-FIRST architecture"""
    context = {"request": request}
    context.update(get_template_context())
    
    # Try to inject summary data if available (for window.__RISKCAST_SUMMARY__)
    try:
        from app.core.engine_state import get_last_result_v2
        v2_result = get_last_result_v2()
        if v2_result:
            import json
            # Pass as JSON string - will be inserted directly into JS
            context["summary_json"] = json.dumps(v2_result, ensure_ascii=False)
    except Exception as e:
        # Continue without injected data
        if hasattr(e, '__module__'):
            pass  # Silently fail
    
    return templates.TemplateResponse("results.html", context)

@app.get("/results-showcase", response_class=HTMLResponse)
async def results_showcase(request: Request):
    """Results showcase page with mock data toggle"""
    context = {"request": request}
    context.update(get_template_context())
    return templates.TemplateResponse("results_showcase.html", context)

@app.get("/results_legacy", response_class=HTMLResponse)
async def view_results(request: Request):
    """ResultsOS v4000 page."""
    context = {"request": request}
    context.update(get_template_context())
    return templates.TemplateResponse("results.html", context)

@app.get("/results/data")
async def results_data():
    """
    Backend data feed for ResultsOS v4000 front-end.
    
    ARCHITECTURE: ENGINE-FIRST
    - Returns data that has passed through the CORE RISK ENGINE
    - Priority: LAST_RESULT_V2 (from Engine v2) > LAST_RESULT (legacy) > demo data
    - Results page MUST use this endpoint as primary data source
    - Storage (localStorage/sessionStorage) is ONLY a fallback for legacy support
    
    Returns:
        Complete engine result object (authoritative, immutable)
        If no engine result exists, returns 404 or empty payload
    """
    result = compute_results()
    
    # If no engine result exists, return empty payload (not demo data)
    # This forces Results page to explicitly handle "no data" state
    v2_result = get_last_result_v2()
    if not v2_result and not LAST_RESULT:
        # Return empty payload - Results page will fall back to storage
        return {}
    
    return result


# ResultsOS v4000 route - MUST be early to avoid conflicts with other routes
@app.get("/results_os_v4000")
@app.get("/results_os_v4000/")
@app.get("/results_os_v4000/{path:path}")
async def results_os_v4000(request: Request, path: str = ""):
    """Legacy path: redirect to new ResultsOS page."""
    return RedirectResponse(url="/results", status_code=307)

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
    """Summary v400 page - Shipment Overview & Smart Editor."""
    context = {"request": request}
    context.update(get_template_context())
    return templates.TemplateResponse("summary/summary_v400.html", context)

@app.get("/results_os_v4000")
@app.get("/results_os_v4000/")
@app.get("/results_os_v4000/{path:path}")
async def results_os_v4000(request: Request, path: str = ""):
    """Legacy path: redirect to new ResultsOS page."""
    return RedirectResponse(url="/results", status_code=307)

# ============================
# API ROUTES
# ============================
# Include new v1 API router
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(api_router_v60, tags=["api-v60"])

# Include AI Adviser router
app.include_router(ai_router, prefix="/api/ai", tags=["AI Adviser"])

# Include Overview router
app.include_router(overview_router)


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
