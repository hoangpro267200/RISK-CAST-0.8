# app/routes/overview.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from app.core.templates import templates
from app.memory import memory_system
import importlib.util
import os
import json
from datetime import datetime
from pathlib import Path

# Import LAST_RESULT from app/api.py module file (not from app/api package)
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
}

def get_port_info(port_code: str):
    """Get port information from database"""
    if not port_code:
        return PORT_DATABASE.get('VNSGN')
    port_code = port_code.upper()
    return PORT_DATABASE.get(port_code, PORT_DATABASE.get('VNSGN'))

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

BASIC_OVERVIEW_FALLBACK = {
    "cities": [
        {"name": "Los Angeles", "lat": 34.0522, "lng": -118.2437},
        {"name": "Shanghai", "lat": 31.2304, "lng": 121.4737},
        {"name": "Singapore", "lat": 1.3521, "lng": 103.8198},
        {"name": "Rotterdam", "lat": 51.9225, "lng": 4.4792},
        {"name": "Dubai", "lat": 25.2048, "lng": 55.2708},
    ],
    "routes": [
        {"startLat": 34.0522, "startLng": -118.2437, "endLat": 31.2304, "endLng": 121.4737},
        {"startLat": 31.2304, "startLng": 121.4737, "endLat": 1.3521, "endLng": 103.8198},
        {"startLat": 1.3521, "startLng": 103.8198, "endLat": 25.2048, "endLng": 55.2708},
        {"startLat": 25.2048, "startLng": 55.2708, "endLat": 51.9225, "endLng": 4.4792},
    ],
    "summary": {
        "vessel": "MSC GÜLSÜN",
        "distance": "12,847 NM",
        "eta": "2025-12-28 14:30 UTC",
        "riskLevel": "LOW",
    },
}

V35_DEMO_STATE = {
    "transport": {
        "tradeLane": "Asia - Europe",
        "modeOfTransport": "Ocean Freight",
        "shipmentType": "FCL",
        "serviceRoute": "Direct",
        "carrier": "Maersk Line",
        "priority": "Standard",
        "incoterm": "FOB",
        "incotermLocation": "Shanghai",
        "pol": "Shanghai, China",
        "pod": "Rotterdam, Netherlands",
        "containerType": "40HC",
        "etd": "15/12/2025",
        "scheduleFrequency": "Weekly",
        "transitTimeDays": 35,
        "eta": "19/01/2026",
        "reliabilityScore": "92%",
    },
    "cargo": {
        "cargoType": "Electronics",
        "hsCode": "8517.62.00",
        "packingType": "Cartons",
        "numberOfPackages": 480,
        "grossWeight": "12000 kg",
        "netWeight": "11500 kg",
        "volume": "65 m³",
        "stackability": "Yes",
        "insuranceValue": "$450,000",
        "insuranceCoverage": "All Risk",
        "cargoSensitivity": "Fragile",
        "dangerousGoods": "No",
        "cargoDescription": "Mobile phone components and accessories",
        "specialHandling": "Keep dry, avoid extreme temperatures",
    },
    "seller": {
        "companyName": "Shanghai Tech Electronics Co., Ltd.",
        "businessType": "Manufacturer",
        "country": "China",
        "city": "Shanghai",
        "address": "1288 Zhongshan Road, Pudong District",
        "contactPerson": "Li Wei",
        "role": "Export Manager",
        "email": "li.wei@shanghaitech.com",
        "phone": "+86 21 5888 9999",
        "taxId": "91310000MA1FL5",
    },
    "buyer": {
        "companyName": "EuroTech Distribution B.V.",
        "businessType": "Distributor",
        "country": "Netherlands",
        "city": "Rotterdam",
        "address": "Wilhelminakade 123, 3072 AP",
        "contactPerson": "Jan van der Berg",
        "role": "Procurement Director",
        "email": "j.vandenberg@eurotech.nl",
        "phone": "+31 10 123 4567",
        "taxId": "NL123456789B01",
    },
    "risk": {
        "overall": "LOW",
        "weather": "LOW",
        "political": "LOW",
        "security": "MEDIUM",
    },
    "riskModules": {
        "esg": True,
        "weather": True,
        "congestion": True,
        "carrier": True,
        "market": True,
        "insurance": True,
    },
    "routeLegs": [
        {
            "from": {"name": "Shanghai", "lat": 31.2304, "lng": 121.4737},
            "to": {"name": "Singapore", "lat": 1.3521, "lng": 103.8198},
            "distanceNm": 1450,
        },
        {
            "from": {"name": "Singapore", "lat": 1.3521, "lng": 103.8198},
            "to": {"name": "Colombo", "lat": 6.9271, "lng": 79.8612},
            "distanceNm": 1680,
        },
        {
            "from": {"name": "Colombo", "lat": 6.9271, "lng": 79.8612},
            "to": {"name": "Suez Canal", "lat": 30.5852, "lng": 32.2654},
            "distanceNm": 3420,
        },
        {
            "from": {"name": "Suez Canal", "lat": 30.5852, "lng": 32.2654},
            "to": {"name": "Rotterdam", "lat": 51.9225, "lng": 4.4792},
            "distanceNm": 3850,
        },
    ],
}


