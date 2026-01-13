# app/routes/backend_overview_route_v32.py
"""
RISKCAST Overview v32 - Backend Route
FastAPI route for Overview v32 page with proper data binding
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.core.templates import templates
from app.memory import memory_system
import json
from typing import Dict, Any, Optional

# Import LAST_RESULT from app/api.py module file (not from app/api package)
import importlib.util
from pathlib import Path

_api_module_path = Path(__file__).parent.parent / "api.py"
_api_spec = importlib.util.spec_from_file_location("_api_module", _api_module_path)
_api_module = importlib.util.module_from_spec(_api_spec)
_api_spec.loader.exec_module(_api_module)
LAST_RESULT = _api_module.LAST_RESULT

# Port database with lat/lon
PORT_DATABASE = {
    'VNSGN': {'name': 'Ho Chi Minh', 'country': 'Vietnam', 'code': 'VNSGN', 'lat': 10.8231, 'lon': 106.6297},
    'SGN': {'name': 'Ho Chi Minh', 'country': 'Vietnam', 'code': 'VNSGN', 'lat': 10.8231, 'lon': 106.6297},
    'CNSHA': {'name': 'Shanghai', 'country': 'China', 'code': 'CNSHA', 'lat': 31.2304, 'lon': 121.4737},
    'SHA': {'name': 'Shanghai', 'country': 'China', 'code': 'CNSHA', 'lat': 31.2304, 'lon': 121.4737},
    'SGSIN': {'name': 'Singapore', 'country': 'Singapore', 'code': 'SGSIN', 'lat': 1.3521, 'lon': 103.8198},
    'SIN': {'name': 'Singapore', 'country': 'Singapore', 'code': 'SGSIN', 'lat': 1.3521, 'lon': 103.8198},
    'HKHKG': {'name': 'Hong Kong', 'country': 'Hong Kong', 'code': 'HKHKG', 'lat': 22.3193, 'lon': 114.1694},
    'HKG': {'name': 'Hong Kong', 'country': 'Hong Kong', 'code': 'HKHKG', 'lat': 22.3193, 'lon': 114.1694},
    'USLAX': {'name': 'Los Angeles', 'country': 'USA', 'code': 'USLAX', 'lat': 33.7701, 'lon': -118.1937},
    'LAX': {'name': 'Los Angeles', 'country': 'USA', 'code': 'USLAX', 'lat': 33.7701, 'lon': -118.1937},
    'USJFK': {'name': 'New York', 'country': 'USA', 'code': 'USJFK', 'lat': 40.6413, 'lon': -73.7781},
    'JFK': {'name': 'New York', 'country': 'USA', 'code': 'USJFK', 'lat': 40.6413, 'lon': -73.7781},
    'CMP': {'name': 'Ho Chi Minh', 'country': 'Vietnam', 'code': 'VNSGN', 'lat': 10.8231, 'lon': 106.6297},
    'COL': {'name': 'Colombia', 'country': 'Colombia', 'code': 'COL', 'lat': 4.7110, 'lon': -74.0721},
    'USA': {'name': 'United States', 'country': 'USA', 'code': 'USA', 'lat': 39.8283, 'lon': -98.5795},
    'CHN': {'name': 'China', 'country': 'China', 'code': 'CHN', 'lat': 35.8617, 'lon': 104.1954},
    'KOR': {'name': 'South Korea', 'country': 'South Korea', 'code': 'KOR', 'lat': 35.9078, 'lon': 127.7669},
    'JPN': {'name': 'Japan', 'country': 'Japan', 'code': 'JPN', 'lat': 36.2048, 'lon': 138.2529},
    'DEU': {'name': 'Germany', 'country': 'Germany', 'code': 'DEU', 'lat': 51.1657, 'lon': 10.4515},
}

def get_port_info(port_code: str) -> Dict[str, Any]:
    """Get port information from database"""
    if not port_code:
        return PORT_DATABASE["VNSGN"]
    port_code = port_code.upper()
    return PORT_DATABASE.get(port_code, PORT_DATABASE["VNSGN"])

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great circle distance between two points in kilometers using Haversine formula"""
    import math
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# Create router
router = APIRouter()

