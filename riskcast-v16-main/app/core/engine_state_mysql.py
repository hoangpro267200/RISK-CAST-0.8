"""
ENGINE-FIRST ARCHITECTURE: MySQL-based Shared State for Engine Results

This module provides MySQL-based storage for Engine v2 results.
This is the SINGLE SOURCE OF TRUTH for ResultsOS v4000.

CRITICAL ARCHITECTURE RULES:
- Results page MUST always render data that has passed through the CORE RISK ENGINE
- MySQL is the authoritative source (replaces in-memory state)
- No recomputation, no UI-side logic, pure pass-through
"""
from typing import Dict, Any, Optional
from app.config.database import get_session
from app.models.risk_analysis import RiskAnalysis
from sqlalchemy.orm import Session
from sqlalchemy import desc


def set_last_result_v2(result: Dict[str, Any]) -> None:
    """
    Store Engine v2 analysis result in MySQL database.
    
    This function is called by /api/v1/risk/v2/analyze endpoint
    after the engine completes execution.
    
    Args:
        result: Complete engine result object (authoritative, immutable)
    
    ARCHITECTURE GUARANTEE:
    - This is the ONLY place where v2 engine results are stored
    - Results page reads from this via GET /results/data
    - No recomputation, no UI-side logic, pure pass-through
    """
    try:
        with get_session() as db:
            # Extract shipment_id from result
            shipment_id = None
            if result.get("shipment"):
                shipment_id = result["shipment"].get("id") or result["shipment"].get("shipment_id")
            
            if not shipment_id:
                # Generate shipment_id from route or timestamp
                route = result.get("shipment", {}).get("route", "")
                if route:
                    shipment_id = f"SH-{route.replace(' ', '').replace('→', '-').replace('->', '-')}-{int(__import__('time').time())}"
                else:
                    shipment_id = f"SH-{int(__import__('time').time())}"
            
            # Check if risk analysis already exists for this shipment_id
            existing = db.query(RiskAnalysis).filter(
                RiskAnalysis.shipment_id == shipment_id
            ).order_by(desc(RiskAnalysis.created_at)).first()
            
            if existing:
                # Update existing record
                existing.risk_score = result.get("risk_score") or result.get("overall_risk")
                existing.overall_risk = result.get("overall_risk") or result.get("risk_score")
                existing.risk_level = result.get("risk_level", "MEDIUM")
                existing.confidence = result.get("confidence", 0.8)
                existing.engine_result = result
                existing.decision_summary = result.get("decision_summary")
                existing.recommendations = result.get("recommendations")
                existing.layers = result.get("layers")
                existing.drivers = result.get("drivers") or result.get("risk_factors")
                existing.scenarios = result.get("scenarios")
                existing.financial = result.get("financial") or result.get("loss")
                existing.ai_narrative = result.get("ai_narrative")
                existing.engine_version = result.get("engine_version", "v2")
                existing.language = result.get("language", "en")
            else:
                # Create new record
                risk_analysis = RiskAnalysis(
                    shipment_id=shipment_id,
                    risk_score=result.get("risk_score") or result.get("overall_risk"),
                    overall_risk=result.get("overall_risk") or result.get("risk_score"),
                    risk_level=result.get("risk_level", "MEDIUM"),
                    confidence=result.get("confidence", 0.8),
                    engine_result=result,
                    decision_summary=result.get("decision_summary"),
                    recommendations=result.get("recommendations"),
                    layers=result.get("layers"),
                    drivers=result.get("drivers") or result.get("risk_factors"),
                    scenarios=result.get("scenarios"),
                    financial=result.get("financial") or result.get("loss"),
                    ai_narrative=result.get("ai_narrative"),
                    engine_version=result.get("engine_version", "v2"),
                    language=result.get("language", "en")
                )
                db.add(risk_analysis)
            
            db.commit()
            
    except Exception as e:
        import logging
        logging.error(f"[Engine State MySQL] Error storing result: {e}", exc_info=True)
        # Fallback: Don't fail the request, just log error


def get_last_result_v2() -> Dict[str, Any]:
    """
    Get the latest Engine v2 analysis result from MySQL database.
    
    Returns:
        Complete engine result object or empty dict if no analysis has been run
    
    ARCHITECTURE GUARANTEE:
    - Returns exact object produced by v2 engine
    - No transformation, no computation, pure retrieval
    """
    try:
        with get_session() as db:
            # Get most recent risk analysis
            risk_analysis = db.query(RiskAnalysis).order_by(desc(RiskAnalysis.created_at)).first()
            
            if risk_analysis and risk_analysis.engine_result:
                return risk_analysis.engine_result.copy() if isinstance(risk_analysis.engine_result, dict) else {}
            
            return {}
            
    except Exception as e:
        import logging
        logging.error(f"[Engine State MySQL] Error retrieving result: {e}", exc_info=True)
        return {}


def get_result_by_shipment_id(shipment_id: str) -> Optional[Dict[str, Any]]:
    """
    Get engine result by shipment_id
    
    Args:
        shipment_id: Shipment identifier
    
    Returns:
        Engine result or None
    """
    try:
        with get_session() as db:
            risk_analysis = db.query(RiskAnalysis).filter(
                RiskAnalysis.shipment_id == shipment_id
            ).order_by(desc(RiskAnalysis.created_at)).first()
            
            if risk_analysis and risk_analysis.engine_result:
                return risk_analysis.engine_result.copy() if isinstance(risk_analysis.engine_result, dict) else {}
            
            return None
            
    except Exception as e:
        import logging
        logging.error(f"[Engine State MySQL] Error retrieving result by shipment_id: {e}", exc_info=True)
        return None