@router.get("/overview-basic", response_class=HTMLResponse)
async def overview_basic(request: Request):
    """Basic FutureOS overview page (stable mode)."""
    cesium_token = os.getenv("CESIUM_ION_TOKEN") or os.getenv("CESIUM_TOKEN") or ""
    context = {
        "request": request,
        "CESIUM_TOKEN": cesium_token,
    }
    return templates.TemplateResponse("overview_basic.html", context)


def _parse_date(date_str: str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except Exception:
            return None


def _format_date_ddmmyyyy(dt: datetime):
    if not dt:
        return ""
    return dt.strftime("%d/%m/%Y")


def build_v35_lite_state(payload: dict) -> dict:
    """
    Normalize incoming shipment/state data to the v35 lite shape.
    Fallback to demo if insufficient data.
    """
    if not isinstance(payload, dict) or not payload:
        return V35_DEMO_STATE

    state = V35_DEMO_STATE.copy()
    state = {k: (v.copy() if isinstance(v, dict) else v) for k, v in state.items()}

    # Transport mapping
    transport = state["transport"]
    transport["carrier"] = payload.get("carrier") or transport["carrier"]
    transport["incoterm"] = payload.get("incoterm") or payload.get("incoterms") or transport["incoterm"]
    transport["incotermLocation"] = payload.get("incoterm_location") or transport["incotermLocation"]
    transport["pol"] = payload.get("pol") or payload.get("origin") or transport["pol"]
    transport["pod"] = payload.get("pod") or payload.get("destination") or transport["pod"]
    transport["modeOfTransport"] = payload.get("mode") or payload.get("transport_mode") or transport["modeOfTransport"]
    transport["shipmentType"] = payload.get("shipment_type_label") or payload.get("shipment_type") or transport["shipmentType"]
    transport["priority"] = payload.get("priority") or transport["priority"]
    transport["containerType"] = payload.get("container_type") or transport["containerType"]
    etd_in = payload.get("etd") or payload.get("etd_date")
    eta_in = payload.get("eta") or payload.get("eta_date")
    transit_days = payload.get("transit_days") or payload.get("transitTimeDays")

    etd_dt = _parse_date(etd_in) if etd_in else None
    eta_dt = _parse_date(eta_in) if eta_in else None
    if not transit_days and etd_dt and eta_dt:
        transit_days = (eta_dt - etd_dt).days
    transport["etd"] = _format_date_ddmmyyyy(etd_dt) if etd_dt else (etd_in or transport["etd"])
    transport["eta"] = _format_date_ddmmyyyy(eta_dt) if eta_dt else (eta_in or transport["eta"])
    transport["transitTimeDays"] = transit_days or transport["transitTimeDays"]

    # Risk
    risk = state["risk"]
    risk_level = payload.get("risk_level") or payload.get("riskLevel") or risk["overall"]
    risk["overall"] = str(risk_level).upper()
    risk["weather"] = payload.get("risk_weather") or risk["weather"]
    risk["political"] = payload.get("risk_political") or risk["political"]
    risk["security"] = payload.get("risk_security") or risk["security"]

    # Cargo
    cargo = state["cargo"]
    cargo["cargoType"] = payload.get("cargo_type") or cargo["cargoType"]
    cargo["hsCode"] = payload.get("hs_code") or cargo["hsCode"]
    cargo["grossWeight"] = payload.get("gross_weight") or cargo["grossWeight"]
    cargo["netWeight"] = payload.get("net_weight") or cargo["netWeight"]
    cargo["volume"] = payload.get("volume") or cargo["volume"]
    cargo["insuranceValue"] = payload.get("insurance_value") or cargo["insuranceValue"]
    cargo["insuranceCoverage"] = payload.get("insurance_coverage") or cargo["insuranceCoverage"]
    cargo["cargoDescription"] = payload.get("cargo_description") or cargo["cargoDescription"]
    cargo["dangerousGoods"] = payload.get("dangerous_goods") or cargo["dangerousGoods"]

    # Parties (best-effort)
    seller = state["seller"]
    buyer = state["buyer"]
    seller["companyName"] = payload.get("seller") or seller["companyName"]
    buyer["companyName"] = payload.get("buyer") or buyer["companyName"]

    # Route legs
    route_legs = []
    pol_code = payload.get("pol_code") or payload.get("origin_code") or payload.get("origin")
    pod_code = payload.get("pod_code") or payload.get("destination_code") or payload.get("destination")
    pol_info = get_port_info(pol_code) if pol_code else None
    pod_info = get_port_info(pod_code) if pod_code else None
    if pol_info and pod_info:
        dist_km = calculate_distance_km(pol_info["lat"], pol_info["lon"], pod_info["lat"], pod_info["lon"])
        dist_nm = dist_km * 0.539957
        route_legs = [
            {
                "from": {"name": pol_info["name"], "lat": pol_info["lat"], "lng": pol_info["lon"]},
                "to": {"name": pod_info["name"], "lat": pod_info["lat"], "lng": pod_info["lon"]},
                "distanceNm": round(dist_nm, 1),
            }
        ]
        transport["pol"] = f"{pol_info['name']}, {pol_info['country']}"
        transport["pod"] = f"{pod_info['name']}, {pod_info['country']}"
    state["routeLegs"] = route_legs or state["routeLegs"]

    return state

def build_basic_overview_payload(shipment_data=None):
    """Build data payload for overview basic page."""
    if not shipment_data:
        return BASIC_OVERVIEW_FALLBACK

    pol_code = shipment_data.get("pol_code") or shipment_data.get("pol") or shipment_data.get("origin_port") or shipment_data.get("origin")
    pod_code = shipment_data.get("pod_code") or shipment_data.get("pod") or shipment_data.get("destination_port") or shipment_data.get("destination")

    pol_info = get_port_info(pol_code)
    pod_info = get_port_info(pod_code)

    if not pol_info or not pod_info:
        return BASIC_OVERVIEW_FALLBACK

    distance_km = calculate_distance_km(pol_info["lat"], pol_info["lon"], pod_info["lat"], pod_info["lon"])
    distance_nm = distance_km * 0.539957

    cities = [
        {"name": pol_info["name"], "lat": pol_info["lat"], "lng": pol_info["lon"]},
        {"name": pod_info["name"], "lat": pod_info["lat"], "lng": pod_info["lon"]},
    ]

    routes = [
        {"startLat": pol_info["lat"], "startLng": pol_info["lon"], "endLat": pod_info["lat"], "endLng": pod_info["lon"]}
    ]

    summary = {
        "vessel": shipment_data.get("vessel") or shipment_data.get("carrier") or "Demo Vessel",
        "distance": f"{distance_nm:,.0f} NM",
        "eta": shipment_data.get("eta") or shipment_data.get("etd") or "TBD",
        "riskLevel": (shipment_data.get("risk_level") or "LOW").upper(),
    }

    return {"cities": cities, "routes": routes, "summary": summary}

@router.get("/overview")
async def overview_page():
    """Redirect overview directly to summary to remove dependency on overview templates."""
    return RedirectResponse("/summary")


@router.get("/global-overview", response_class=HTMLResponse)
async def global_overview_page(request: Request):
    """Alias for /overview using the v35 lite experience."""
    return RedirectResponse("/summary")


# Explicit alias for the new IBM-style overview
@router.get("/overview-v36-ibm", response_class=HTMLResponse)
async def overview_v36_ibm(request: Request):
    return RedirectResponse("/summary")


# Alias for FutureOS v40 template now pointing to v60
@router.get("/overview-v40", response_class=HTMLResponse)
async def overview_v40(request: Request):
    return RedirectResponse("/summary")


@router.get("/api/shipment/state")
async def get_shipment_state():
    """
    Return complete shipment state for Overview v31.
    This is the primary data source for the frontend.
    
    Returns:
    {
        "cargo": {...},
        "transport": {...},
        "parties": {...},
        "risk": {...},
        "segments": [
            {
                "from": "VNSGN",
                "to": "SGSIN",
                "lat1": 10.8231,
                "lon1": 106.6297,
                "lat2": 1.3521,
                "lon2": 103.8198,
                "distance": 1087
            },
            ...
        ]
    }
    """
    # Get shipment data from memory system
    shipment_data = memory_system.get("latest_shipment") or {}
    
    # If no shipment data, return empty state (not an error)
    # Frontend will use template fallback
    if not shipment_data:
        return JSONResponse({
            "cargo": {},
            "transport": {},
            "parties": {},
            "risk": {},
            "segments": []
        })
    
    # Extract port codes
    pol_code = shipment_data.get("pol_code") or shipment_data.get("origin") or "VNSGN"
    pod_code = shipment_data.get("pod_code") or shipment_data.get("destination") or "CNSHA"
    pol_info = get_port_info(pol_code)
    pod_info = get_port_info(pod_code)
    
    # Get transport mode
    transport_mode = shipment_data.get("transport_mode", "")
    mode = "ocean"
    if transport_mode:
        mode = transport_mode.replace("_fcl", "").replace("_lcl", "").replace("_", "")
    
    # Build segments
    singapore = get_port_info("SGSIN")
    direct_distance = calculate_distance_km(pol_info['lat'], pol_info['lon'], pod_info['lat'], pod_info['lon'])
    
    segments = []
    if direct_distance > 8000:
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
                "distance": round(seg1_distance, 1)
            },
            {
                "from": singapore['code'],
                "to": pod_info['code'],
                "lat1": singapore['lat'],
                "lon1": singapore['lon'],
                "lat2": pod_info['lat'],
                "lon2": pod_info['lon'],
                "distance": round(seg2_distance, 1)
            }
        ]
    else:
        segments = [
            {
                "from": pol_info['code'],
                "to": pod_info['code'],
                "lat1": pol_info['lat'],
                "lon1": pol_info['lon'],
                "lat2": pod_info['lat'],
                "lon2": pod_info['lon'],
                "distance": round(direct_distance, 1)
            }
        ]
    
    # Build complete state
    state = {
        "cargo": {
            "type": shipment_data.get("cargo_type", "Electronics") or "Electronics",
            "hsCode": "8471.30",
            "quantity": "2 x 40' HC",
            "weight": "24,000 kg",
            "value": f"${shipment_data.get('cargo_value', 150000):,}" if shipment_data.get('cargo_value') else "$150,000"
        },
        "transport": {
            "mode": mode,
            "pol": f"{pol_info['name']}, {pol_info['country']} ({pol_info['code']})",
            "pod": f"{pod_info['name']}, {pod_info['country']} ({pod_info['code']})",
            "etd": shipment_data.get("etd", "2025-12-10"),
            "eta": shipment_data.get("eta", "2025-12-25")
        },
        "parties": {
            "seller": shipment_data.get("seller", "VN Tech Export Ltd.") or "VN Tech Export Ltd.",
            "buyer": shipment_data.get("buyer", "Shanghai Electronics Co.") or "Shanghai Electronics Co.",
            "incoterms": shipment_data.get("incoterm", "FOB") or "FOB",
            "paymentTerms": "L/C at sight"
        },
        "risk": {
            "score": float(shipment_data.get("risk_score", 7.2)) if shipment_data.get("risk_score") else 7.2,
            "level": shipment_data.get("risk_level", "Medium") or "Medium",
            "factors": [
                {"icon": "🌊", "label": "Weather: Moderate"},
                {"icon": "⚓", "label": "Port Congestion: Low"},
                {"icon": "📋", "label": "Documentation: OK"}
            ]
        },
        "segments": segments
    }
    
    return JSONResponse(state)


