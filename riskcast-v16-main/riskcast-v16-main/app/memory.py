"""
RISKCAST Enterprise AI - Mini Memory System
Stores and compares shipment analysis history
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class ShipmentMemory:
    """Shipment analysis record"""
    shipment_id: str
    timestamp: str
    shipment_data: Dict
    risk_analysis: Dict
    summary: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class MemorySystem:
    """Mini Memory System for RISKCAST"""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize memory system
        
        Args:
            data_dir: Directory to store history data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.history_file = self.data_dir / "history.json"
        self.kv_store_file = self.data_dir / "kv_store.json"
        self._load_history()
        self._load_kv_store()
    
    def _load_history(self) -> None:
        """Load history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.history = {}
        else:
            self.history = {}
    
    def _load_kv_store(self) -> None:
        """Load key-value store from file"""
        if self.kv_store_file.exists():
            try:
                with open(self.kv_store_file, 'r', encoding='utf-8') as f:
                    self.kv_store = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.kv_store = {}
        else:
            self.kv_store = {}
    
    def _save_history(self) -> None:
        """Save history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving history: {e}")
    
    def _save_kv_store(self) -> None:
        """Save key-value store to file"""
        try:
            with open(self.kv_store_file, 'w', encoding='utf-8') as f:
                json.dump(self.kv_store, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving kv_store: {e}")
    
    def save_shipment(self, shipment_data: Dict, risk_analysis: Dict, summary: str = "") -> str:
        """
        Save shipment analysis to memory
        
        Args:
            shipment_data: Original shipment data
            risk_analysis: Risk calculation results
            summary: Executive summary text
        
        Returns:
            shipment_id: Unique identifier for this shipment
        """
        shipment_id = str(uuid.uuid4())
        
        memory = ShipmentMemory(
            shipment_id=shipment_id,
            timestamp=datetime.now().isoformat(),
            shipment_data=shipment_data,
            risk_analysis=risk_analysis,
            summary=summary
        )
        
        self.history[shipment_id] = memory.to_dict()
        self._save_history()
        
        return shipment_id
    
    def get_shipment(self, shipment_id: str) -> Optional[Dict]:
        """
        Retrieve shipment from memory
        
        Args:
            shipment_id: Unique identifier
        
        Returns:
            Shipment memory dict or None
        """
        return self.history.get(shipment_id)
    
    def get_all_shipments(self, limit: int = 10) -> List[Dict]:
        """
        Get recent shipments
        
        Args:
            limit: Maximum number of shipments to return
        
        Returns:
            List of shipment memories
        """
        shipments = list(self.history.values())
        # Sort by timestamp (newest first)
        shipments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return shipments[:limit]
    
    def compare_shipments(self, shipment_id_1: str, shipment_id_2: str) -> Dict:
        """
        Compare two shipments
        
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
        
        overall_1 = risk_1.get('overall_risk_index', 50.0)
        overall_2 = risk_2.get('overall_risk_index', 50.0)
        
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
            "insights": _generate_comparison_insights(shipment_1, shipment_2, risk_change)
        }
    
    def get_historical_trend(self, limit: int = 5) -> Dict:
        """
        Get historical risk trend
        
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
            risk = shipment.get('risk_analysis', {}).get('overall_risk_index', 50.0)
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
        Set a key-value pair in the store
        
        Args:
            key: Storage key
            value: Value to store (must be JSON serializable)
        """
        self.kv_store[key] = value
        self._save_kv_store()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the store
        
        Args:
            key: Storage key
            default: Default value if key not found
        
        Returns:
            Stored value or default
        """
        return self.kv_store.get(key, default)


def _generate_comparison_insights(shipment_1: Dict, shipment_2: Dict, risk_change: float) -> List[str]:
    """Generate comparison insights"""
    insights = []
    
    if abs(risk_change) > 10:
        if risk_change > 0:
            insights.append(f"Risk increased significantly by {risk_change:.1f} points - review route and carrier selection")
        else:
            insights.append(f"Risk decreased by {abs(risk_change):.1f} points - improvements in risk management")
    
    loss_1 = shipment_1.get('risk_analysis', {}).get('expected_loss', 0)
    loss_2 = shipment_2.get('risk_analysis', {}).get('expected_loss', 0)
    
    if abs(loss_2 - loss_1) > 1000:
        insights.append(f"Expected loss changed by ${abs(loss_2 - loss_1):,.2f} - significant financial impact")
    
    rel_1 = shipment_1.get('risk_analysis', {}).get('reliability_score', 50.0)
    rel_2 = shipment_2.get('risk_analysis', {}).get('reliability_score', 50.0)
    
    if abs(rel_2 - rel_1) > 10:
        insights.append(f"Reliability changed by {abs(rel_2 - rel_1):.1f}% - delivery performance impact")
    
    return insights


# Global memory instance
memory_system = MemorySystem()


