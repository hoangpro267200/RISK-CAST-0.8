"""
Risk Assessment Background Tasks
"""

from datetime import datetime
from typing import Dict, List, Optional
import asyncio

from celery import shared_task
from celery.utils.log import get_task_logger

from app.tasks.celery_app import celery_app
from app.core.logging import get_logger


logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.risk_tasks.calculate_quote_risk",
    max_retries=3,
    default_retry_delay=30
)
def calculate_quote_risk(
    self,
    quote_id: str,
    cargo_data: Dict,
    route_data: Dict
) -> Dict:
    """
    Calculate risk for a quote asynchronously.
    
    Called when a new quote is requested.
    """
    logger.info(f"Calculating risk for quote {quote_id}")
    
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _async_calculate_risk(quote_id, cargo_data, route_data)
            )
        finally:
            loop.close()
        
        logger.info(f"Risk calculation complete for quote {quote_id}: {result.get('risk_score')}")
        return result
        
    except Exception as e:
        logger.error(f"Risk calculation failed for quote {quote_id}: {e}")
        raise self.retry(exc=e)


async def _async_calculate_risk(
    quote_id: str,
    cargo_data: Dict,
    route_data: Dict
) -> Dict:
    """Async risk calculation implementation."""
    from app.core.risk_engine.v16.risk_engine_calibrated import CalibratedRiskEngine
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get or create model version
        from app.models.risk_model import RiskModelVersion
        from sqlalchemy import select
        
        result = db.execute(
            select(RiskModelVersion).where(RiskModelVersion.version == 'v16.0.0')
        )
        model_version = result.scalar_one_or_none()
        
        if not model_version:
            # Create default model version if not exists
            model_version = RiskModelVersion(
                version='v16.0.0',
                is_active=True
            )
            db.add(model_version)
            db.commit()
            db.refresh(model_version)
        
        engine = CalibratedRiskEngine(model_version=model_version)
        
        # Build shipment_data dict for risk engine
        shipment_data = {
            "cargo_type": cargo_data.get("cargo_type"),
            "cargo_value_usd": cargo_data.get("cargo_value_usd"),
            "origin_port": route_data.get("origin_port"),
            "destination_port": route_data.get("destination_port"),
            "departure_date": route_data.get("departure_date"),
            **cargo_data,
            **route_data
        }
        
        # Calculate risk
        risk_result = engine.calculate_risk(shipment_data)
        
        # Update quote with risk score
        from sqlalchemy import select
        from app.models.quote import Quote
        
        result = db.execute(
            select(Quote).where(Quote.id == quote_id)
        )
        quote = result.scalar_one_or_none()
        
        if quote:
            # Extract risk score and grade from RiskMetrics
            overall_score = getattr(risk_result, 'overall_score', None) or getattr(risk_result, 'overall_risk', 0.5)
            risk_grade = getattr(risk_result, 'risk_grade', None) or _score_to_grade(overall_score)
            
            quote.risk_score = overall_score
            quote.risk_grade = risk_grade
            quote.risk_data = risk_result.to_dict() if hasattr(risk_result, 'to_dict') else {
                "overall_score": overall_score,
                "risk_grade": risk_grade
            }
            db.commit()
        
        # Prepare return value
        overall_score = getattr(risk_result, 'overall_score', None) or getattr(risk_result, 'overall_risk', 0.5)
        risk_grade = getattr(risk_result, 'risk_grade', None) or _score_to_grade(overall_score)
        
        return risk_result.to_dict() if hasattr(risk_result, 'to_dict') else {
            "overall_score": overall_score,
            "risk_grade": risk_grade
        }
        
    finally:
        db.close()


def _score_to_grade(score: float) -> str:
    """Convert risk score to grade."""
    if score < 0.2:
        return "A"
    elif score < 0.4:
        return "B"
    elif score < 0.6:
        return "C"
    elif score < 0.8:
        return "D"
    else:
        return "F"


@celery_app.task(
    bind=True,
    name="app.tasks.risk_tasks.recalculate_policy_risk",
    max_retries=3
)
def recalculate_policy_risk(
    self,
    policy_id: str,
    reason: str = "scheduled"
) -> Dict:
    """
    Recalculate risk for an active policy.
    
    Called when risk factors change (weather, port conditions, etc.)
    """
    logger.info(f"Recalculating risk for policy {policy_id}, reason: {reason}")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                _async_recalculate_policy_risk(policy_id)
            )
        finally:
            loop.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Policy risk recalculation failed: {e}")
        raise self.retry(exc=e)


