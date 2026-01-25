"""
Predictive Analytics API Endpoints

Provides ML-powered predictions for loss, claims, and market trends.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime
import pandas as pd

from app.ml.predictive_models import (
    loss_model,
    claim_model,
    market_predictor,
    PremiumOptimizer,
    PredictionResult
)
from app.database import get_db

import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Predictive Analytics"])


class LossPredictionRequest(BaseModel):
    """Request for loss prediction."""
    cargo_value_usd: float = Field(..., gt=0)
    container_count: int = Field(..., gt=0)
    transit_days: int = Field(..., gt=0)
    risk_score: float = Field(..., ge=0, le=1)
    weather_risk: float = Field(0.5, ge=0, le=1)
    port_congestion_risk: float = Field(0.3, ge=0, le=1)
    carrier_reliability_score: float = Field(0.8, ge=0, le=1)
    historical_loss_rate: float = Field(0.02, ge=0, le=1)
    cargo_type: Optional[str] = "GENERAL"
    origin_region: Optional[str] = "ASIA"
    destination_region: Optional[str] = "EUROPE"
    coverage_type: Optional[str] = "STANDARD"


class LossPredictionResponse(BaseModel):
    """Response from loss prediction."""
    expected_loss_pct: float
    expected_loss_amount: float
    confidence: float
    lower_bound_pct: float
    upper_bound_pct: float
    risk_level: str
    explanation: str
    feature_importance: Dict[str, float]
    metadata: Dict


class ClaimProbabilityRequest(BaseModel):
    """Request for claim probability."""
    cargo_value_usd: float
    container_count: int
    transit_days: int
    risk_score: float
    weather_risk: float = 0.5
    carrier_reliability_score: float = 0.8
    customer_claim_history: int = 0
    route_historical_claims: float = 0.05


class ClaimProbabilityResponse(BaseModel):
    """Response from claim probability."""
    claim_probability: float
    confidence: float
    risk_assessment: str
    recommended_actions: List[str]


class MarketTrendRequest(BaseModel):
    """Request for market trend prediction."""
    months_ahead: int = Field(6, ge=1, le=12)


class MarketTrendResponse(BaseModel):
    """Response from market trend prediction."""
    predictions: List[Dict]
    summary: Dict
    insights: List[str]


class PremiumOptimizationRequest(BaseModel):
    """Request for premium optimization."""
    policy_data: LossPredictionRequest
    market_rate: float = Field(..., description="Current market rate per mille")
    competitive_rate: Optional[float] = Field(None, description="Competitor rate per mille")


class PremiumOptimizationResponse(BaseModel):
    """Response from premium optimization."""
    recommended_premium: float
    recommended_rate: float
    actuarial_rate: float
    market_rate: float
    confidence: float
    rate_components: Dict
    pricing_factors: Dict
    explanation: str


@router.post("/predict/loss", response_model=LossPredictionResponse)
async def predict_loss(request: LossPredictionRequest):
    """
    Predict expected loss for a shipment/policy.
    
    Uses machine learning to estimate expected loss percentage with
    confidence intervals based on shipment characteristics.
    
    ## Request Body
    
    ```json
    {
        "cargo_value_usd": 100000,
        "container_count": 2,
        "transit_days": 21,
        "risk_score": 0.65,
        "weather_risk": 0.6,
        "port_congestion_risk": 0.3,
        "carrier_reliability_score": 0.85,
        "historical_loss_rate": 0.02,
        "cargo_type": "ELECTRONICS",
        "origin_region": "ASIA",
        "destination_region": "EUROPE"
    }
    ```
    
    ## Response
    
    ```json
    {
        "expected_loss_pct": 0.0235,
        "expected_loss_amount": 2350,
        "confidence": 0.87,
        "lower_bound_pct": 0.015,
        "upper_bound_pct": 0.034,
        "risk_level": "MEDIUM",
        "explanation": "Expected loss: 2.35% (MEDIUM risk). Key factors: weather_risk, risk_score, transit_days",
        "feature_importance": {...}
    }
    ```
    """
    try:
        # Convert request to DataFrame
        data = pd.DataFrame([request.dict()])
        
        # Get prediction
        results = loss_model.predict(data)
        result = results[0]
        
        # Determine risk level
        if result.prediction < 0.02:
            risk_level = "LOW"
        elif result.prediction < 0.05:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Calculate expected loss amount
        expected_loss_amount = result.prediction * request.cargo_value_usd
        
        logger.info(
            "Loss prediction completed",
            expected_loss_pct=result.prediction,
            confidence=result.confidence,
            risk_level=risk_level
        )
        
        return LossPredictionResponse(
            expected_loss_pct=result.prediction,
            expected_loss_amount=expected_loss_amount,
            confidence=result.confidence,
            lower_bound_pct=result.lower_bound,
            upper_bound_pct=result.upper_bound,
            risk_level=risk_level,
            explanation=result.explanation,
            feature_importance=result.feature_importance,
            metadata=result.metadata
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Model not trained or invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Loss prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Loss prediction failed: {str(e)}"
        )


@router.post("/predict/claim-probability", response_model=ClaimProbabilityResponse)
async def predict_claim_probability(request: ClaimProbabilityRequest):
    """
    Predict probability of claim being filed.
    
    Uses machine learning to estimate the likelihood that a policy
    will result in a claim.
    
    ## Request Body
    
    ```json
    {
        "cargo_value_usd": 100000,
        "container_count": 2,
        "transit_days": 21,
        "risk_score": 0.65,
        "weather_risk": 0.6,
        "carrier_reliability_score": 0.85,
        "customer_claim_history": 1,
        "route_historical_claims": 0.08
    }
    ```
    
    ## Response
    
    ```json
    {
        "claim_probability": 0.15,
        "confidence": 0.82,
        "risk_assessment": "MEDIUM - 15% probability of claim",
        "recommended_actions": [
            "Monitor shipment closely",
            "Ensure carrier reliability",
            "Consider additional coverage options"
        ]
    }
    ```
    """
    try:
        # Convert to DataFrame
        data = pd.DataFrame([request.dict()])
        
        # Get prediction
        results = claim_model.predict(data)
        probability, confidence = results[0]
        
        # Risk assessment
        if probability < 0.1:
            risk_assessment = f"LOW - {probability:.1%} probability of claim"
            actions = ["Standard monitoring"]
        elif probability < 0.2:
            risk_assessment = f"MEDIUM - {probability:.1%} probability of claim"
            actions = [
                "Monitor shipment closely",
                "Ensure carrier reliability",
                "Consider additional coverage options"
            ]
        else:
            risk_assessment = f"HIGH - {probability:.1%} probability of claim"
            actions = [
                "Enhanced monitoring required",
                "Verify cargo protection measures",
                "Review carrier selection",
                "Consider premium adjustments"
            ]
        
        logger.info(
            "Claim probability predicted",
            probability=probability,
            confidence=confidence
        )
        
        return ClaimProbabilityResponse(
            claim_probability=probability,
            confidence=confidence,
            risk_assessment=risk_assessment,
            recommended_actions=actions
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Model not trained or invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Claim probability prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Claim probability prediction failed: {str(e)}"
        )


@router.post("/predict/market-trend", response_model=MarketTrendResponse)
async def predict_market_trend(request: MarketTrendRequest):
    """
    Predict market rate trends.
    
    Uses time series analysis to forecast insurance rate trends
    for the upcoming months.
    
    ## Request Body
    
    ```json
    {
        "months_ahead": 6
    }
    ```
    
    ## Response
    
    ```json
    {
        "predictions": [
            {
                "date": "2026-02-24",
                "month": "2026-02",
                "predicted_rate": 0.0082,
                "change_from_current": 0.025,
                "confidence": 0.90,
                "forecast_horizon_months": 1
            },
            ...
        ],
        "summary": {
            "trend": "INCREASING",
            "avg_rate": 0.0085,
            "rate_change": 0.0625
        },
        "insights": [
            "Market rates expected to increase by 6.25% over 6 months",
            "Peak rates anticipated in Q2 2026",
            "Consider locking in current rates"
        ]
    }
    ```
    """
    try:
        # Create sample historical data (in production, fetch from database)
        current_date = datetime.utcnow()
        historical_dates = [current_date - pd.DateOffset(months=i) for i in range(24, 0, -1)]
        
        # Generate sample rates with trend
        base_rate = 0.008
        rates = [base_rate * (1 + 0.002 * i + np.random.normal(0, 0.0005)) for i in range(24)]
        
        current_data = pd.DataFrame({
            'date': historical_dates,
            'avg_rate': rates
        })
        
        # Get predictions
        predictions = market_predictor.predict_rate_trend(
            current_data,
            months_ahead=request.months_ahead
        )
        
        # Calculate summary
        current_rate = rates[-1]
        future_rates = [p['predicted_rate'] for p in predictions]
        avg_future_rate = np.mean(future_rates)
        rate_change = (avg_future_rate - current_rate) / current_rate
        
        if rate_change > 0.05:
            trend = "INCREASING"
        elif rate_change < -0.05:
            trend = "DECREASING"
        else:
            trend = "STABLE"
        
        summary = {
            "current_rate": current_rate,
            "avg_future_rate": avg_future_rate,
            "rate_change_pct": rate_change,
            "trend": trend
        }
        
        # Generate insights
        insights = []
        if trend == "INCREASING":
            insights.append(f"Market rates expected to increase by {rate_change:.1%} over {request.months_ahead} months")
            insights.append("Consider locking in current rates")
        elif trend == "DECREASING":
            insights.append(f"Market rates expected to decrease by {abs(rate_change):.1%}")
            insights.append("Rates may be more favorable in coming months")
        else:
            insights.append("Market rates expected to remain stable")
        
        # Find peak/trough
        max_rate = max(future_rates)
        max_month = predictions[future_rates.index(max_rate)]['month']
        insights.append(f"Peak rates anticipated around {max_month}")
        
        logger.info(
            "Market trend predicted",
            months_ahead=request.months_ahead,
            trend=trend,
            rate_change=rate_change
        )
        
        return MarketTrendResponse(
            predictions=predictions,
            summary=summary,
            insights=insights
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Model not trained or invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Market trend prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Market trend prediction failed: {str(e)}"
        )


@router.post("/optimize/premium", response_model=PremiumOptimizationResponse)
async def optimize_premium(request: PremiumOptimizationRequest):
    """
    Optimize premium pricing.
    
    Combines loss predictions, claim probabilities, and market conditions
    to recommend optimal premium pricing.
    
    ## Request Body
    
    ```json
    {
        "policy_data": {
            "cargo_value_usd": 100000,
            "container_count": 2,
            "transit_days": 21,
            "risk_score": 0.65,
            ...
        },
        "market_rate": 0.85,
        "competitive_rate": 0.82
    }
    ```
    
    ## Response
    
    ```json
    {
        "recommended_premium": 850,
        "recommended_rate": 0.85,
        "actuarial_rate": 0.88,
        "market_rate": 0.85,
        "confidence": 0.85,
        "rate_components": {
            "risk_based": 0.88,
            "market_adjusted": 0.87,
            "competitive_adjusted": 0.85,
            "final": 0.85
        },
        "pricing_factors": {
            "target_loss_ratio": 0.65,
            "expense_ratio": 0.25,
            "profit_margin": 0.10
        },
        "explanation": "Recommended rate: 0.85‰ balances risk, market, and competition"
    }
    ```
    """
    try:
        # Convert policy data to DataFrame
        policy_df = pd.DataFrame([request.policy_data.dict()])
        
        # Create optimizer
        optimizer = PremiumOptimizer(loss_model, claim_model)
        
        # Get optimization result
        result = optimizer.optimize_premium(
            policy_df,
            request.market_rate,
            request.competitive_rate
        )
        
        # Generate explanation
        if request.competitive_rate:
            competition_str = f"competition ({request.competitive_rate:.2f}‰)"
        else:
            competition_str = "profitability"
        
        explanation = (
            f"Recommended rate: {result['recommended_rate']:.2f}‰ balances risk "
            f"(actuarial: {result['actuarial_rate']:.2f}‰), market "
            f"({request.market_rate:.2f}‰), and {competition_str}"
        )
        
        logger.info(
            "Premium optimized",
            recommended_rate=result['recommended_rate'],
            recommended_premium=result['recommended_premium'],
            confidence=result['confidence']
        )
        
        return PremiumOptimizationResponse(
            recommended_premium=result['recommended_premium'],
            recommended_rate=result['recommended_rate'],
            actuarial_rate=result['actuarial_rate'],
            market_rate=result['market_rate'],
            confidence=result['confidence'],
            rate_components=result['rate_components'],
            pricing_factors=result['pricing_factors'],
            explanation=explanation
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Models not trained or invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Premium optimization error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Premium optimization failed: {str(e)}"
        )


@router.get("/predictive/status")
async def get_predictive_status():
    """
    Get status of predictive models.
    
    Returns information about which models are trained and available.
    
    ## Response
    
    ```json
    {
        "loss_prediction": {
            "trained": true,
            "features": 12,
            "model_type": "xgboost"
        },
        "claim_probability": {
            "trained": true,
            "features": 8,
            "model_type": "random_forest"
        },
        "market_trend": {
            "trained": true,
            "model_type": "xgboost"
        },
        "capabilities": [
            "loss_prediction",
            "claim_probability",
            "market_trend_forecasting",
            "premium_optimization"
        ]
    }
    ```
    """
    status = {
        "loss_prediction": {
            "trained": loss_model.model_mean is not None,
            "features": len(loss_model.feature_names),
            "model_type": "xgboost" if loss_model.use_xgboost else "gradient_boosting"
        },
        "claim_probability": {
            "trained": claim_model.model is not None,
            "features": len(claim_model.feature_names),
            "model_type": "random_forest"
        },
        "market_trend": {
            "trained": market_predictor.rate_model is not None,
            "model_type": "xgboost" if market_predictor.use_xgboost else "gradient_boosting"
        },
        "capabilities": []
    }
    
    if status["loss_prediction"]["trained"]:
        status["capabilities"].append("loss_prediction")
    
    if status["claim_probability"]["trained"]:
        status["capabilities"].append("claim_probability")
    
    if status["market_trend"]["trained"]:
        status["capabilities"].extend(["market_trend_forecasting", "premium_optimization"])
    
    return status


# Import numpy for market trend sample data
import numpy as np
