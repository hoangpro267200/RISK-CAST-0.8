"""
Fraud Detection API Endpoints

Provides ML-powered anomaly detection and fraud detection capabilities.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.ml.anomaly_detection import fraud_service, AnomalyResult, AnomalyType
from app.database import get_db

import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Fraud Detection"])


class ClaimFraudRequest(BaseModel):
    """Request for claim fraud detection."""
    claim_id: str
    claim: Dict = Field(..., description="Claim data")
    policy: Dict = Field(..., description="Associated policy data")


class FraudDetectionResponse(BaseModel):
    """Response from fraud detection."""
    claim_id: str
    is_fraud_suspect: bool
    fraud_score: float = Field(..., ge=0.0, le=1.0, description="0-1, higher = more suspicious")
    anomaly_type: Optional[str]
    confidence: float
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, or CRITICAL")
    explanation: str
    contributing_factors: List[str]
    recommended_actions: List[str]
    metadata: Dict
    assessed_at: str


class TrainingRequest(BaseModel):
    """Request to train fraud detection models."""
    force_retrain: bool = Field(False, description="Force retraining even if models exist")


class ModelStatusResponse(BaseModel):
    """Model status response."""
    is_trained: bool
    use_autoencoder: bool
    models_available: List[str]
    last_trained: Optional[str]
    statistics: Dict


@router.post("/fraud/detect", response_model=FraudDetectionResponse)
async def detect_claim_fraud(
    request: ClaimFraudRequest,
    db = Depends(get_db)
):
    """
    Detect potential fraud in a claim.
    
    Uses ensemble ML approach with Isolation Forest and Autoencoder
    to identify suspicious patterns.
    
    ## Request Body
    
    ```json
    {
        "claim_id": "CLM-123",
        "claim": {
            "claimed_amount": 95000,
            "loss_date": "2026-01-20",
            "filed_at": "2026-01-21T10:00:00Z",
            "loss_type": "CARGO_LOSS",
            "customer_previous_claims": 2
        },
        "policy": {
            "coverage_limit": 100000,
            "cargo_value_usd": 100000,
            "effective_from": "2026-01-19",
            "total_premium_usd": 850
        }
    }
    ```
    
    ## Response
    
    ```json
    {
        "claim_id": "CLM-123",
        "is_fraud_suspect": true,
        "fraud_score": 0.87,
        "anomaly_type": "fraud_suspect",
        "confidence": 0.92,
        "risk_level": "HIGH",
        "explanation": "Fraud risk: HIGH. Claim amount is 95% of coverage (very high); Claim filed shortly after policy inception",
        "contributing_factors": [
            "claim_coverage_ratio",
            "days_since_inception",
            "previous_claims"
        ],
        "recommended_actions": [
            "Manual review required",
            "Request additional documentation",
            "Investigate claim history"
        ],
        "metadata": {
            "isolation_forest_score": 0.89,
            "autoencoder_score": 0.85,
            "ensemble": true
        },
        "assessed_at": "2026-01-24T22:30:00Z"
    }
    ```
    
    ## Risk Levels
    
    - **LOW** (0.0-0.3): Normal claim, low fraud risk
    - **MEDIUM** (0.3-0.5): Some unusual patterns, monitor
    - **HIGH** (0.5-0.8): Significant fraud indicators, manual review recommended
    - **CRITICAL** (0.8-1.0): Strong fraud suspicion, immediate investigation required
    
    ## Common Fraud Indicators
    
    1. **Claim-to-Coverage Ratio**: Very high claims (>80% of coverage)
    2. **Timing**: Claims filed shortly after policy inception (<7 days)
    3. **Reporting Delay**: Unusual time between loss and reporting
    4. **Frequency**: Multiple previous claims from same customer
    5. **Pattern Deviation**: Statistical outliers in claim characteristics
    """
    try:
        # Run fraud detection
        result: AnomalyResult = await fraud_service.detect_fraud(
            request.claim,
            request.policy
        )
        
        # Determine risk level
        if result.anomaly_score >= 0.8:
            risk_level = "CRITICAL"
        elif result.anomaly_score >= 0.5:
            risk_level = "HIGH"
        elif result.anomaly_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Generate recommended actions
        recommended_actions = _generate_recommendations(result, risk_level)
        
        # Log assessment
        logger.info(
            "Fraud detection completed",
            claim_id=request.claim_id,
            fraud_score=result.anomaly_score,
            risk_level=risk_level,
            is_fraud_suspect=result.is_anomaly
        )
        
        return FraudDetectionResponse(
            claim_id=request.claim_id,
            is_fraud_suspect=result.is_anomaly,
            fraud_score=result.anomaly_score,
            anomaly_type=result.anomaly_type.value if result.anomaly_type else None,
            confidence=result.confidence,
            risk_level=risk_level,
            explanation=result.explanation,
            contributing_factors=result.features_contributing,
            recommended_actions=recommended_actions,
            metadata=result.metadata,
            assessed_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Fraud detection error: {e}", claim_id=request.claim_id)
        raise HTTPException(
            status_code=500,
            detail=f"Fraud detection failed: {str(e)}"
        )


@router.post("/fraud/train")
async def train_fraud_models(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    Train fraud detection models on historical data.
    
    This endpoint triggers background training of the ML models
    on historical claims data.
    
    **Note:** Training can take several minutes depending on data size.
    
    ## Request Body
    
    ```json
    {
        "force_retrain": false
    }
    ```
    
    ## Response
    
    ```json
    {
        "status": "training_started",
        "message": "Fraud detection models training initiated",
        "estimated_duration": "5-10 minutes"
    }
    ```
    """
    # Check if already trained and not forcing retrain
    if fraud_service.is_trained and not request.force_retrain:
        return {
            "status": "already_trained",
            "message": "Models are already trained. Use force_retrain=true to retrain."
        }
    
    # Start training in background
    background_tasks.add_task(_train_models_background)
    
    logger.info("Fraud detection training initiated", force_retrain=request.force_retrain)
    
    return {
        "status": "training_started",
        "message": "Fraud detection models training initiated",
        "estimated_duration": "5-10 minutes"
    }


