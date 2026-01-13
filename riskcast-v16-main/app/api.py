# app/api.py
from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime

from app.core.services.risk_service import run_risk_engine_v14

router = APIRouter()

# Store last result
LAST_RESULT: Optional[Dict[str, Any]] = None

def extract_origin_from_route(route: str) -> str:
    """Extract origin port code from route string"""
    if not route:
        return 'LAX'
    parts = route.split('_')
    if len(parts) >= 2:
        origin_part = parts[0]
        port_map = {
            'VN': 'SGN', 'VNSGN': 'SGN', 'VNHPH': 'HPH',
            'US': 'LAX', 'USLAX': 'LAX', 'USNYC': 'NYC', 'USJFK': 'JFK',
            'CN': 'SHA', 'CNSHA': 'SHA', 'CNPEK': 'PEK',
            'EU': 'DEP', 'EUDEP': 'DEP', 'EULON': 'LON'
        }
        return port_map.get(origin_part, origin_part[-3:] if len(origin_part) >= 3 else 'LAX')
    return 'LAX'

def extract_destination_from_route(route: str) -> str:
    """Extract destination port code from route string"""
    if not route:
        return 'JFK'
    parts = route.split('_')
    if len(parts) >= 2:
        dest_part = parts[1]
        port_map = {
            'VN': 'SGN', 'VNSGN': 'SGN', 'VNHPH': 'HPH',
            'US': 'JFK', 'USLAX': 'LAX', 'USNYC': 'NYC', 'USJFK': 'JFK',
            'CN': 'SHA', 'CNSHA': 'SHA', 'CNPEK': 'PEK',
            'EU': 'DEP', 'EUDEP': 'DEP', 'EULON': 'LON'
        }
        return port_map.get(dest_part, dest_part[-3:] if len(dest_part) >= 3 else 'JFK')
    return 'JFK'


def _normalize_port_code(value: Optional[str], fallback: str) -> str:
    """Normalize a port/airport code with a safe fallback."""
    if value and isinstance(value, str) and value.strip():
        return value.strip().upper()
    return fallback


def _build_trade_lane(pol_code: str, pod_code: str) -> str:
    """Build a compact trade lane key (e.g., vn_cn) for frontends."""
    try:
        origin = pol_code[:2].lower()
        dest = pod_code[:2].lower()
        return f"{origin}_{dest}"
    except Exception:
        return "vn_cn"


