"""
RISKCAST API v1 - Risk Routes
Risk analysis endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.services.risk_service import run_risk_engine_v14
from app.core.engine_v2.risk_pipeline import RiskPipeline
from app.core.scenario_engine.simulation_engine import SimulationEngine
from app.core.scenario_engine.delta_engine import DeltaEngine
from app.core.scenario_engine.scenario_store import ScenarioStore
from app.core.scenario_engine.presets import ScenarioPresets
from app.core.engine_v2.llm_reasoner import LLMReasoner
from fastapi.responses import Response, StreamingResponse  # type: ignore
from fastapi import Request

router = APIRouter()

# Initialize scenario engines
simulation_engine = SimulationEngine()
delta_engine = DeltaEngine()
scenario_store = ScenarioStore()
llm_reasoner = LLMReasoner(use_llm=True)


class ShipmentModel(BaseModel):
    """Shipment model for risk analysis"""
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
    distance: Optional[float] = None
    route_type: Optional[str] = None
    carrier_rating: Optional[float] = None
    weather_risk: Optional[float] = None
    port_risk: Optional[float] = None
    container_match: Optional[float] = None
    shipment_value: Optional[float] = None
    use_fuzzy: bool = False
    use_forecast: bool = False
    use_mc: bool = False
    use_var: bool = False
    # Climate fields
    ENSO_index: float = 0.0
    typhoon_frequency: float = 0.5
    sst_anomaly: float = 0.0
    port_climate_stress: float = 5.0
    climate_volatility_index: float = 5.0
    climate_tail_event_probability: float = 0.05
    ESG_score: float = 50.0
    climate_resilience: float = 5.0
    green_packaging: float = 5.0
    # Buyer-seller fields
    buyer: Optional[Dict[str, Any]] = None
    seller: Optional[Dict[str, Any]] = None
    priority_profile: Optional[str] = None
    priority_weights: Optional[Dict[str, int]] = None
    # Multi-language support
    language: Optional[str] = "en"  # Language code: vi, en, zh


@router.post("/risk/analyze")
async def analyze_risk(shipment: ShipmentModel):
    """
    Analyze shipment risk
    """
    try:
        shipment_dict = shipment.model_dump()
        result = run_risk_engine_v14(shipment_dict)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")


@router.post("/risk/evaluate")
async def risk_evaluate(request: Request):
    """
    Lightweight risk evaluation used by Results v38.
    Accepts the stored RISKCAST_STATE payload and returns computed risk metrics.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    def _num(val, default=0.0):
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    risk = payload.get("risk", {}) if isinstance(payload, dict) else {}
    kpi = payload.get("kpi", {}) if isinstance(payload, dict) else {}
    transport = payload.get("transport", {}) if isinstance(payload, dict) else {}

    weather_risk = _num(risk.get("weatherImpact") or kpi.get("weatherImpact"), 10)
    congestion_risk = _num(risk.get("congestionScore") or kpi.get("congestionIndex"), 10)
    carrier_risk = 100 - _num(transport.get("reliability"), 50)
    macro_risk = _num(risk.get("politicalScore") or kpi.get("politicalScore"), 10)

    risk_score_7d = max(0, weather_risk + congestion_risk + carrier_risk + macro_risk)
    eta_confidence = max(0, 100 - (risk_score_7d * 0.6))
    delay_prob = max(0, min(100, risk_score_7d * 0.75))

    # Simple chart scaffold
    labels = ["D1", "D2", "D3", "D4", "D5", "D6", "D7"]
    values = [max(2, min(95, risk_score_7d * (0.4 + i * 0.05))) for i in range(len(labels))]

    return {
        "status": "ok",
        "eta_confidence": round(eta_confidence, 2),
        "risk_score_7d": round(risk_score_7d, 2),
        "delay_prob": round(delay_prob, 2),
        "insights": [
            f"Weather risk: {weather_risk:.1f}",
            f"Congestion risk: {congestion_risk:.1f}",
            f"Carrier schedule gap: {carrier_risk:.1f}",
            f"Macro risk: {macro_risk:.1f}",
        ],
        "chart_data": {
            "labels": labels,
            "values": values,
        },
        "model": "Risk Engine Evaluate v1",
    }


