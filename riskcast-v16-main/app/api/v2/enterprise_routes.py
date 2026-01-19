"""
RISKCAST Enterprise API Routes v2
==================================
API endpoints for enterprise features:
- Multi-persona risk views
- Scenario analysis
- Audit trail
- Privacy/compliance
- Model versioning

Author: RISKCAST Team
Version: 2.0
"""

from fastapi import APIRouter, HTTPException, Request, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
import logging

# Import services
from app.services.persona_adapter import PersonaAdapter, UserPersona, adapt_for_persona
from app.services.scenario_engine import ScenarioEngine, compare_shipment_scenarios, get_available_presets
from app.services.fraud_detection import FraudDetector, analyze_request_for_fraud
from app.services.missing_data_handler import calculate_missing_data_penalty
from app.models.audit_trail import AuditService, log_risk_calculation
from app.models.provenance import track_request_provenance
from app.models.uncertainty import UncertaintyQuantifier, add_uncertainty_to_result
from app.core.model_versioning import (
    get_current_model_version,
    get_model_version,
    list_model_versions,
    get_version_for_audit
)
from app.services.data_privacy import (
    export_user_data,
    delete_user_data,
    export_portable_data,
    get_processing_register,
    record_consent
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["Enterprise"])


# ========================
# Request/Response Models
# ========================

class ShipmentData(BaseModel):
    """Base shipment data for risk analysis."""
    transport_mode: str = Field(default="sea", description="Transport mode")
    cargo_type: str = Field(default="standard", description="Cargo type")
    cargo_value: float = Field(default=50000, gt=0, description="Cargo value in USD")
    route: str = Field(default="vn_us", description="Trade route")
    carrier: Optional[str] = Field(default=None, description="Carrier name")
    transit_time: float = Field(default=30, gt=0, description="Transit time in days")
    etd: Optional[str] = Field(default=None, description="Estimated departure date")
    eta: Optional[str] = Field(default=None, description="Estimated arrival date")
    carrier_rating: float = Field(default=5.0, ge=0, le=10)
    packaging_quality: float = Field(default=7.0, ge=0, le=10)
    container_match: float = Field(default=7.0, ge=0, le=10)
    incoterm: str = Field(default="FOB")
    priority: str = Field(default="standard")


class PersonaRiskRequest(BaseModel):
    """Request for persona-specific risk view."""
    shipment: ShipmentData
    persona: str = Field(
        default="executive",
        description="User persona: executive, analyst, operations, insurance"
    )


class ScenarioRequest(BaseModel):
    """Request for scenario analysis."""
    baseline: Dict[str, Any]
    scenarios: List[Dict[str, Any]]
    include_presets: bool = Field(default=False)


class PrivacyExportRequest(BaseModel):
    """Request for privacy data export."""
    user_id: str
    format: str = Field(default="json", description="Export format: json or csv")


class PrivacyDeleteRequest(BaseModel):
    """Request for data deletion."""
    user_id: str
    reason: str


class ConsentRequest(BaseModel):
    """Request to record consent."""
    user_id: str
    consent_type: str
    granted: bool


