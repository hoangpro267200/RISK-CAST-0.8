"""
Shipment Summary Page Routes
Handles the new Vanilla JS-based shipment summary page
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Use shared templates + state storage
from app.core.templates import templates
from app.core.state_storage import load_state, generate_shipment_id

# Create router
router = APIRouter()


def generate_sample_shipment_data(shipment_id: str = None) -> Dict[str, Any]:
    """
    Generate sample shipment data for testing
    In production, this would fetch from database
    """
    if not shipment_id:
        shipment_id = f"SH-SGN-LAX-{int(datetime.now().timestamp())}"
    
    # Calculate dates
    now = datetime.now()
    etd = now + timedelta(days=2)
    eta = etd + timedelta(days=5)
    
    return {
        "shipment_id": shipment_id,
        "origin": {
            "code": "SGN",
            "city": "Ho Chi Minh City",
            "country": "Vietnam"
        },
        "destination": {
            "code": "LAX",
            "city": "Los Angeles",
            "country": "USA"
        },
        "transport_mode": "Air",
        "eta_range": f"{eta.strftime('%b %d')}-{eta.strftime('%d, %Y')}",
        "eta_duration": "5-7 days",
        "confidence": 85,
        "risk_level": "LOW",
        "expected_loss": "$2,400",
        "eta_reliability": "92%",
        "active_alerts": 2,
        "route": {
            "departure_date": etd.strftime("%b %d, %Y"),
            "departure_time": "14:30 UTC+7",
            "arrival_date": f"{eta.strftime('%b %d')}-{eta.strftime('%d, %Y')}",
            "transit_duration": "5-7 days",
            "incoterms": "FOB"
        },
        "cargo": {
            "commodity": "Electronics",
            "value": "$145,000",
            "weight": "2,450 kg",
            "packaging": "12 Pallets",
            "hs_code": "8471.30"
        },
        "parties": {
            "shipper": {
                "name": "TechVN Manufacturing",
                "location": "Ho Chi Minh City, VN"
            },
            "consignee": {
                "name": "Pacific Electronics Corp",
                "location": "Los Angeles, CA, USA"
            },
            "carrier": {
                "name": "Global Air Freight",
                "rating": "4.7/5.0"
            }
        }
    }


def get_shipment_data_from_memory(shipment_id: str = None) -> Dict[str, Any]:
    """
    Try to get shipment data from:
    1) Persistent state storage (future /api/v1/state flow)
    2) In-memory key-value store used by current input/overview flow
    Falls back to sample data if nothing is available.
    """
    # 1) Try persisted state_storage first (new flow from /api/v1/state)
    if shipment_id:
        try:
            loaded = load_state(shipment_id)
            if loaded:
                # File-based storage wraps the state in a {"state": {...}} envelope
                state = loaded.get("state") or loaded
                return transform_state_to_summary_data(state)
        except Exception as e:
            print(f"[ShipmentSummary] Could not load from state_storage: {e}")

    # 2) Try legacy memory system (current production flow)
    #    This is populated in multiple places, e.g.:
    #    - app.main.input_v20_submit (memory_system.set('latest_shipment', ...))
    #    - app.api.run_analysis
    from app.memory import memory_system

    try:
        shipment_payload = None

        # In the future we might support per-shipment IDs in memory.
        # For now, we use the canonical "latest_shipment" entry which is
        # already wired into the overview/dashboard flows.
        if shipment_id:
            # Best‑effort: try history-based storage first if available
            get_shipment = getattr(memory_system, "get_shipment", None)
            if callable(get_shipment):
                shipment_record = get_shipment(shipment_id)
                if shipment_record and isinstance(shipment_record, dict):
                    shipment_payload = shipment_record.get("shipment_data") or shipment_record

        if shipment_payload is None:
            shipment_payload = memory_system.get("latest_shipment")

        if shipment_payload:
            return transform_shipment_payload_to_summary_data(shipment_payload)

    except Exception as e:
        print(f"[ShipmentSummary] Could not load from memory: {e}")

    # 3) Fallback to sample data
    return generate_sample_shipment_data(shipment_id)


def transform_state_to_summary_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform existing RISKCAST state format (v35/v36 style) to new summary data format.
    
    NOTE: This is primarily for future /api/v1/state integration where we
    persist a richer RISKCAST_STATE object. For the current production
    flow that uses a simpler "shipment_payload" dict, see
    `transform_shipment_payload_to_summary_data` below.
    """
    shipment_meta = state.get("meta", {}) or {}
    shipment_id = shipment_meta.get("shipment_id") or state.get("shipment_id") or generate_shipment_id(state)

    # Extract route info – support both top‑level and nested trade_route keys
    route = state.get("trade_route", {}) or state.get("route", {}) or {}
    pol = route.get("pol_code") or state.get("pol_code") or "SGN"
    pod = route.get("pod_code") or state.get("pod_code") or "LAX"

    # Extract dates
    etd = route.get("etd") or state.get("etd") or datetime.now().strftime("%Y-%m-%d")
    eta = route.get("eta") or state.get("eta") or (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Calculate transit time
    try:
        etd_date = datetime.strptime(etd, "%Y-%m-%d")
        eta_date = datetime.strptime(eta, "%Y-%m-%d")
        transit_days = (eta_date - etd_date).days
    except:
        transit_days = 7
    
    # Extract cargo info
    cargo = state.get("cargo_packing", {}) or state.get("cargo", {}) or {}
    cargo_value = cargo.get("cargo_value", 0)
    
    # Extract parties
    seller = state.get("seller", {}) or state.get("shipper", {}) or {}
    buyer = state.get("buyer", {}) or state.get("consignee", {}) or {}
    
    return {
        "shipment_id": shipment_id,
        "origin": {
            "code": pol,
            "city": get_port_city(pol),
            "country": get_port_country(pol)
        },
        "destination": {
            "code": pod,
            "city": get_port_city(pod),
            "country": get_port_country(pod)
        },
        "transport_mode": route.get("transport_mode", "Air"),
        "eta_range": format_date_range(etd, eta),
        "eta_duration": f"{transit_days} days",
        "confidence": 85,  # Default
        "risk_level": "LOW",  # Will be calculated
        "expected_loss": f"${int(cargo_value * 0.02)}",  # Estimate
        "eta_reliability": "92%",  # Default
        "active_alerts": 0,
        "route": {
            "departure_date": format_date(etd),
            "departure_time": "14:30 UTC+7",
            "arrival_date": format_date_range(etd, eta),
            "transit_duration": f"{transit_days} days",
            "incoterms": route.get("incoterm", "FOB")
        },
        "cargo": {
            "commodity": cargo.get("cargo_type", "General"),
            "value": f"${cargo_value:,}" if cargo_value else "$0",
            "weight": f"{cargo.get('packages', 0) * 50} kg",  # Estimate
            "packaging": f"{cargo.get('packages', 0)} Pallets",
            "hs_code": cargo.get("hs_code", "N/A")
        },
        "parties": {
            "shipper": {
                "name": seller.get("name", "N/A"),
                "location": seller.get("location", "")
            },
            "consignee": {
                "name": buyer.get("name", "N/A"),
                "location": buyer.get("location", "")
            },
            "carrier": {
                "name": "Carrier TBD",
                "rating": "N/A"
            }
        }
    }


def transform_shipment_payload_to_summary_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform the simplified shipment payload (used by input_v20 & overview)
    into the summary data format expected by the new Shipment Summary page.
    
    This function is intentionally tolerant of missing fields and will
    fall back to sensible defaults where necessary.
    """
    # Basic identifiers
    pol = payload.get("pol_code") or payload.get("origin") or "SGN"
    pod = payload.get("pod_code") or payload.get("destination") or "LAX"

    # Dates & transit
    etd = payload.get("etd") or datetime.now().strftime("%Y-%m-%d")
    eta = payload.get("eta") or (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    try:
        etd_date = datetime.strptime(etd, "%Y-%m-%d")
        eta_date = datetime.strptime(eta, "%Y-%m-%d")
        transit_days = max((eta_date - etd_date).days, 1)
    except Exception:
        transit_days = 7

    # Cargo info
    cargo_value = payload.get("cargo_value") or payload.get("shipment_value") or 0

    # Parties – current input uses plain strings, overview/state may enrich later
    shipper = payload.get("shipper") or ""
    consignee = payload.get("consignee") or ""

    shipment_id = payload.get("shipment_id") or f"SH-{pol}-{pod}-{int(datetime.now().timestamp())}"

    return {
        "shipment_id": shipment_id,
        "origin": {
            "code": pol,
            "city": get_port_city(pol),
            "country": get_port_country(pol),
        },
        "destination": {
            "code": pod,
            "city": get_port_city(pod),
            "country": get_port_country(pod),
        },
        "transport_mode": payload.get("transport_mode", "Air"),
        "eta_range": format_date_range(etd, eta),
        "eta_duration": f"{transit_days} days",
        # Risk surface – best‑effort using existing numeric hints
        "confidence": 85,
        "risk_level": str(payload.get("risk_level", "LOW")).upper(),
        "expected_loss": f"${int((cargo_value or 0) * 0.02):,}" if cargo_value else "$0",
        "eta_reliability": "92%",
        "active_alerts": 0,
        "route": {
            "departure_date": format_date(etd),
            "departure_time": "14:30 UTC+7",
            "arrival_date": format_date_range(etd, eta),
            "transit_duration": f"{transit_days} days",
            "incoterms": payload.get("incoterm", "FOB"),
        },
        "cargo": {
            "commodity": payload.get("cargo_type", "General"),
            "value": f"${cargo_value:,.0f}" if cargo_value else "$0",
            "weight": f"{payload.get('gross_weight') or payload.get('weight') or 0} kg",
            "packaging": payload.get("packaging", "Palletized"),
            "hs_code": payload.get("hs_code", "N/A"),
        },
        "parties": {
            "shipper": {
                "name": shipper or "N/A",
                "location": "",
            },
            "consignee": {
                "name": consignee or "N/A",
                "location": "",
            },
            "carrier": {
                "name": payload.get("carrier") or "Carrier TBD",
                "rating": "N/A",
            },
        },
    }


def get_port_city(port_code: str) -> str:
    """Get city name from port code"""
    port_map = {
        "SGN": "Ho Chi Minh City",
        "VNSGN": "Ho Chi Minh City",
        "LAX": "Los Angeles",
        "USLAX": "Los Angeles",
        "SHA": "Shanghai",
        "CNSHA": "Shanghai",
        "SIN": "Singapore",
        "SGSIN": "Singapore",
        "HKG": "Hong Kong",
        "HKHKG": "Hong Kong",
    }
    return port_map.get(port_code.upper(), "Unknown")


def get_port_country(port_code: str) -> str:
    """Get country from port code"""
    port_map = {
        "SGN": "Vietnam",
        "VNSGN": "Vietnam",
        "LAX": "USA",
        "USLAX": "USA",
        "SHA": "China",
        "CNSHA": "China",
        "SIN": "Singapore",
        "SGSIN": "Singapore",
        "HKG": "Hong Kong",
        "HKHKG": "Hong Kong",
    }
    return port_map.get(port_code.upper(), "Unknown")


def format_date(date_str: str) -> str:
    """Format date string to readable format"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%b %d, %Y")
    except:
        return date_str


