"""
RISKCAST Engine v2 - Unified Risk Scoring
Combines FAHP weights, TOPSIS scores, climate risk, and network risk into final 0-100 score
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class RiskScoreComponents:
    """Components of final risk score"""
    fahp_weighted: float  # FAHP-weighted TOPSIS component
    climate_risk: float   # Climate risk component
    network_risk: float   # Network risk component
    operational_risk: float  # Operational risk component
    missing_data_penalty: float  # Penalty for missing data
    final_score: float    # Final unified score (0-100)


class UnifiedRiskScoring:
    """Unified risk scoring system"""
    
    def __init__(self):
        """Initialize unified scoring"""
        # Weight fusion coefficients
        self.FAHP_WEIGHT = 0.45  # FAHP-weighted TOPSIS
        self.CLIMATE_WEIGHT = 0.20  # Climate risk
        self.NETWORK_WEIGHT = 0.20  # Network risk
        self.OPERATIONAL_WEIGHT = 0.15  # Operational risk
        
        # Missing data penalty
        self.MISSING_DATA_PENALTY = 0.1  # 10% penalty per missing critical field
        
    def compute_fahp_weighted_component(self, topsis_score: float,
                                       fahp_weights: Dict[str, float]) -> float:
        """
        Compute FAHP-weighted TOPSIS component
        
        Args:
            topsis_score: TOPSIS closeness coefficient (0-1)
            fahp_weights: FAHP weights dictionary
            
        Returns:
            Weighted component (0-1)
        """
        # FAHP weights already sum to 1, so we can use TOPSIS score directly
        # Weighted by overall FAHP consistency
        weight_sum = sum(fahp_weights.values())
        if weight_sum > 0:
            consistency_factor = 1.0  # Could incorporate FAHP consistency ratio
            weighted = topsis_score * consistency_factor
        else:
            weighted = topsis_score
        
        return min(1.0, max(0.0, weighted))
    
    def compute_operational_risk(self, inputs: Dict[str, any]) -> float:
        """
        Compute operational risk from various inputs
        
        Args:
            inputs: Dictionary of operational inputs
            
        Returns:
            Operational risk score (0-1)
        """
        risk_factors = []
        
        # Transit time variance
        transit_time = inputs.get("transit_time")
        if transit_time:
            # Longer transit times = higher operational risk
            normalized_transit = min(1.0, transit_time / 30.0)  # Normalize to 30 days
            risk_factors.append(normalized_transit * 0.3)
        
        # Cargo value (higher value = higher risk)
        cargo_value = inputs.get("cargo_value", 0)
        if cargo_value > 0:
            normalized_value = min(1.0, cargo_value / 1000000.0)  # Normalize to $1M
            risk_factors.append(normalized_value * 0.2)
        
        # Container match
        container_match = inputs.get("container_match")
        if container_match is not None:
            try:
                container_match = float(container_match)
                # Lower match = higher risk
                mismatch_risk = 1.0 - container_match if container_match <= 1.0 else 0.0
                risk_factors.append(mismatch_risk * 0.2)
            except (TypeError, ValueError):
                # Skip if container_match cannot be converted to float
                pass
        
        # Priority level (higher priority = higher operational risk if issues occur)
        priority = inputs.get("priority", "standard")
        priority_multipliers = {
            "critical": 1.3,
            "high": 1.1,
            "standard": 1.0,
            "low": 0.9,
        }
        priority_mult = priority_multipliers.get(priority.lower(), 1.0)
        
        # Packaging quality
        packaging = inputs.get("packaging_quality")
        if packaging is not None:
            try:
                packaging = float(packaging)
                if packaging < 0.5:
                    risk_factors.append((0.5 - packaging) * 0.3)
            except (TypeError, ValueError):
                # Skip if packaging cannot be converted to float
                pass
        
        # Combine factors
        if risk_factors:
            operational_risk = sum(risk_factors) * priority_mult
        else:
            operational_risk = 0.5  # Default medium risk
        
        return min(1.0, max(0.0, operational_risk))
    
    def compute_missing_data_penalty(self, inputs: Dict[str, any],
                                    critical_fields: List[str]) -> float:
        """
        Compute penalty for missing critical data
        
        Args:
            inputs: Input dictionary
            critical_fields: List of critical field names
            
        Returns:
            Penalty factor (0-1, 1 = no penalty, <1 = penalty applied)
        """
        missing_count = 0
        for field in critical_fields:
            if field not in inputs or inputs[field] is None:
                missing_count += 1
        
        if missing_count == 0:
            return 1.0
        
        penalty = 1.0 - (missing_count * self.MISSING_DATA_PENALTY)
        return max(0.0, penalty)
    
    def apply_nonlinear_scaling(self, base_score: float) -> float:
        """
        Apply non-linear scaling for extreme events
        
        Args:
            base_score: Base risk score (0-1)
            
        Returns:
            Scaled score (0-1)
        """
        # Use exponential scaling to emphasize high-risk scenarios
        # y = x^0.8 for more gradual, or x^1.2 for more aggressive
        
        if base_score < 0.5:
            # Lower risk: more gradual scaling
            scaled = base_score ** 0.9
        else:
            # Higher risk: exponential emphasis
            scaled = base_score ** 0.7
        
        return min(1.0, max(0.0, scaled))
    
    def compute_unified_score(self, topsis_score: float,
                             fahp_weights: Dict[str, float],
                             climate_risk: float,
                             network_risk: float,
                             operational_inputs: Dict[str, any],
                             critical_fields: Optional[List[str]] = None) -> RiskScoreComponents:
        """
        Compute unified risk score (0-100)
        
        Args:
            topsis_score: TOPSIS closeness coefficient (0-1)
            fahp_weights: FAHP weights dictionary
            climate_risk: Climate risk score (0-1)
            network_risk: Network risk score (0-1)
            operational_inputs: Operational risk inputs
            critical_fields: List of critical fields for missing data check
            
        Returns:
            RiskScoreComponents object
        """
        # Compute FAHP-weighted component
        fahp_weighted = self.compute_fahp_weighted_component(topsis_score, fahp_weights)
        
        # Compute operational risk
        operational_risk = self.compute_operational_risk(operational_inputs)
        
        # Check for missing data
        if critical_fields is None:
            critical_fields = ["route", "pol", "pod", "cargo_value"]
        
        missing_penalty = self.compute_missing_data_penalty(operational_inputs, critical_fields)
        
        # Weighted fusion
        base_score = (
            fahp_weighted * self.FAHP_WEIGHT +
            climate_risk * self.CLIMATE_WEIGHT +
            network_risk * self.NETWORK_WEIGHT +
            operational_risk * self.OPERATIONAL_WEIGHT
        )
        
        # Apply non-linear scaling
        scaled_score = self.apply_nonlinear_scaling(base_score)
        
        # Apply missing data penalty
        final_score = scaled_score * missing_penalty
        
        # Scale to 0-100
        final_score_0_100 = final_score * 100.0
        
        # Clamp to 0-100
        final_score_0_100 = min(100.0, max(0.0, final_score_0_100))
        
        return RiskScoreComponents(
            fahp_weighted=fahp_weighted,
            climate_risk=climate_risk,
            network_risk=network_risk,
            operational_risk=operational_risk,
            missing_data_penalty=missing_penalty,
            final_score=final_score_0_100
        )
















