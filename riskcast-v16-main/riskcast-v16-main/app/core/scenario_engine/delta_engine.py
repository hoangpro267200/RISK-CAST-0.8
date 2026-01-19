"""
RISKCAST Scenario Engine - Delta Analysis Module
Computes differences between baseline and scenario results
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class DeltaAnalysis:
    """Delta analysis result"""
    absolute_delta: float  # Absolute score difference
    percentage_change: float  # Percentage change
    risk_level_shift: str  # e.g., "Medium → High"
    dominant_factor_changes: List[Dict[str, Any]]  # Top changed factors
    recommended_mitigations: List[str]  # Mitigation recommendations
    component_deltas: Dict[str, float]  # Component-wise deltas


class DeltaEngine:
    """Delta analysis engine for scenario comparison"""
    
    RISK_LEVELS = {
        (0, 30): "Low",
        (30, 50): "Low-Medium",
        (50, 70): "Medium",
        (70, 85): "Medium-High",
        (85, 95): "High",
        (95, 100): "Critical",
    }
    
    def __init__(self):
        """Initialize delta engine"""
        pass
    
    def get_risk_level(self, score: float) -> str:
        """
        Determine risk level from score
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            Risk level string
        """
        for (min_score, max_score), level in self.RISK_LEVELS.items():
            if min_score <= score < max_score:
                return level
        return "Critical" if score >= 100 else "Low"
    
    def compute_component_deltas(self, 
                                baseline_components: Dict[str, float],
                                scenario_components: Dict[str, float]) -> Dict[str, float]:
        """
        Compute deltas for each component
        
        Args:
            baseline_components: Baseline component scores
            scenario_components: Scenario component scores
            
        Returns:
            Dictionary of component deltas
        """
        deltas = {}
        
        component_keys = [
            "fahp_weighted",
            "climate_risk",
            "network_risk",
            "operational_risk",
        ]
        
        for key in component_keys:
            baseline_val = baseline_components.get(key, 0.0)
            scenario_val = scenario_components.get(key, 0.0)
            
            # Convert to 0-100 scale if needed
            if baseline_val <= 1.0 and scenario_val <= 1.0:
                baseline_val *= 100.0
                scenario_val *= 100.0
            
            deltas[key] = round(scenario_val - baseline_val, 2)
        
        return deltas
    
    def identify_dominant_changes(self,
                                 baseline_factors: Dict[str, float],
                                 scenario_factors: Dict[str, float],
                                 top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Identify dominant factor changes
        
        Args:
            baseline_factors: Baseline factor values
            scenario_factors: Scenario factor values
            top_n: Number of top changes to return
            
        Returns:
            List of dominant changes
        """
        changes = []
        
        # Get all factor keys
        all_keys = set(baseline_factors.keys()) | set(scenario_factors.keys())
        
        for key in all_keys:
            baseline_val = baseline_factors.get(key, 0.0)
            scenario_val = scenario_factors.get(key, 0.0)
            delta = scenario_val - baseline_val
            
            # Only include significant changes
            if abs(delta) > 0.01:
                changes.append({
                    "factor": key,
                    "baseline": round(baseline_val, 3),
                    "scenario": round(scenario_val, 3),
                    "delta": round(delta, 3),
                    "delta_percent": round((delta / baseline_val * 100) if baseline_val > 0 else 0, 1),
                })
        
        # Sort by absolute delta
        changes.sort(key=lambda x: abs(x["delta"]), reverse=True)
        
        return changes[:top_n]
    
    def generate_mitigations(self, 
                            delta_analysis: DeltaAnalysis,
                            scenario_result: Dict[str, Any]) -> List[str]:
        """
        Generate mitigation recommendations based on delta analysis
        
        Args:
            delta_analysis: Delta analysis result
            scenario_result: Scenario result dictionary
            
        Returns:
            List of mitigation recommendations
        """
        mitigations = []
        
        # If risk increased significantly
        if delta_analysis.absolute_delta > 10:
            mitigations.append("Significant risk increase detected - consider alternative routes or carriers")
            mitigations.append("Increase insurance coverage and implement enhanced monitoring")
        
        # Check dominant changes
        for change in delta_analysis.dominant_factor_changes:
            factor = change["factor"]
            delta = change["delta"]
            
            if delta > 0.1:  # Significant increase
                if factor in ["climate", "weather_hazard"]:
                    mitigations.append("Weather risk increased - consider adjusting transit window or adding weather contingency")
                elif factor in ["port", "port_congestion"]:
                    mitigations.append("Port congestion risk increased - explore alternative ports or extended transit times")
                elif factor == "carrier":
                    mitigations.append("Carrier reliability concern - evaluate backup carrier options")
                elif factor == "network":
                    mitigations.append("Network dependency risk increased - identify alternative routing paths")
        
        # If risk level shifted up
        if "→" in delta_analysis.risk_level_shift and "High" in delta_analysis.risk_level_shift:
            mitigations.append("Risk level escalation - activate contingency plans and notify stakeholders")
        
        # Default if no specific mitigations
        if not mitigations:
            mitigations.append("Monitor key risk factors and maintain standard operating procedures")
        
        return mitigations
    
    def compute_delta(self, 
                     baseline: Dict[str, Any],
                     scenario: Dict[str, Any]) -> DeltaAnalysis:
        """
        Compute delta between baseline and scenario
        
        Args:
            baseline: Baseline risk assessment result
            scenario: Scenario simulation result
            
        Returns:
            DeltaAnalysis object with comprehensive comparison
        """
        # Extract scores
        baseline_score = baseline.get("risk_score", 0.0)
        scenario_score = scenario.get("simulation_score", scenario.get("risk_score", 0.0))
        
        # Compute absolute delta
        absolute_delta = round(scenario_score - baseline_score, 2)
        
        # Compute percentage change
        if baseline_score > 0:
            percentage_change = round((absolute_delta / baseline_score) * 100, 1)
        else:
            percentage_change = 0.0 if absolute_delta == 0 else 100.0
        
        # Determine risk level shift
        baseline_level = self.get_risk_level(baseline_score)
        scenario_level = self.get_risk_level(scenario_score)
        
        if baseline_level == scenario_level:
            risk_level_shift = f"{baseline_level} (No change)"
        else:
            risk_level_shift = f"{baseline_level} → {scenario_level}"
        
        # Extract factors
        baseline_profile = baseline.get("profile", {})
        baseline_factors = baseline_profile.get("factors", baseline.get("factors", {}))
        
        scenario_factors = scenario.get("factors", {})
        if not scenario_factors:
            scenario_profile = scenario.get("profile", {})
            scenario_factors = scenario_profile.get("factors", {})
        
        # Identify dominant changes
        dominant_changes = self.identify_dominant_changes(
            baseline_factors,
            scenario_factors,
            top_n=5
        )
        
        # Compute component deltas
        baseline_components = baseline.get("components", {})
        scenario_components = scenario.get("components", {})
        component_deltas = self.compute_component_deltas(baseline_components, scenario_components)
        
        # Create delta analysis
        delta_analysis = DeltaAnalysis(
            absolute_delta=absolute_delta,
            percentage_change=percentage_change,
            risk_level_shift=risk_level_shift,
            dominant_factor_changes=dominant_changes,
            recommended_mitigations=[],  # Will be filled below
            component_deltas=component_deltas,
        )
        
        # Generate mitigations
        delta_analysis.recommended_mitigations = self.generate_mitigations(
            delta_analysis,
            scenario
        )
        
        return delta_analysis
    
    def delta_to_dict(self, delta: DeltaAnalysis) -> Dict[str, Any]:
        """
        Convert DeltaAnalysis to dictionary
        
        Args:
            delta: DeltaAnalysis object
            
        Returns:
            Dictionary representation
        """
        return {
            "absolute_delta": delta.absolute_delta,
            "percentage_change": delta.percentage_change,
            "risk_level_shift": delta.risk_level_shift,
            "dominant_factor_changes": delta.dominant_factor_changes,
            "recommended_mitigations": delta.recommended_mitigations,
            "component_deltas": delta.component_deltas,
        }




















