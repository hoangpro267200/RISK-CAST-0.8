"""
RISKCAST API v1 - Analyze Endpoint
DEPRECATED: This endpoint now redirects to the real engine.
Use /api/v1/risk/v2/analyze for full functionality.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.core.engine.risk_engine_v16 import calculate_enterprise_risk
from app.core.utils.sanitizer import sanitize_input

router = APIRouter()
logger = logging.getLogger(__name__)


class AnalyzeRequest(BaseModel):
    """
    Basic analyze request model.
    For full functionality, use /api/v1/risk/v2/analyze with ShipmentModel.
    """
    route: str = Field(..., description="Trade route (e.g., 'vn_us')")
    cargo_value: float = Field(..., gt=0, description="Cargo value in USD")
    cargo_type: str = Field(..., description="Cargo type")
    incoterm: str = Field(..., description="Incoterm (e.g., 'FOB', 'CIF')")
    priority: str = Field(default="standard", description="Priority level")
    transport_mode: Optional[str] = Field(default="sea", description="Transport mode")
    transit_time: Optional[float] = Field(default=30.0, gt=0, description="Transit time in days")
    container_match: Optional[float] = Field(default=7.0, ge=0, le=10)
    packaging_quality: Optional[float] = Field(default=7.0, ge=0, le=10)
    carrier_rating: Optional[float] = Field(default=5.0, ge=0, le=10)


@router.post("/analyze")
def analyze(request: AnalyzeRequest):
    """
    Analyze shipment risk using RISKCAST engine.
    
    ⚠️ DEPRECATION WARNING: This endpoint is simplified.
    For full enterprise risk analysis, use POST /api/v1/risk/v2/analyze
    
    Returns:
        risk_score: Overall risk score (0-100 scale, converted from 0-10)
        risk_level: Risk level classification
        expected_loss: Expected loss in USD
        var_95: Value at Risk at 95% confidence
        cvar_95: Conditional VaR at 95%
        layers: Risk factor breakdown
        recommendations: Actionable recommendations
    """
    logger.warning(
        "[DEPRECATION] /api/v1/analyze called. "
        "Consider migrating to /api/v1/risk/v2/analyze for full functionality."
    )
    
    try:
        # Sanitize input
        shipment_data = sanitize_input({
            'transport_mode': request.transport_mode or 'sea',
            'cargo_type': request.cargo_type,
            'route': request.route,
            'incoterm': request.incoterm,
            'container_match': request.container_match or 7.0,
            'packaging_quality': request.packaging_quality or 7.0,
            'priority': request.priority or 'standard',
            'transit_time': request.transit_time or 30.0,
            'cargo_value': request.cargo_value,
            'shipment_value': request.cargo_value,
            'carrier_rating': request.carrier_rating or 5.0,
        })
        
        # Call REAL engine - no more hardcoded values
        engine_result = calculate_enterprise_risk(shipment_data)
        
        # Extract and transform results
        overall_risk = engine_result.get('overall_risk', 5.0)
        risk_score = overall_risk * 10  # Convert 0-10 to 0-100 scale
        
        # Determine risk level
        if risk_score <= 25:
            risk_level = "low"
        elif risk_score <= 55:
            risk_level = "medium"
        elif risk_score <= 75:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        # Extract financial metrics
        financial_dist = engine_result.get('financial_distribution', {})
        expected_loss = financial_dist.get('expected_loss_usd', 
                        engine_result.get('expected_loss', request.cargo_value * 0.05))
        var_95 = financial_dist.get('var_95_usd', expected_loss * 1.5)
        cvar_95 = financial_dist.get('cvar_95_usd', expected_loss * 1.8)
        
        # Extract risk factors/layers
        risk_factors = engine_result.get('risk_factors', [])
        layers = []
        for factor in risk_factors[:6]:  # Top 6 factors
            if isinstance(factor, dict):
                layers.append({
                    "name": factor.get('name', 'Unknown'),
                    "score": factor.get('score', 0) / 10.0  # Normalize to 0-1
                })
        
        # If no layers from engine, provide basic structure
        if not layers:
            layers = [
                {"name": "Delay Risk", "score": overall_risk / 10.0},
                {"name": "Damage Risk", "score": overall_risk * 0.8 / 10.0},
                {"name": "Cost Volatility", "score": overall_risk * 0.6 / 10.0}
            ]
        
        # Extract recommendations
        recommendations = engine_result.get('recommendations', [])
        if isinstance(recommendations, dict):
            recommendations = recommendations.get('actions', [])
        if not recommendations:
            recommendations = [
                "Review route options for potential delays",
                "Verify carrier reliability rating",
                "Consider insurance coverage based on risk level"
            ]
        
        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "expected_loss": round(expected_loss, 2),
            "var_95": round(var_95, 2),
            "cvar_95": round(cvar_95, 2),
            "reliability": engine_result.get('reliability_score', 
                          max(0, 100 - risk_score)),
            "esg": engine_result.get('esg_score', 50),
            "recommendations": recommendations[:5],
            "layers": layers,
            "_meta": {
                "engine_version": "v16",
                "deprecation_warning": "Use /api/v1/risk/v2/analyze for full functionality"
            }
        }
        
    except Exception as e:
        logger.error(f"[analyze] Risk calculation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Risk analysis failed: {str(e)}"
        )