async def _async_recalculate_policy_risk(policy_id: str) -> Dict:
    """Async policy risk recalculation."""
    from app.database import SessionLocal
    from sqlalchemy import select
    from app.models.policy import Policy
    
    db = SessionLocal()
    try:
        result = db.execute(
            select(Policy).where(Policy.id == policy_id)
        )
        policy = result.scalar_one_or_none()
        
        if not policy:
            return {"error": "Policy not found"}
        
        # Recalculate using current data
        # ... risk engine call ...
        
        return {
            "policy_id": policy_id,
            "previous_risk_score": getattr(policy, 'risk_score', None),
            "new_risk_score": getattr(policy, 'risk_score', None),  # Would be updated
            "recalculated_at": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.risk_tasks.batch_risk_recalculation"
)
def batch_risk_recalculation(self, policy_ids: List[str]) -> Dict:
    """
    Batch recalculate risk for multiple policies.
    """
    logger.info(f"Batch risk recalculation for {len(policy_ids)} policies")
    
    results = []
    for policy_id in policy_ids:
        try:
            result = recalculate_policy_risk.delay(policy_id, "batch")
            results.append({"policy_id": policy_id, "task_id": result.id})
        except Exception as e:
            results.append({"policy_id": policy_id, "error": str(e)})
    
    return {
        "total": len(policy_ids),
        "dispatched": len([r for r in results if "task_id" in r]),
        "results": results
    }


@celery_app.task(
    bind=True,
    name="app.tasks.risk_tasks.analyze_portfolio_risk"
)
def analyze_portfolio_risk(
    self,
    tenant_id: str,
    as_of_date: Optional[str] = None
) -> Dict:
    """
    Analyze portfolio-level risk for a tenant.
    """
    logger.info(f"Analyzing portfolio risk for tenant {tenant_id}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _async_portfolio_analysis(tenant_id, as_of_date)
        )
        return result
    finally:
        loop.close()


async def _async_portfolio_analysis(
    tenant_id: str,
    as_of_date: Optional[str]
) -> Dict:
    """Async portfolio analysis."""
    from app.database import SessionLocal
    from sqlalchemy import select, func
    from app.models.policy import Policy
    
    db = SessionLocal()
    try:
        # Get active policies
        result = db.execute(
            select(Policy)
            .where(Policy.tenant_id == tenant_id)
            .where(Policy.status == "ACTIVE")
        )
        policies = result.scalars().all()
        
        if not policies:
            return {"tenant_id": tenant_id, "message": "No active policies"}
        
        # Calculate metrics
        total_exposure = sum(getattr(p, 'coverage_limit_usd', 0) or 0 for p in policies)
        total_premium = sum(getattr(p, 'total_premium_usd', 0) or 0 for p in policies)
        risk_scores = [getattr(p, 'risk_score', 0) or 0 for p in policies]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        # Risk distribution
        risk_distribution = {
            "A": len([p for p in policies if getattr(p, 'risk_grade', None) == "A"]),
            "B": len([p for p in policies if getattr(p, 'risk_grade', None) == "B"]),
            "C": len([p for p in policies if getattr(p, 'risk_grade', None) == "C"]),
            "D": len([p for p in policies if getattr(p, 'risk_grade', None) == "D"]),
            "F": len([p for p in policies if getattr(p, 'risk_grade', None) == "F"]),
        }
        
        # Concentration by cargo type
        cargo_concentration = {}
        for p in policies:
            cargo_type = getattr(p, 'cargo_type', 'UNKNOWN')
            if cargo_type not in cargo_concentration:
                cargo_concentration[cargo_type] = {"count": 0, "exposure": 0}
            cargo_concentration[cargo_type]["count"] += 1
            cargo_concentration[cargo_type]["exposure"] += getattr(p, 'coverage_limit_usd', 0) or 0
        
        return {
            "tenant_id": tenant_id,
            "as_of_date": as_of_date or datetime.utcnow().date().isoformat(),
            "total_policies": len(policies),
            "total_exposure_usd": total_exposure,
            "total_premium_usd": total_premium,
            "average_risk_score": round(avg_risk_score, 3),
            "risk_distribution": risk_distribution,
            "cargo_concentration": cargo_concentration,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    finally:
        db.close()