@router.get("/fraud/status", response_model=ModelStatusResponse)
async def get_fraud_detection_status():
    """
    Get fraud detection models status.
    
    Returns information about model training status and availability.
    
    ## Response
    
    ```json
    {
        "is_trained": true,
        "use_autoencoder": true,
        "models_available": [
            "isolation_forest",
            "autoencoder"
        ],
        "last_trained": "2026-01-24T20:00:00Z",
        "statistics": {
            "isolation_forest_features": 6,
            "autoencoder_encoding_dim": 8
        }
    }
    ```
    """
    models_available = []
    
    if fraud_service.isolation_forest.model is not None:
        models_available.append("isolation_forest")
    
    if fraud_service.use_autoencoder and fraud_service.autoencoder and fraud_service.autoencoder.model is not None:
        models_available.append("autoencoder")
    
    statistics = {
        "isolation_forest_features": len(fraud_service.feature_names),
        "feature_names": fraud_service.feature_names
    }
    
    if fraud_service.use_autoencoder and fraud_service.autoencoder:
        statistics["autoencoder_encoding_dim"] = fraud_service.autoencoder.encoding_dim
        statistics["autoencoder_threshold"] = fraud_service.autoencoder.threshold
    
    return ModelStatusResponse(
        is_trained=fraud_service.is_trained,
        use_autoencoder=fraud_service.use_autoencoder,
        models_available=models_available,
        last_trained=None,  # Would track this in production
        statistics=statistics
    )


def _generate_recommendations(result: AnomalyResult, risk_level: str) -> List[str]:
    """Generate recommended actions based on fraud assessment."""
    recommendations = []
    
    if risk_level == "CRITICAL":
        recommendations.extend([
            "Immediate manual investigation required",
            "Hold claim payment pending review",
            "Request comprehensive documentation",
            "Conduct customer interview",
            "Verify all claim details independently"
        ])
    elif risk_level == "HIGH":
        recommendations.extend([
            "Manual review required",
            "Request additional documentation",
            "Verify loss details with third parties",
            "Check customer claim history"
        ])
    elif risk_level == "MEDIUM":
        recommendations.extend([
            "Enhanced documentation review",
            "Verify key claim details",
            "Monitor for pattern consistency"
        ])
    else:
        recommendations.append("Standard claim processing")
    
    # Add specific recommendations based on contributing factors
    if 'claim_coverage_ratio' in result.features_contributing:
        recommendations.append("Verify actual cargo value and loss extent")
    
    if 'days_since_inception' in result.features_contributing:
        recommendations.append("Verify policy inception date and coverage start")
    
    if 'days_to_report' in result.features_contributing:
        recommendations.append("Investigate reason for reporting delay")
    
    if 'previous_claims' in result.features_contributing:
        recommendations.append("Review customer's complete claim history")
    
    return recommendations[:5]  # Limit to top 5


async def _train_models_background():
    """Background task for training fraud detection models."""
    try:
        logger.info("Starting fraud detection model training")
        
        # Train models
        success = await fraud_service.train_models()
        
        if success:
            logger.info("Fraud detection model training completed successfully")
        else:
            logger.error("Fraud detection model training failed")
            
    except Exception as e:
        logger.error(f"Fraud detection training error: {e}")