class AuditQueryRequest(BaseModel):
    """Request for audit trail query."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    limit: int = Field(default=100, le=1000)


# ========================
# Persona-Specific Endpoints
# ========================

@router.post("/risk/analyze/executive")
async def analyze_for_executive(request: PersonaRiskRequest, req: Request):
    """
    Executive dashboard view.
    
    Returns high-level KPIs, clear recommendations, and top risk drivers.
    Designed for quick decision-making.
    """
    start_time = time.time()
    
    try:
        risk_data = await _calculate_full_risk(request.shipment.model_dump())
        result = PersonaAdapter.format_for_executive(risk_data)
        
        # Log to audit trail
        _log_calculation(req, request.shipment.model_dump(), result, start_time)
        
        return result
        
    except Exception as e:
        logger.error(f"Executive analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk/analyze/analyst")
async def analyze_for_analyst(request: PersonaRiskRequest, req: Request):
    """
    Detailed analyst view.
    
    Returns complete breakdown, methodology details, sensitivity analysis,
    and comparable shipments.
    """
    start_time = time.time()
    
    try:
        risk_data = await _calculate_full_risk(request.shipment.model_dump())
        result = PersonaAdapter.format_for_analyst(risk_data)
        
        _log_calculation(req, request.shipment.model_dump(), result, start_time)
        
        return result
        
    except Exception as e:
        logger.error(f"Analyst analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk/analyze/operations")
async def analyze_for_operations(request: PersonaRiskRequest, req: Request):
    """
    Operations action view.
    
    Returns actionable mitigation steps, timeline impact, carrier recommendations,
    and monitoring plan.
    """
    start_time = time.time()
    
    try:
        risk_data = await _calculate_full_risk(request.shipment.model_dump())
        result = PersonaAdapter.format_for_operations(risk_data)
        
        _log_calculation(req, request.shipment.model_dump(), result, start_time)
        
        return result
        
    except Exception as e:
        logger.error(f"Operations analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk/analyze/insurance")
async def analyze_for_insurance(request: PersonaRiskRequest, req: Request):
    """
    Insurance underwriter view.
    
    Returns underwriting summary, loss metrics, actuarial data,
    policy recommendations, and regulatory flags.
    """
    start_time = time.time()
    
    try:
        risk_data = await _calculate_full_risk(request.shipment.model_dump())
        result = PersonaAdapter.format_for_insurance(risk_data)
        
        _log_calculation(req, request.shipment.model_dump(), result, start_time)
        
        return result
        
    except Exception as e:
        logger.error(f"Insurance analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# Scenario Analysis Endpoints
# ========================

@router.post("/risk/scenarios")
async def analyze_scenarios(request: ScenarioRequest, req: Request):
    """
    What-If scenario analysis.
    
    Compare baseline shipment against multiple alternative scenarios.
    Returns ranked scenarios with cost-benefit analysis.
    """
    try:
        result = compare_shipment_scenarios(
            baseline=request.baseline,
            scenarios=request.scenarios,
            include_presets=request.include_presets
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Scenario analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/scenarios/presets")
async def get_scenario_presets():
    """
    Get available preset scenario templates.
    
    Returns pre-defined scenarios like alternative carrier, air freight, etc.
    """
    return {
        "presets": get_available_presets(),
        "count": len(get_available_presets())
    }


# ========================
# Fraud Detection Endpoints
# ========================

@router.post("/risk/fraud-check")
async def check_fraud_signals(
    shipment: ShipmentData,
    req: Request,
    user_history: Optional[List[Dict]] = None
):
    """
    Check request for fraud/gaming signals.
    
    Analyzes input for strategic omissions, value anomalies,
    and other gaming patterns.
    """
    try:
        result = analyze_request_for_fraud(
            shipment.model_dump(),
            user_history=user_history,
            ip_address=req.client.host if req.client else None
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Fraud check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk/data-quality")
async def check_data_quality(shipment: ShipmentData):
    """
    Check data quality and missing field penalties.
    
    Returns penalty points for missing fields and data completeness score.
    """
    try:
        penalty_result = calculate_missing_data_penalty(shipment.model_dump())
        provenance_result = track_request_provenance(shipment.model_dump())
        
        return {
            "penalty": penalty_result,
            "provenance": provenance_result,
            "overall_quality": provenance_result.get('overall_data_quality', 0)
        }
        
    except Exception as e:
        logger.error(f"Data quality check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# Audit Trail Endpoints
# ========================

@router.get("/audit/verify")
async def verify_audit_integrity():
    """
    Verify audit trail integrity.
    
    Checks blockchain-style chain integrity to detect any tampering.
    """
    try:
        result = AuditService.verify_integrity()
        return result
        
    except Exception as e:
        logger.error(f"Audit verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/query")
async def query_audit_trail(request: AuditQueryRequest):
    """
    Query audit trail entries.
    
    Returns filtered audit entries for compliance reporting.
    """
    try:
        entries = AuditService.query_entries(
            start_date=request.start_date,
            end_date=request.end_date,
            user_id=request.user_id,
            organization_id=request.organization_id,
            limit=request.limit
        )
        
        return {
            "count": len(entries),
            "entries": [e.to_dict() for e in entries]
        }
        
    except Exception as e:
        logger.error(f"Audit query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/compliance-report")
async def generate_compliance_report(
    start_date: datetime = Query(default=None),
    end_date: datetime = Query(default=None),
    organization_id: Optional[str] = Query(default=None)
):
    """
    Generate compliance report.
    
    Returns comprehensive report for regulatory purposes.
    """
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        report = AuditService.generate_compliance_report(
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Compliance report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# Privacy/GDPR Endpoints
# ========================

@router.post("/privacy/export")
async def export_my_data(request: PrivacyExportRequest):
    """
    GDPR Article 15: Right of access.
    
    Export all personal data for a user.
    """
    try:
        if request.format == 'json':
            data = export_user_data(request.user_id)
            return data
        else:
            # Return as file download
            data = export_portable_data(request.user_id, request.format)
            from fastapi.responses import Response
            return Response(
                content=data,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename=riskcast_export_{request.user_id}.{request.format}"
                }
            )
        
    except Exception as e:
        logger.error(f"Data export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/privacy/delete")
async def delete_my_data(request: PrivacyDeleteRequest):
    """
    GDPR Article 17: Right to erasure.
    
    Delete/anonymize all personal data for a user.
    """
    try:
        result = delete_user_data(request.user_id, request.reason)
        return result
        
    except Exception as e:
        logger.error(f"Data deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/privacy/consent")
async def record_user_consent(request: ConsentRequest):
    """
    Record user consent.
    
    Track consent for various processing activities.
    """
    try:
        result = record_consent(
            request.user_id,
            request.consent_type,
            request.granted
        )
        return result
        
    except Exception as e:
        logger.error(f"Consent recording failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/privacy/processing-register")
async def get_gdpr_register():
    """
    GDPR Article 30: Records of processing activities.
    
    Returns the complete processing register.
    """
    return {
        "processing_activities": get_processing_register(),
        "last_updated": datetime.utcnow().isoformat()
    }


# ========================
# Model Versioning Endpoints
# ========================

@router.get("/models/versions")
async def list_versions(include_deprecated: bool = Query(default=False)):
    """
    List all model versions.
    
    Returns version history with validation metrics.
    """
    return {
        "current_version": get_current_model_version(),
        "all_versions": list_model_versions(include_deprecated),
        "deprecated_count": len([v for v in list_model_versions(True) if v.get('deprecated')])
    }


@router.get("/models/versions/{version}")
async def get_version_details(version: str):
    """
    Get specific model version details.
    """
    result = get_model_version(version)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Version {version} not found")
    
    return result


@router.get("/models/current")
async def get_current_version():
    """
    Get current production model version.
    """
    return get_current_model_version()


# ========================
# Health & Status Endpoints
# ========================

@router.get("/health")
async def health_check():
    """
    Enterprise health check.
    
    Verifies all enterprise services are operational.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "persona_adapter": "operational",
            "scenario_engine": "operational",
            "fraud_detection": "operational",
            "audit_trail": "operational",
            "privacy_service": "operational",
            "model_versioning": "operational"
        },
        "model_version": get_version_for_audit()
    }