@router.get("/api/overview-data")
async def get_overview_basic_data():
    """Provide overview data for the basic FutureOS map."""
    shipment_data = memory_system.get("latest_shipment") or LAST_RESULT or {}
    if not isinstance(shipment_data, dict):
        shipment_data = {}
    payload = build_basic_overview_payload(shipment_data)
    return JSONResponse(payload)


@router.get("/api/overview_data")
async def get_overview_data():
    """
    Return latest shipment snapshot for Overview v21.
    
    Try order:
    1. memory_system.get("latest_shipment")
    2. Fallback: demo data
    """
    data = memory_system.get("latest_shipment")
    
    if not data:
        # Safe fallback demo data
        data = {
            "shipment_id": "RC-DEMO",
            "trade_lane_key": "vn_hk",
            "trade_lane_label": "Vietnam → Hong Kong",
            "mode": "ocean_fcl",
            "mode_label": "Sea Freight — FCL",
            "shipment_type_label": "Đường Biển — FCL",
            "pol_code": "CMP",
            "pod_code": "HKHKG",
            "carrier": "Maersk",
            "etd": "2025-12-09",
            "eta": "2025-12-11",
            "transit_days": 2,
            "risk_score": 12,
            "risk_level": "low",
            "reliability_score": 92,
            "weather": {
                "origin": {"code": "CMP", "temp_c": 30, "condition": "Sunny"},
                "destination": {"code": "HKHKG", "temp_c": 28, "condition": "Partly cloudy"}
            }
        }
    
    return JSONResponse(data)

