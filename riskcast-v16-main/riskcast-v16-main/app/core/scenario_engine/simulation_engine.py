"""
RISKCAST Scenario Engine - Core Simulation Module
Simulates risk scenarios by adjusting key factors and recomputing scores
"""

from typing import Dict, List, Optional, Any
from copy import deepcopy
import json

from app.core.engine_v2.risk_pipeline import RiskPipeline
from app.core.engine_v2.fahp import FAHPSolver
from app.core.engine_v2.topsis import TOPSISSolver
from app.core.engine_v2.climate_model import ClimateRiskModel
from app.core.engine_v2.network_model import NetworkRiskModel
from app.core.engine_v2.scoring import UnifiedRiskScoring
from app.core.engine_v2.risk_profile import RiskProfileBuilder


class SimulationEngine:
    """Core simulation engine for scenario testing"""
    
    def __init__(self):
        """Initialize simulation engine"""
        self.fahp_solver = FAHPSolver()
        self.topsis_solver = TOPSISSolver()
        self.climate_model = ClimateRiskModel()
        self.network_model = NetworkRiskModel()
        self.scoring = UnifiedRiskScoring()
        self.profile_builder = RiskProfileBuilder()
    
    def clone_factors(self, factors: Dict[str, float]) -> Dict[str, float]:
        """
        Deep clone risk factors dictionary
        
        Args:
            factors: Original risk factors
            
        Returns:
            Cloned factors dictionary
        """
        return deepcopy(factors)
    
    def apply_adjustments(self, factors: Dict[str, float], 
                         adjustments: Dict[str, float]) -> Dict[str, float]:
        """
        Apply percentage adjustments to risk factors
        
        Args:
            factors: Original risk factors (values 0-1)
            adjustments: Adjustment percentages (e.g., {"port": +0.15, "weather": -0.1})
                        Can be absolute values or percentages
            
        Returns:
            Adjusted factors dictionary
        """
        adjusted = self.clone_factors(factors)
        
        # Map common adjustment keys to factor keys
        key_mapping = {
            "port_congestion": "port",
            "weather_hazard": "climate",
            "carrier_reliability": "carrier",
            "esg": "esg",
            "network": "network",
            "equipment": "equipment",
            "delay": "delay",
            "climate": "climate",
            "port": "port",
            "carrier": "carrier",
        }
        
        for adj_key, adj_value in adjustments.items():
            # Find corresponding factor key
            factor_key = key_mapping.get(adj_key, adj_key)
            
            if factor_key in adjusted:
                # Apply adjustment as percentage change
                # adj_value is like +0.15 (15% increase) or -0.1 (10% decrease)
                original_value = adjusted[factor_key]
                
                # Calculate new value with bounds
                new_value = original_value + adj_value
                
                # Clamp to [0, 1]
                adjusted[factor_key] = max(0.0, min(1.0, new_value))
        
        return adjusted
    
    def recompute_components(self, 
                           adjusted_factors: Dict[str, float],
                           original_inputs: Dict[str, Any],
                           original_components: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Recompute FAHP, TOPSIS, climate, and network components with adjusted factors
        
        Args:
            adjusted_factors: Risk factors after adjustments
            original_inputs: Original shipment inputs
            original_components: Original component results (for reference)
            
        Returns:
            Dictionary with recomputed components
        """
        # Step 1: Re-run FAHP with adjusted context
        fahp_weights = self.fahp_solver.solve(risk_context=adjusted_factors)
        
        # Step 2: Re-run TOPSIS with adjusted factors
        alternatives = [adjusted_factors]
        criteria = list(adjusted_factors.keys())
        criteria_directions = {c: "minimize" for c in criteria}
        
        topsis_result = self.topsis_solver.solve(
            alternatives=alternatives,
            criteria=criteria,
            weights=fahp_weights,
            criteria_directions=criteria_directions
        )
        
        # Step 3: Recompute climate risk (may need adjustment based on weather_hazard)
        # If weather_hazard was adjusted, scale climate risk accordingly
        climate_result = self.climate_model.compute_climate_risk(
            route=original_inputs.get("route", "UNKNOWN"),
            departure_date=original_inputs.get("etd"),
            etd=original_inputs.get("etd"),
            enso_state="neutral"
        )
        
        # Apply weather adjustment if present
        weather_adj = adjusted_factors.get("climate", climate_result.overall_risk)
        if "climate" in adjusted_factors:
            # Scale climate result by adjustment
            climate_risk = max(0.0, min(1.0, weather_adj))
        else:
            climate_risk = climate_result.overall_risk
        
        # Step 4: Recompute network risk
        network_result = self.network_model.compute_network_risk(
            pol=original_inputs.get("pol", ""),
            pod=original_inputs.get("pod", ""),
            carrier=original_inputs.get("carrier"),
            route=original_inputs.get("route")
        )
        
        # Apply network adjustment if present
        if "network" in adjusted_factors:
            network_risk = adjusted_factors["network"]
        else:
            network_risk = network_result.overall_risk
        
        return {
            "fahp_weights": fahp_weights,
            "topsis_score": topsis_result.closeness_coefficient,
            "climate_risk": climate_risk,
            "network_risk": network_risk,
            "climate_result": climate_result,
            "network_result": network_result,
        }
    
    async def simulate(self, 
                      baseline_result: Dict[str, Any],
                      adjustments: Dict[str, float],
                      original_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main simulation function
        
        Args:
            baseline_result: Original risk assessment result from RiskPipeline
            adjustments: Adjustment percentages (e.g., {"port_congestion": +0.15, "weather_hazard": +0.25})
            original_inputs: Original shipment inputs (optional, extracted from baseline if not provided)
            
        Returns:
            Simulation result dictionary with:
            - simulation_score: New risk score (0-100)
            - delta_from_baseline: Score difference
            - drivers_changed: List of factors that changed
            - matrix: Impact matrix
            - profile: Risk profile
            - confidence: Confidence score
            - components: Component breakdown
        """
        # Step 1: Extract original factors from baseline
        baseline_score = baseline_result.get("risk_score", 0)
        baseline_profile = baseline_result.get("profile", {})
        baseline_factors = baseline_profile.get("factors", {})
        
        # If no factors in baseline, try to reconstruct from components
        if not baseline_factors:
            # Extract from details if available
            details = baseline_result.get("details", {})
            baseline_factors = {
                "delay": 0.5,
                "port": 0.5,
                "climate": details.get("climate", {}).get("storm_probability", 0.5),
                "carrier": 0.5,
                "esg": 0.5,
                "equipment": 0.5,
            }
        
        # Step 2: Clone and adjust factors
        adjusted_factors = self.clone_factors(baseline_factors)
        adjusted_factors = self.apply_adjustments(adjusted_factors, adjustments)
        
        # Step 3: Extract original inputs
        if not original_inputs:
            # Try to reconstruct from baseline (simplified)
            original_inputs = {
                "route": baseline_result.get("details", {}).get("route", ""),
                "etd": None,
                "pol": "",
                "pod": "",
                "carrier": "",
                "transit_time": None,
                "cargo_value": None,
            }
        
        # Step 4: Recompute components
        components = self.recompute_components(adjusted_factors, original_inputs)
        
        # Step 5: Recompute unified score
        score_components = self.scoring.compute_unified_score(
            topsis_score=components["topsis_score"],
            fahp_weights=components["fahp_weights"],
            climate_risk=components["climate_risk"],
            network_risk=components["network_risk"],
            operational_inputs=original_inputs,
            critical_fields=["route", "pol", "pod", "cargo_value"]
        )
        
        # Step 6: Build new risk profile
        components_dict = {
            "fahp": score_components.fahp_weighted,
            "climate": score_components.climate_risk,
            "network": score_components.network_risk,
            "operational": score_components.operational_risk,
        }
        
        risk_profile = self.profile_builder.build_profile(
            score=score_components.final_score,
            factors=adjusted_factors,
            components=components_dict,
            operational_inputs=original_inputs,
            confidence=baseline_profile.get("confidence", 0.85)
        )
        
        # Step 7: Identify changed drivers
        drivers_changed = []
        for key, adj_value in adjustments.items():
            if abs(adj_value) > 0.01:  # Only significant changes
                original_val = baseline_factors.get(key, 0)
                new_val = adjusted_factors.get(key, original_val)
                if abs(new_val - original_val) > 0.01:
                    drivers_changed.append({
                        "factor": key,
                        "original": round(original_val, 3),
                        "adjusted": round(new_val, 3),
                        "delta": round(new_val - original_val, 3),
                    })
        
        # Step 8: Calculate delta
        simulation_score = round(score_components.final_score, 2)
        delta_from_baseline = round(simulation_score - baseline_score, 2)
        
        # Step 9: Build result
        profile_dict = self.profile_builder.profile_to_dict(risk_profile)
        
        result = {
            "simulation_score": simulation_score,
            "delta_from_baseline": delta_from_baseline,
            "drivers_changed": drivers_changed,
            "matrix": {
                "probability": risk_profile.matrix.probability,
                "severity": risk_profile.matrix.severity,
                "quadrant": risk_profile.matrix.quadrant,
                "description": risk_profile.matrix.description,
            },
            "profile": profile_dict,
            "confidence": round(risk_profile.confidence, 3),
            "components": {
                "fahp_weighted": round(score_components.fahp_weighted, 3),
                "climate_risk": round(score_components.climate_risk, 3),
                "network_risk": round(score_components.network_risk, 3),
                "operational_risk": round(score_components.operational_risk, 3),
                "missing_data_penalty": round(score_components.missing_data_penalty, 3),
            },
            "factors": adjusted_factors,
            "baseline_score": baseline_score,
        }
        
        return result




