@router.get("/overview", response_class=HTMLResponse)
async def overview_v32_page(request: Request, id: Optional[str] = None):
    """
    Overview v32 page - Global 3D Overview of shipment data
    
    Args:
        request: FastAPI Request object
        id: Optional shipment ID (for future use with session memory)
    
    Returns:
        HTMLResponse with overview_v32.html template
    """
    # Priority 1: Get shipment data from session (most recent)
    shipment_data = request.session.get("shipment_data", {}) if hasattr(request, 'session') else {}
    
    # Priority 2: Get from memory system
    if not shipment_data:
        shipment_data = memory_system.get("latest_shipment") or {}
    
    # Priority 3: Get from LAST_RESULT (legacy)
    if not shipment_data and LAST_RESULT:
        shipment = LAST_RESULT.get('shipment', {})
        if shipment:
            shipment_data = {
                'transport_mode': shipment.get('transport_mode', ''),
                'route': shipment.get('route', ''),
                'eta': shipment.get('eta', ''),
                'etd': shipment.get('etd', ''),
                'cargo_type': shipment.get('cargo_type', ''),
                'cargo_value': shipment.get('cargo_value', 0),
                'pol_code': shipment.get('origin', ''),
                'pod_code': shipment.get('destination', ''),
                'risk_score': LAST_RESULT.get('overall_risk', 7.2),
                'risk_level': LAST_RESULT.get('risk_level', 'Medium')
            }
    
    # Get POL/POD info
    pol_code = shipment_data.get("pol_code") or shipment_data.get("origin") or "VNSGN"
    pod_code = shipment_data.get("pod_code") or shipment_data.get("destination") or "CNSHA"
    pol_info = get_port_info(pol_code)
    pod_info = get_port_info(pod_code)
    
    # Get transport mode
    transport_mode = shipment_data.get("transport_mode", "")
    mode = "ocean"
    if transport_mode:
        mode = transport_mode.replace("_fcl", "").replace("_lcl", "").replace("_", "").lower()
    
    # Build segments with distance calculations
    singapore = get_port_info("SGSIN")
    direct_distance = calculate_distance_km(pol_info['lat'], pol_info['lon'], pod_info['lat'], pod_info['lon'])
    
    segments = []
    if direct_distance > 8000:  # Long route, add intermediate stop
        seg1_distance = calculate_distance_km(pol_info['lat'], pol_info['lon'], singapore['lat'], singapore['lon'])
        seg2_distance = calculate_distance_km(singapore['lat'], singapore['lon'], pod_info['lat'], pod_info['lon'])
        
        segments = [
            {
                "from": pol_info['code'],
                "to": singapore['code'],
                "lat1": pol_info['lat'],
                "lon1": pol_info['lon'],
                "lat2": singapore['lat'],
                "lon2": singapore['lon'],
                "mode": mode,
                "distance": round(seg1_distance, 1)
            },
            {
                "from": singapore['code'],
                "to": pod_info['code'],
                "lat1": singapore['lat'],
                "lon1": singapore['lon'],
                "lat2": pod_info['lat'],
                "lon2": pod_info['lon'],
                "mode": mode,
                "distance": round(seg2_distance, 1)
            }
        ]
    else:
        # Direct route
        segments = [
            {
                "from": pol_info['code'],
                "to": pod_info['code'],
                "lat1": pol_info['lat'],
                "lon1": pol_info['lon'],
                "lat2": pod_info['lat'],
                "lon2": pod_info['lon'],
                "mode": mode,
                "distance": round(direct_distance, 1)
            }
        ]
    
    # Build shipmentState JSON structure (EXACT format as specified)
    shipment_state = {
        "transport": {
            "mode": mode,
            "vessel_name": shipment_data.get("carrier") or shipment_data.get("vessel_name") or "-",
            "flight_number": shipment_data.get("flight_number") or "-"
        },
        "cargo": {
            "commodity": shipment_data.get("cargo_type") or "-",
            "weight": shipment_data.get("weight") or shipment_data.get("cargo_weight") or "-",
            "volume": shipment_data.get("volume") or shipment_data.get("cargo_volume") or "-",
            "container_type": shipment_data.get("container") or shipment_data.get("container_type") or "-",
            "hs_code": shipment_data.get("hs_code") or "-"
        },
        "parties": {
            "shipper": shipment_data.get("shipper") or shipment_data.get("seller") or "-",
            "consignee": shipment_data.get("consignee") or shipment_data.get("buyer") or "-",
            "forwarder": shipment_data.get("forwarder") or "-"
        },
        "risk": {
            "score": float(shipment_data.get("risk_score", 7.2)) if shipment_data.get("risk_score") else 7.2,
            "weather": shipment_data.get("weather_risk") or shipment_data.get("weather") or "-",
            "congestion": shipment_data.get("port_risk") or shipment_data.get("congestion") or "-",
            "delay_probability": shipment_data.get("delay_probability") or "-"
        },
        "segments": segments
    }
    
    # Convert to JSON string for embedding in template
    shipment_state_json = json.dumps(shipment_state, ensure_ascii=False)
    
    return templates.TemplateResponse("overview_v32.html", {
        "request": request,
        "shipment_state_json": shipment_state_json
    })

# Redirect /overview to /summary to remove dependency on legacy overview templates
@router.get("/overview")
async def overview_redirect():
    return RedirectResponse("/summary")