def format_date_range(etd: str, eta: str) -> str:
    """Format date range"""
    try:
        etd_obj = datetime.strptime(etd, "%Y-%m-%d")
        eta_obj = datetime.strptime(eta, "%Y-%m-%d")
        return f"{etd_obj.strftime('%b %d')}-{eta_obj.strftime('%d, %Y')}"
    except:
        return f"{etd} - {eta}"


@router.get("/shipments/{shipment_id}/summary", response_class=HTMLResponse)
async def shipment_summary_page(request: Request, shipment_id: str, react: str = None):
    """
    Shipment Summary Page - React or Vanilla JS implementation
    Use ?react=1 to force React app, otherwise uses React by default
    """
    from pathlib import Path
    
    # Serve React app from dist/index.html
    dist_index = Path(__file__).parent.parent.parent / "dist" / "index.html"
    if dist_index.exists():
        with open(dist_index, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    
    # Fallback to Vanilla JS template if React build not available
    shipment_data = get_shipment_data_from_memory(shipment_id)
    return templates.TemplateResponse(
        "shipment/summary.html",
        {
            "request": request,
            "shipment_data": json.dumps(shipment_data),
            "shipment_data_python": shipment_data,
        }
    )


@router.get("/shipments/summary", response_class=HTMLResponse)
async def shipment_summary_page_default(request: Request, react: str = None):
    """
    Shipment Summary Page - Default (no shipment_id)
    Serves React app from dist/index.html
    """
    from pathlib import Path
    
    # Serve React app from dist/index.html
    dist_index = Path(__file__).parent.parent.parent / "dist" / "index.html"
    if dist_index.exists():
        with open(dist_index, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    
    # Fallback to Vanilla JS template
    shipment_data = get_shipment_data_from_memory()
    return templates.TemplateResponse(
        "shipment/summary.html",
        {
            "request": request,
            "shipment_data": json.dumps(shipment_data),
            "shipment_data_python": shipment_data,
        }
    )


@router.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    """
    Results Page - Serves React Results app from dist/index.html
    This is where users are redirected after running analysis
    """
    from pathlib import Path
    
    # Serve React app from dist/index.html
    dist_index = Path(__file__).parent.parent.parent / "dist" / "index.html"
    if dist_index.exists():
        with open(dist_index, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    
    # Fallback HTML if React build not available
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>RISKCAST Results - Build Required</title>
        <style>
            body { 
                font-family: system-ui, sans-serif; 
                background: linear-gradient(135deg, #0a1628 0%, #1a2942 100%);
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }
            .container { text-align: center; padding: 40px; }
            code { 
                background: rgba(255,255,255,0.1); 
                padding: 8px 16px; 
                border-radius: 8px;
                display: block;
                margin: 16px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚠️ React Build Required</h1>
            <p>Please build the React app:</p>
            <code>cd riskcast-v16-main && npm run build</code>
            <p>Then restart the server.</p>
        </div>
    </body>
    </html>
    """)