@router.post("/risk/v2/analyze")
async def analyze_risk_v2(shipment: ShipmentModel):
    """
    Analyze shipment risk using Engine v2 (FAHP + TOPSIS + Climate + Network + LLM)
    
    Supports multi-language (vi/en/zh) and auto-detects region based on route.
    
    ARCHITECTURE: ENGINE-FIRST
    - This is the ONLY endpoint that executes the risk engine
    - Engine result is stored in shared backend state (LAST_RESULT_V2)
    - Results page reads from shared state via GET /results/data
    - No duplicate execution, no UI-side computation
    
    Request Body:
    - All ShipmentModel fields
    - language: Optional language code (vi, en, zh) - default: "en"
    
    Returns unified risk score with:
    - Risk score (0-100)
    - Risk level (Low/Medium/High/Critical)
    - Confidence score
    - Risk profile with impact matrix
    - Key drivers
    - Recommendations
    - LLM-generated reasoning (region-aware, in specified language)
    - Region information (detected region and configuration)
    """
    try:
        # Convert to dict
        shipment_dict = shipment.model_dump()
        
        # Get language from shipment data
        language = shipment_dict.get("language", "en")
        
        # Validate language
        valid_languages = ['vi', 'en', 'zh']
        if language not in valid_languages:
            language = 'en'
        
        # Remove language from shipment_dict to avoid processing issues
        shipment_dict.pop("language", None)
        
        # Initialize pipeline
        pipeline = RiskPipeline()
        
        # Run analysis with language support
        result = await pipeline.run(shipment_dict, language=language)
        
        # ============================================================
        # ENGINE-FIRST ARCHITECTURE: Store result in shared backend state
        # ============================================================
        # CRITICAL: Store the complete engine result for Results page
        # Results page reads from this via GET /results/data
        # This ensures Results page ALWAYS renders engine-computed data
        # ============================================================
        try:
            # Import the setter function from engine_state module
            from app.core.engine_state import set_last_result_v2
            
            # Build complete result payload for ResultsOS
            # Include shipment data for UI mapping
            # CRITICAL: Extract pol/pod from route if not provided directly
            route_str = shipment_dict.get("route", "")
            pol_code = shipment_dict.get("pol_code", "")
            pod_code = shipment_dict.get("pod_code", "")
            
            # Extract from route string if pol_code/pod_code not provided
            if not pol_code or not pod_code:
                if "_" in route_str:
                    parts = route_str.split("_")
                    if len(parts) >= 2:
                        pol_code = pol_code or parts[0]
                        pod_code = pod_code or parts[1]
                elif "→" in route_str or "->" in route_str:
                    separator = "→" if "→" in route_str else "->"
                    parts = route_str.split(separator)
                    if len(parts) >= 2:
                        pol_code = pol_code or parts[0].strip()
                        pod_code = pod_code or parts[1].strip()
            
            # Build route display string
            route_display = f"{pol_code} → {pod_code}" if pol_code and pod_code else route_str
            
            complete_result = {
                "shipment": {
                    "id": f"SH-{pol_code}-{pod_code}-{int(__import__('time').time())}" if pol_code and pod_code else f"SH-{int(__import__('time').time())}",
                    "route": route_display,
                    "pol_code": pol_code,
                    "pod_code": pod_code,
                    "origin": pol_code,
                    "destination": pod_code,
                    "mode": shipment_dict.get("transport_mode", ""),
                    "carrier": shipment_dict.get("carrier", ""),
                    "etd": shipment_dict.get("etd", ""),
                    "eta": shipment_dict.get("eta", ""),
                    "transit_time": shipment_dict.get("transit_time", 0),
                    "container": shipment_dict.get("container", ""),
                    "cargo": shipment_dict.get("cargo_type", ""),
                    "incoterm": shipment_dict.get("incoterm", ""),
                    "value": shipment_dict.get("cargo_value", shipment_dict.get("shipment_value", 0)),
                    "cargo_value": shipment_dict.get("cargo_value", shipment_dict.get("shipment_value", 0)),
                },
                "risk_score": result.get("risk_score", 0),
                "overall_risk": result.get("risk_score", 0),
                "risk_level": result.get("risk_level", "Medium"),
                "confidence": result.get("confidence", 0),
                # Build layers from components (engine v2 doesn't return layers directly)
                "layers": _build_layers_from_components(result.get("components", {}), result.get("details", {})),
                "risk_factors": result.get("drivers", []),
                "factors": result.get("drivers", []),
                # Transform recommendations array to object format
                "recommendations": _transform_recommendations(result.get("recommendations", []), result),
                "profile": result.get("profile", {}),
                "matrix": result.get("profile", {}).get("matrix", {}),
                "drivers": result.get("drivers", []),
                "region": result.get("region", {}),
                "details": result.get("details", {}),
                # Extract loss metrics (engine may provide, or calculate from cargo value)
                "loss": result.get("loss") or _calculate_loss_metrics(
                    shipment_dict.get("cargo_value", shipment_dict.get("shipment_value", 0)),
                    result.get("risk_score", 0)
                ),
                "methodology": {
                    "riskAggregation": {
                        "model": "FAHP",
                        "method": "Fuzzy Analytic Hierarchy Process with Monte Carlo simulation"
                    }
                },
                "engine_version": "v2",
                "language": language,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
            
            # Store in shared backend state (authoritative source)
            set_last_result_v2(complete_result)
            
        except ImportError:
            # Fallback: If main.py import fails, log warning but continue
            # This should not happen in production, but graceful degradation
            import logging
            logging.warning("[Engine v2] Failed to store result in shared state - Results page may fall back to storage")
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logging.error(f"[Engine v2] Error storing result in shared state: {e}")
        
        return {
            "status": "success",
            "engine_version": "v2",
            "language": language,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis v2 failed: {str(e)}")


def _build_layers_from_components(components: Dict[str, Any], details: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build layers array from engine v2 components
    ENGINE-FIRST: This is UI mapping only, not computation
    """
    layers = []
    
    # Map components to layer names
    layer_map = {
        "fahp_weighted": "Transport",
        "climate_risk": "Weather",
        "network_risk": "Port",
        "operational_risk": "Carrier"
    }
    
    for key, value in components.items():
        if key in layer_map and value is not None:
            score = float(value) * 100 if value <= 1 else float(value)
            layers.append({
                "name": layer_map[key],
                "score": round(score, 1),
                "contribution": float(value)
            })
    
    # Add additional layers from details if available
    if details.get("fahp_weights"):
        for layer_name, weight in details["fahp_weights"].items():
            if layer_name not in [l["name"] for l in layers]:
                score = float(weight) * 100 if weight <= 1 else float(weight)
                layers.append({
                    "name": layer_name.replace("_", " ").title(),
                    "score": round(score, 1),
                    "contribution": float(weight)
                })
    
    return layers

def _transform_recommendations(recommendations: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform recommendations from engine v2 format to ResultsOS format
    ENGINE-FIRST: This is format transformation only, not computation
    """
    if not recommendations:
        return {}
    
    # If recommendations is already an object, return as-is
    if isinstance(recommendations, dict):
        return recommendations
    
    # If recommendations is an array, transform to object format
    if isinstance(recommendations, list):
        # Extract insurance recommendation if present
        insurance_rec = None
        for rec in recommendations:
            if isinstance(rec, dict) and rec.get("type") == "insurance":
                insurance_rec = rec
                break
        
        # Build recommendations object
        rec_obj = {
            "insurance": insurance_rec or {
                "required": result.get("risk_score", 0) > 60,
                "level": "standard" if result.get("risk_score", 0) > 60 else "optional",
                "threshold": 60,
                "premium": 0
            },
            "providers": [],
            "timing": {},
            "actions": [rec if isinstance(rec, str) else rec.get("text", "") for rec in recommendations[:5]],
            "trace": {
                "version": "v2",
                "dominantSignals": result.get("drivers", [])[:3],
                "triggers": []
            }
        }
        
        return rec_obj
    
    return {}

def _calculate_loss_metrics(cargo_value: float, risk_score: float) -> Dict[str, Any]:
    """
    Calculate loss metrics from cargo value and risk score
    ENGINE-FIRST: This is UI mapping only - actual calculation should be in engine
    For now, use simple estimation based on risk score
    """
    if cargo_value <= 0 or risk_score <= 0:
        return {"p95": 0, "p99": 0, "expectedLoss": 0}
    
    # Simple estimation: expected loss = cargo_value * (risk_score / 100) * 0.3
    expected_loss = cargo_value * (risk_score / 100) * 0.3
    var95 = expected_loss * 1.5  # VaR 95% = 1.5x expected
    cvar95 = expected_loss * 1.8  # CVaR 95% = 1.8x expected
    
    return {
        "p95": round(var95, 2),
        "p99": round(cvar95, 2),
        "expectedLoss": round(expected_loss, 2),
        "tailContribution": 15.0 if risk_score < 60 else 28.5
    }

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


# ===============================================================
# SCENARIO SIMULATION API ROUTES
# ===============================================================

class SimulationRequest(BaseModel):
    """Request model for scenario simulation"""
    baseline_result: Dict[str, Any]  # Original risk assessment result
    adjustments: Dict[str, float]  # Adjustment percentages
    original_inputs: Optional[Dict[str, Any]] = None  # Original shipment inputs


@router.post("/risk/v2/simulate")
async def simulate_scenario(request: SimulationRequest):
    """
    Run scenario simulation with adjusted risk factors
    
    Input:
    - baseline_result: Original risk assessment result
    - adjustments: Adjustment dictionary (e.g., {"port_congestion": +0.15, "weather_hazard": +0.25})
    - original_inputs: Optional original shipment inputs
    
    Returns simulation result with new risk score and changes
    """
    try:
        result = await simulation_engine.simulate(
            baseline_result=request.baseline_result,
            adjustments=request.adjustments,
            original_inputs=request.original_inputs
        )
        
        return {
            "status": "success",
            "simulation": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


class DeltaRequest(BaseModel):
    """Request model for delta analysis"""
    baseline: Dict[str, Any]  # Baseline result
    scenario: Dict[str, Any]  # Scenario result


@router.post("/risk/v2/simulation/delta")
async def compute_simulation_delta(request: DeltaRequest):
    """
    Compute delta analysis between baseline and scenario
    
    Returns detailed comparison including:
    - Absolute delta
    - Percentage change
    - Risk level shift
    - Dominant factor changes
    - Mitigation recommendations
    """
    try:
        delta = delta_engine.compute_delta(
            baseline=request.baseline,
            scenario=request.scenario
        )
        
        return {
            "status": "success",
            "delta": delta_engine.delta_to_dict(delta)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delta computation failed: {str(e)}")


class SaveScenarioRequest(BaseModel):
    """Request model for saving scenario"""
    name: str
    adjustments: Dict[str, float]
    result: Optional[Dict[str, Any]] = None
    baseline_score: Optional[float] = None
    description: Optional[str] = None


@router.post("/risk/v2/simulation/save")
async def save_scenario(request: SaveScenarioRequest):
    """Save a scenario configuration"""
    try:
        success = scenario_store.save_scenario(
            name=request.name,
            adjustments=request.adjustments,
            result=request.result,
            baseline_score=request.baseline_score,
            description=request.description
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Scenario name already exists")
        
        return {
            "status": "success",
            "message": f"Scenario '{request.name}' saved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save scenario: {str(e)}")


@router.get("/risk/v2/simulation/load/{name}")
async def load_scenario(name: str):
    """Load a saved scenario by name"""
    try:
        scenario = scenario_store.load_scenario(name)
        
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")
        
        return {
            "status": "success",
            "scenario": scenario
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load scenario: {str(e)}")


@router.get("/risk/v2/simulation/list")
async def list_scenarios():
    """List all saved scenarios"""
    try:
        scenarios = scenario_store.list_scenarios()
        
        return {
            "status": "success",
            "count": len(scenarios),
            "scenarios": scenarios
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list scenarios: {str(e)}")


@router.delete("/risk/v2/simulation/delete/{name}")
async def delete_scenario(name: str):
    """Delete a saved scenario"""
    try:
        success = scenario_store.delete_scenario(name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")
        
        return {
            "status": "success",
            "message": f"Scenario '{name}' deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete scenario: {str(e)}")


@router.get("/risk/v2/simulation/presets")
async def list_presets():
    """List all available preset scenarios"""
    try:
        presets = ScenarioPresets.list_presets()
        
        return {
            "status": "success",
            "count": len(presets),
            "presets": presets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list presets: {str(e)}")


@router.get("/risk/v2/simulation/preset/{name}")
async def get_preset(name: str):
    """Get a specific preset scenario"""
    try:
        preset = ScenarioPresets.get_preset(name)
        
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset '{name}' not found")
        
        return {
            "status": "success",
            "preset": {
                "name": name,
                "description": preset.get("description"),
                "adjustments": preset.get("adjustments", {}),
                "category": preset.get("category"),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preset: {str(e)}")


class ScenarioExplanationRequest(BaseModel):
    """Request model for scenario explanation"""
    baseline: Dict[str, Any]  # Baseline result
    scenario: Dict[str, Any]  # Scenario result
    deltas: Dict[str, Any]  # Delta analysis result


@router.post("/risk/v2/simulation/explain")
async def explain_scenario(request: ScenarioExplanationRequest):
    """
    Generate AI explanation for scenario comparison
    
    Returns explanation with:
    - Summary of changes
    - Key driver changes
    - Impact analysis
    - Recommendations
    """
    try:
        # Compute delta if not provided
        deltas = request.deltas
        if not deltas:
            delta_analysis = delta_engine.compute_delta(
                baseline=request.baseline,
                scenario=request.scenario
            )
            deltas = delta_engine.delta_to_dict(delta_analysis)
        
        # Generate explanation
        explanation = await llm_reasoner.generate_scenario_explanation(
            baseline=request.baseline,
            scenario=request.scenario,
            deltas=deltas
        )
        
        return {
            "status": "success",
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")


# ===============================================================
# PDF REPORT GENERATION
# ===============================================================

class PDFReportRequest(BaseModel):
    """Request model for PDF report generation"""
    risk_score: float
    risk_level: str
    confidence: float
    profile: Dict[str, Any]
    matrix: Dict[str, Any]
    factors: Dict[str, float]
    drivers: List[str]
    recommendations: List[str]
    timeline: Optional[List[Any]] = None
    network: Optional[Dict[str, Any]] = None
    scenario_comparisons: Optional[List[Dict[str, Any]]] = None
    charts: Optional[Dict[str, str]] = None  # Base64 chart images
    route: Optional[str] = None


@router.post("/risk/v2/report/pdf")
async def generate_pdf_report(request: PDFReportRequest):
    """
    Generate enterprise PDF report
    
    Input:
    - Risk assessment data
    - Chart images as base64 strings
    
    Returns:
    - PDF file as downloadable response
    """
    try:
        try:
            from app.core.report.pdf_builder import PDFReportBuilder  # type: ignore
        except ImportError as ie:
            raise HTTPException(status_code=500, detail="PDF generation unavailable: missing reportlab dependency") from ie

        # Initialize PDF builder
        pdf_builder = PDFReportBuilder()
        
        # Prepare report data
        report_data = {
            "risk_score": request.risk_score,
            "risk_level": request.risk_level,
            "confidence": request.confidence,
            "profile": request.profile,
            "matrix": request.matrix,
            "factors": request.factors,
            "drivers": request.drivers or [],
            "recommendations": request.recommendations or [],
            "timeline": request.timeline or [],
            "network": request.network or {},
            "scenario_comparisons": request.scenario_comparisons or [],
            "charts": request.charts or {},
            "route": request.route or "Unknown Route",
        }
        
        # Generate PDF
        pdf_buffer = pdf_builder.generate_report(report_data)
        
        # Create response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=riskcast_report.pdf",
                "Content-Type": "application/pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