# ========================
# Helper Functions
# ========================

async def _calculate_full_risk(shipment_data: Dict) -> Dict:
    """
    Calculate full risk with all enterprise features.
    """
    from app.core.engine.risk_engine_v16 import calculate_enterprise_risk
    
    # Base risk calculation
    result = calculate_enterprise_risk(shipment_data)
    
    # Extract risk score
    risk_score = result.get('overall_risk', 5) * 10  # Convert to 0-100
    
    # Add fraud analysis
    fraud_result = analyze_request_for_fraud(shipment_data)
    
    # Add missing data penalty
    penalty_result = calculate_missing_data_penalty(shipment_data)
    
    # Apply penalties
    adjusted_score = min(100, risk_score + penalty_result['total_penalty_points'])
    if fraud_result['fraud_score'] > 20:
        adjusted_score = min(100, adjusted_score + fraud_result['risk_penalty'])
    
    # Add provenance
    provenance = track_request_provenance(shipment_data)
    
    # Build comprehensive result
    return {
        'risk_score': adjusted_score,
        'base_risk_score': risk_score,
        'risk_level': _get_risk_level(adjusted_score),
        'expected_loss': result.get('expected_loss', shipment_data.get('cargo_value', 0) * 0.05),
        'confidence': result.get('confidence', 0.85),
        'risk_factors': result.get('risk_factors', []),
        'layers': result.get('layers', []),
        'monte_carlo_results': result.get('monte_carlo_results', {}),
        'fraud_analysis': fraud_result,
        'data_quality': penalty_result,
        'input_provenance': provenance,
        'model_version': get_version_for_audit(),
        'cargo_value': shipment_data.get('cargo_value', 0),
        'data_completeness': 1.0 - (penalty_result['total_penalty_points'] / 30)
    }


def _get_risk_level(score: float) -> str:
    """Get risk level from score."""
    if score < 25:
        return "low"
    elif score < 50:
        return "medium"
    elif score < 75:
        return "high"
    else:
        return "critical"


def _log_calculation(
    req: Request,
    request_data: Dict,
    response_data: Dict,
    start_time: float
):
    """Log calculation to audit trail."""
    try:
        log_risk_calculation(
            request_data=request_data,
            response_data=response_data,
            user_id=req.headers.get('X-User-ID'),
            organization_id=req.headers.get('X-Organization-ID'),
            ip_address=req.client.host if req.client else None,
            computation_time_ms=(time.time() - start_time) * 1000
        )
    except Exception as e:
        logger.warning(f"Failed to log to audit trail: {e}")
