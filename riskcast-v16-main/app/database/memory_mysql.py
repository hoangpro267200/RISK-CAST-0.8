"""
MySQL-based Memory System
Replaces JSON file-based memory system
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json

from app.config.database import get_session
from app.models.shipment import ShipmentDB
from app.models.risk_analysis import RiskAnalysis
from app.models.scenario import Scenario
from app.models.kv_store import KVStore
from sqlalchemy.orm import Session
from sqlalchemy import desc


class MemorySystemMySQL:
    """MySQL-based Memory System for RISKCAST"""
    
    def __init__(self):
        """Initialize MySQL memory system"""
        pass
    
    def save_shipment(self, shipment_data: Dict, risk_analysis: Dict, summary: str = "") -> str:
        """
        Save shipment analysis to MySQL database
        
        Args:
            shipment_data: Original shipment data
            risk_analysis: Risk calculation results
            summary: Executive summary text
        
        Returns:
            shipment_id: Unique identifier for this shipment
        """
        shipment_id = str(uuid.uuid4())
        
        with get_session() as db:
            # Extract route info
            pol = shipment_data.get("pol_code") or shipment_data.get("pol") or shipment_data.get("origin", "")
            pod = shipment_data.get("pod_code") or shipment_data.get("pod") or shipment_data.get("destination", "")
            route = shipment_data.get("route", "")
            
            # Create shipment record
            shipment = ShipmentDB(
                id=str(uuid.uuid4()),
                shipment_id=shipment_id,
                pol=pol,
                pod=pod,
                route=route,
                carrier=shipment_data.get("carrier", ""),
                etd=self._parse_datetime(shipment_data.get("etd")),
                eta=self._parse_datetime(shipment_data.get("eta")),
                transit_time=str(shipment_data.get("transit_time", "")),
                cargo_type=shipment_data.get("cargo_type", ""),
                cargo_value=str(shipment_data.get("cargo_value", "")),
                container=shipment_data.get("container", ""),
                packaging=shipment_data.get("packaging", ""),
                incoterm=shipment_data.get("incoterm", ""),
                shipment_data=shipment_data
            )
            
            db.add(shipment)
            
            # Create risk analysis record
            risk_analysis_record = RiskAnalysis(
                id=str(uuid.uuid4()),
                shipment_id=shipment_id,
                risk_score=risk_analysis.get("risk_score") or risk_analysis.get("overall_risk_index"),
                overall_risk=risk_analysis.get("overall_risk_index") or risk_analysis.get("risk_score"),
                risk_level=risk_analysis.get("risk_level", "MEDIUM"),
                confidence=risk_analysis.get("confidence", 0.8),
                engine_result=risk_analysis,
                recommendations=risk_analysis.get("recommendations"),
                layers=risk_analysis.get("layers"),
                drivers=risk_analysis.get("drivers") or risk_analysis.get("risk_factors"),
                scenarios=risk_analysis.get("scenarios"),
                financial=risk_analysis.get("financial"),
                ai_narrative=risk_analysis.get("ai_narrative"),
                engine_version="v2",
                language=shipment_data.get("language", "en")
            )
            
            db.add(risk_analysis_record)
            db.commit()
        
        return shipment_id
    
    def get_shipment(self, shipment_id: str) -> Optional[Dict]:
        """
        Retrieve shipment from MySQL database
        
        Args:
            shipment_id: Unique identifier
        
        Returns:
            Shipment memory dict or None
        """
        with get_session() as db:
            shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
            if not shipment:
                return None
            
            risk_analysis = db.query(RiskAnalysis).filter(
                RiskAnalysis.shipment_id == shipment_id
            ).order_by(desc(RiskAnalysis.created_at)).first()
            
            if not risk_analysis:
                return None
            
            return {
                "shipment_id": shipment.shipment_id,
                "timestamp": shipment.created_at.isoformat() if shipment.created_at else datetime.now().isoformat(),
                "shipment_data": shipment.shipment_data or shipment.to_dict(),
                "risk_analysis": risk_analysis.engine_result or {
                    "overall_risk_index": risk_analysis.overall_risk or risk_analysis.risk_score,
                    "risk_score": risk_analysis.risk_score or risk_analysis.overall_risk,
                    "risk_level": risk_analysis.risk_level,
                    "expected_loss": risk_analysis.financial.get("expectedLoss") if risk_analysis.financial else 0,
                    "reliability_score": risk_analysis.confidence * 100 if risk_analysis.confidence else 50.0
                },
                "summary": risk_analysis.ai_narrative.get("executiveSummary", "") if risk_analysis.ai_narrative else ""
            }
    
    def get_all_shipments(self, limit: int = 10) -> List[Dict]:
        """
        Get recent shipments from MySQL
        
        Args:
            limit: Maximum number of shipments to return
        
        Returns:
            List of shipment memories
        """
        with get_session() as db:
            shipments = db.query(Shipment).order_by(desc(Shipment.created_at)).limit(limit).all()
            
            result = []
            for shipment in shipments:
                risk_analysis = db.query(RiskAnalysis).filter(
                    RiskAnalysis.shipment_id == shipment.shipment_id
                ).order_by(desc(RiskAnalysis.created_at)).first()
                
                if risk_analysis:
                    result.append({
                        "shipment_id": shipment.shipment_id,
                        "timestamp": shipment.created_at.isoformat() if shipment.created_at else datetime.now().isoformat(),
                        "shipment_data": shipment.shipment_data or shipment.to_dict(),
                        "risk_analysis": risk_analysis.engine_result or {
                            "overall_risk_index": risk_analysis.overall_risk or risk_analysis.risk_score,
                            "risk_score": risk_analysis.risk_score or risk_analysis.overall_risk,
                            "risk_level": risk_analysis.risk_level,
                            "expected_loss": risk_analysis.financial.get("expectedLoss") if risk_analysis.financial else 0,
                            "reliability_score": risk_analysis.confidence * 100 if risk_analysis.confidence else 50.0
                        },
                        "summary": risk_analysis.ai_narrative.get("executiveSummary", "") if risk_analysis.ai_narrative else ""
                    })
            
            return result
    
    def compare_shipments(self, shipment_id_1: str, shipment_id_2: str) -> Dict:
        """
        Compare two shipments from MySQL
        
        Args:
            shipment_id_1: First shipment ID
            shipment_id_2: Second shipment ID
        
        Returns:
            Comparison analysis
        """
        shipment_1 = self.get_shipment(shipment_id_1)
        shipment_2 = self.get_shipment(shipment_id_2)
        
        if not shipment_1 or not shipment_2:
            return {
                "error": "One or both shipments not found",
                "status": "error"
            }
        
        risk_1 = shipment_1.get('risk_analysis', {})
        risk_2 = shipment_2.get('risk_analysis', {})
        
        overall_1 = risk_1.get('overall_risk_index', risk_1.get('risk_score', 50.0))
        overall_2 = risk_2.get('overall_risk_index', risk_2.get('risk_score', 50.0))
        
        risk_change = overall_2 - overall_1
        risk_trend = "increasing" if risk_change > 0 else "decreasing" if risk_change < 0 else "stable"
        
        return {
            "status": "success",
            "shipment_1": {
                "id": shipment_id_1,
                "timestamp": shipment_1.get('timestamp'),
                "overall_risk": overall_1,
                "expected_loss": risk_1.get('expected_loss', 0)
            },
            "shipment_2": {
                "id": shipment_id_2,
                "timestamp": shipment_2.get('timestamp'),
                "overall_risk": overall_2,
                "expected_loss": risk_2.get('expected_loss', 0)
            },
            "comparison": {
                "risk_change": round(risk_change, 2),
                "risk_trend": risk_trend,
                "loss_change": round(risk_2.get('expected_loss', 0) - risk_1.get('expected_loss', 0), 2),
                "reliability_change": round(
                    risk_2.get('reliability_score', 50.0) - risk_1.get('reliability_score', 50.0), 
                    2
                )
            },
            "insights": self._generate_comparison_insights(shipment_1, shipment_2, risk_change)
        }
    
    def get_historical_trend(self, limit: int = 5) -> Dict:
        """
        Get historical risk trend from MySQL
        
        Args:
            limit: Number of recent shipments to analyze
        
        Returns:
            Trend analysis
        """
        shipments = self.get_all_shipments(limit)
        
        if len(shipments) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least 2 shipments for trend analysis"
            }
        
        risk_scores = []
        timestamps = []
        
        for shipment in shipments:
            risk = shipment.get('risk_analysis', {}).get('overall_risk_index', 
                   shipment.get('risk_analysis', {}).get('risk_score', 50.0))
            risk_scores.append(risk)
            timestamps.append(shipment.get('timestamp', ''))
        
        # Calculate trend
        if len(risk_scores) >= 2:
            recent_avg = sum(risk_scores[:3]) / min(3, len(risk_scores))
            older_avg = sum(risk_scores[3:]) / max(1, len(risk_scores) - 3) if len(risk_scores) > 3 else recent_avg
            
            trend_direction = "increasing" if recent_avg > older_avg else "decreasing" if recent_avg < older_avg else "stable"
            trend_magnitude = abs(recent_avg - older_avg)
        else:
            trend_direction = "stable"
            trend_magnitude = 0
        
        return {
            "status": "success",
            "total_shipments": len(shipments),
            "average_risk": round(sum(risk_scores) / len(risk_scores), 2),
            "trend_direction": trend_direction,
            "trend_magnitude": round(trend_magnitude, 2),
            "recent_risk_scores": [round(r, 2) for r in risk_scores],
            "timestamps": timestamps
        }
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a key-value pair in MySQL store
        
        Args:
            key: Storage key
            value: Value to store (must be JSON serializable)
        """
        with get_session() as db:
            kv = db.query(KVStore).filter(KVStore.key == key).first()
            if kv:
                kv.value = value
                kv.updated_at = datetime.utcnow()
            else:
                kv = KVStore(key=key, value=value)
                db.add(kv)
            db.commit()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from MySQL store
        
        Args:
            key: Storage key
            default: Default value if key not found
        
        Returns:
            Stored value or default
        """
        with get_session() as db:
            kv = db.query(KVStore).filter(KVStore.key == key).first()
            return kv.value if kv else default
    
    def _parse_datetime(self, dt_str: Any) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not dt_str:
            return None
        if isinstance(dt_str, datetime):
            return dt_str
        try:
            # Try ISO format
            return datetime.fromisoformat(str(dt_str).replace('Z', '+00:00'))
        except:
            try:
                # Try common formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y']:
                    try:
                        return datetime.strptime(str(dt_str), fmt)
                    except:
                        continue
            except:
                pass
        return None
    
    def _generate_comparison_insights(self, shipment_1: Dict, shipment_2: Dict, risk_change: float) -> List[str]:
        """Generate comparison insights"""
        insights = []
        
        if abs(risk_change) > 10:
            if risk_change > 0:
                insights.append(f"Risk increased significantly by {risk_change:.1f} points - review route and carrier selection")
            else:
                insights.append(f"Risk decreased by {abs(risk_change):.1f} points - improvements in risk management")
        
        risk_1 = shipment_1.get('risk_analysis', {})
        risk_2 = shipment_2.get('risk_analysis', {})
        
        loss_1 = risk_1.get('expected_loss', 0)
        loss_2 = risk_2.get('expected_loss', 0)
        
        if abs(loss_2 - loss_1) > 1000:
            insights.append(f"Expected loss changed by ${abs(loss_2 - loss_1):,.2f} - significant financial impact")
        
        rel_1 = risk_1.get('reliability_score', 50.0)
        rel_2 = risk_2.get('reliability_score', 50.0)
        
        if abs(rel_2 - rel_1) > 10:
            insights.append(f"Reliability changed by {abs(rel_2 - rel_1):.1f}% - delivery performance impact")
        
        return insights


# Global MySQL memory instance
memory_system_mysql = MemorySystemMySQL()