def build_riskcast_state_from_shipment(shipment_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Create the RISKCAST_STATE shape expected by the overview UI."""
    pol_code = _normalize_port_code(
        shipment_dict.get("pol_code") or extract_origin_from_route(shipment_dict.get("route", "")),
        "VNSGN",
    )
    pod_code = _normalize_port_code(
        shipment_dict.get("pod_code") or extract_destination_from_route(shipment_dict.get("route", "")),
        "CNSHA",
    )
    transport_mode = shipment_dict.get("transport_mode") or "ocean_fcl"
    trade_lane = _build_trade_lane(pol_code, pod_code)

    transport_label = transport_mode.replace("_fcl", "").replace("_lcl", "").replace("_", " ").title()
    pol_name = shipment_dict.get("pol_name") or shipment_dict.get("pol") or pol_code
    pod_name = shipment_dict.get("pod_name") or shipment_dict.get("pod") or pod_code

    # Build a minimal leg so the globe + cards never break
    default_leg = {
        "mode": transport_mode,
        "modeText": transport_label,
        "from": pol_name,
        "fromCode": pol_code,
        "to": pod_name,
        "toCode": pod_code,
        "distance": f"{shipment_dict.get('distance') or 0} km",
        "step": 1,
        "lat1": shipment_dict.get("pol_lat"),
        "lon1": shipment_dict.get("pol_lon"),
        "lat2": shipment_dict.get("pod_lat"),
        "lon2": shipment_dict.get("pod_lon"),
    }

    return {
        "transport": {
            "mode": transport_label or "Ocean",
            "pol": pol_name,
            "polCode": pol_code,
            "pod": pod_name,
            "podCode": pod_code,
            "totalDistance": f"{shipment_dict.get('distance') or 0} km",
            "segmentCount": 1,
            "tradeLane": trade_lane,
        },
        "cargo": {
            "commodity": shipment_dict.get("cargo_type") or "-",
            "weight": str(shipment_dict.get("weight") or shipment_dict.get("cargo_weight") or "-"),
            "volume": str(shipment_dict.get("volume") or shipment_dict.get("cargo_volume") or "-"),
            "containerType": shipment_dict.get("container") or shipment_dict.get("container_type") or "-",
            "hsCode": shipment_dict.get("hs_code") or "-",
        },
        "parties": {
            "shipper": (shipment_dict.get("shipper") or shipment_dict.get("seller") or "-"),
            "consignee": (shipment_dict.get("consignee") or shipment_dict.get("buyer") or "-"),
            "forwarder": shipment_dict.get("forwarder") or "-",
        },
        "risk": {
            "score": float(shipment_dict.get("risk_score", 7.2))
            if shipment_dict.get("risk_score") not in (None, "")
            else 7.2,
            "weatherRisk": shipment_dict.get("weather_risk") or shipment_dict.get("weather") or "-",
            "congestion": shipment_dict.get("port_risk") or shipment_dict.get("congestion") or "-",
            "delayProb": shipment_dict.get("delay_probability") or "-",
        },
        "routeLegs": [default_leg],
    }


class Shipment(BaseModel):
    """Shipment model matching Option A schema exactly"""
    transport_mode: str
    cargo_type: str
    route: str
    incoterm: str
    container: str
    packaging: str
    priority: str
    packages: int
    etd: str
    eta: str
    transit_time: float
    cargo_value: float
    distance: Optional[float] = Field(default=None)
    route_type: Optional[str] = Field(default=None)
    carrier_rating: Optional[float] = Field(default=None)
    weather_risk: Optional[float] = Field(default=None)
    port_risk: Optional[float] = Field(default=None)
    container_match: Optional[float] = Field(default=None)
    shipment_value: Optional[float] = Field(default=None)
    use_fuzzy: bool
    use_forecast: bool
    use_mc: bool
    use_var: bool
    ENSO_index: float = 0.0
    typhoon_frequency: float = 0.5
    sst_anomaly: float = 0.0
    port_climate_stress: float = 5.0
    climate_volatility_index: float = 5.0
    climate_tail_event_probability: float = 0.05
    ESG_score: float = 50.0
    climate_resilience: float = 5.0
    green_packaging: float = 5.0
    # === BUYER-SELLER FIELDS (v16.2) =================================
    buyer: Optional[Dict[str, Any]] = Field(default=None)
    seller: Optional[Dict[str, Any]] = Field(default=None)
    # === PRIORITY PROFILE FIELDS =====================================
    priority_profile: Optional[str] = Field(default=None)
    priority_weights: Optional[Dict[str, int]] = Field(default=None)


@router.post("/analyze")
async def analyze(shipment: Shipment):
    """
    Analyze shipment risk using RISKCAST v14.5 engine with climate intelligence.
    
    Accepts shipment data, runs full risk analysis pipeline, and stores result.
    Returns status and redirect URL for results page.
    """
    global LAST_RESULT

    try:
        # Convert Shipment to dict for engine
        shipment_dict = shipment.model_dump()
        result = run_risk_engine_v14(shipment_dict)
        
        # Add shipment data to result for dashboard display
        result['shipment'] = {
            'route': shipment_dict.get('route', ''),
            'origin': extract_origin_from_route(shipment_dict.get('route', '')),
            'destination': extract_destination_from_route(shipment_dict.get('route', '')),
            'eta': shipment_dict.get('eta', ''),
            'etd': shipment_dict.get('etd', ''),
            'transport_mode': shipment_dict.get('transport_mode', ''),
            'cargo_type': shipment_dict.get('cargo_type', ''),
            'cargo_value': shipment_dict.get('cargo_value', 0),
            'shipment_id': f"FX-{datetime.now().year}-{abs(hash(str(shipment_dict))) % 10000}"
        }
        
        # Store result for retrieval
        LAST_RESULT = result
        
        # Save to memory_system for overview page
        from app.memory import memory_system
        # Store shipment data for overview
        memory_system.set("latest_shipment", {
            **shipment_dict,
            "pol_code": shipment_dict.get("pol_code", extract_origin_from_route(shipment_dict.get('route', ''))),
            "pod_code": shipment_dict.get("pod_code", extract_destination_from_route(shipment_dict.get('route', ''))),
            "risk_score": result.get("overall_risk", result.get("risk_score", 0.5)),
            "risk_level": result.get("risk_level", "MODERATE")
        })
        
        # Build enriched response payload
        advanced_metrics = result.get('advanced_metrics', {})
        response_payload = {
            "status": "ok",
            "redirect_url": "/overview",  # Redirect to Overview v33 (FutureOS Edition)
            "result": result,
            "overall_risk": result.get("overall_risk", result.get("risk_score", 0.5) * 100),
            "risk_level": result.get("risk_level", "MODERATE"),
            "expected_loss": result.get("expected_loss", 0),
            "expected_loss_usd": result.get("expected_loss_usd", result.get("expected_loss", 0)),
            "delay_probability": result.get("delay_probability", 0.0),
            "delay_days_estimate": result.get("delay_days_estimate", 0),
            "risk_factors": result.get("risk_factors", []),
            "dynamic_weights": result.get("dynamic_weights", {}),
            "radar_data": result.get("radar", {}),
            "scenario_analysis": result.get("scenario_analysis", {}),
            "financial_distribution": result.get("financial_distribution", {}),
            "advanced_metrics": {
                **advanced_metrics,
                "climate_var_metrics": advanced_metrics.get("climate_var_metrics", {}),
                "climate_hazard_index": result.get("climate_hazard_index", 5.0),
                "esg_score": advanced_metrics.get("esg_score", 50),
                "green_packaging": advanced_metrics.get("green_packaging", 50),
                "climate_resilience": advanced_metrics.get("climate_resilience", 5.0)
            },
            "layer_interactions": result.get("layer_interactions", {}),
            "ai_summary": result.get("ai_summary", {}),
            "forecast": result.get("forecast", {}),
            "buyer_seller_analysis": result.get("buyer_seller_analysis", {}),
            "priority_profile": result.get("priority_profile", "standard"),
            "priority_weights": result.get("priority_weights", {'speed': 40, 'cost': 40, 'risk': 20})
        }

        return response_payload
    except Exception as e:
        print(f"[API ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Risk engine failed: {str(e)}")


@router.post("/run")
async def run(shipment: Shipment):
    """
    Legacy endpoint - redirects to /analyze for backward compatibility.
    """
    return await analyze(shipment)


@router.post("/run_risk")
async def run_risk(shipment: Shipment):
    """
    Alias for /run endpoint - for backward compatibility with frontend.
    """
    return await analyze(shipment)


@router.post("/run_analysis")
async def run_analysis(request: Request):
    """
    Run risk analysis endpoint for simplified frontend payload.
    Accepts dict payload and transforms to Shipment model format.
    """
    global LAST_RESULT

    try:
        # Get JSON body from request
        payload = await request.json()
        
        def _to_float(key: str) -> Optional[float]:
            value = payload.get(key)
            if value in (None, ""):
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        
        # Transform payload to Shipment format
        shipment_dict = {
            "transport_mode": payload.get("transport_mode", ""),
            "cargo_type": payload.get("cargo_type", "general"),
            "route": payload.get("route", ""),
            "incoterm": payload.get("incoterm", ""),
            "container": payload.get("container", ""),
            "packaging": payload.get("packaging", ""),
            "priority": payload.get("priority", ""),
            "packages": int(payload.get("packages", 0)) if payload.get("packages") else 0,
            "etd": payload.get("etd", ""),
            "eta": payload.get("eta", ""),
            "transit_time": float(payload.get("transit_time", 0)) if payload.get("transit_time") else 0.0,
            "cargo_value": float(payload.get("cargo_value", 0)) if payload.get("cargo_value") else 0.0,
            "distance": _to_float("distance"),
            "route_type": payload.get("route_type"),
            "carrier_rating": _to_float("carrier_rating"),
            "weather_risk": _to_float("weather_risk"),
            "port_risk": _to_float("port_risk"),
            "container_match": _to_float("container_match"),
            "shipment_value": _to_float("shipment_value"),
            "use_fuzzy": payload.get("use_fuzzy", False),
            "use_forecast": payload.get("use_forecast", False),
            "use_mc": payload.get("use_mc", False),
            "use_var": payload.get("use_var", False),
            # Climate fields with defaults
            "ENSO_index": payload.get("ENSO_index", 0.0),
            "typhoon_frequency": payload.get("typhoon_frequency", 0.5),
            "sst_anomaly": payload.get("sst_anomaly", 0.0),
            "port_climate_stress": payload.get("port_climate_stress", 5.0),
            "climate_volatility_index": payload.get("climate_volatility_index", 5.0),
            "climate_tail_event_probability": payload.get("climate_tail_event_probability", 0.05),
            "ESG_score": payload.get("ESG_score", 50.0),
            "climate_resilience": payload.get("climate_resilience", 5.0),
            "green_packaging": payload.get("green_packaging", 5.0),
            # Buyer/Seller info
            "buyer": payload.get("buyer"),
            "seller": payload.get("seller"),
            "priority_profile": payload.get("priority_profile"),
            "priority_weights": payload.get("priority_weights")
        }
        
        # Save to session for overview page
        if hasattr(request, "session"):
            request.session["shipment_data"] = shipment_dict
            # Build unified RISKCAST_STATE for frontends (overview/results)
            request.session["RISKCAST_STATE"] = build_riskcast_state_from_shipment(shipment_dict)
        
        # Create Shipment model instance
        shipment = Shipment(**shipment_dict)
        
        # Run analysis using existing analyze function
        return await analyze(shipment)
        
    except Exception as e:
        print(f"[API ERROR] run_analysis failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")


@router.get("/get_last_result")
async def get_last_result():
    """
    Retrieve the last computed risk analysis result.
    
    Returns the full result JSON if available, or error message if no result exists.
    This endpoint is called by the results page to display analysis data.
    """
    if LAST_RESULT is None:
        return {"error": "no_result"}
    
    return LAST_RESULT

