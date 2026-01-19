"""
RISKCAST Engine v2 - Risk Pipeline Orchestrator
Main pipeline that orchestrates all risk assessment components
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json

from app.core.engine_v2.fahp import FAHPSolver
from app.core.engine_v2.topsis import TOPSISSolver
from app.core.engine_v2.climate_model import ClimateRiskModel
from app.core.engine_v2.network_model import NetworkRiskModel
from app.core.engine_v2.scoring import UnifiedRiskScoring
from app.core.engine_v2.risk_profile import RiskProfileBuilder
from app.core.engine_v2.llm_reasoner import LLMReasoner
from app.core.engine_v2.risk_driver_derivation import (
    derive_risk_drivers,
    drivers_to_dict_list
)
from app.core.utils.sanitizer import sanitize_input
from app.core.regions.detector import RegionDetector


class RiskPipeline:
    """Main risk assessment pipeline"""
    
    def __init__(self):
        """Initialize risk pipeline"""
        self.fahp_solver = FAHPSolver()
        self.topsis_solver = TOPSISSolver()
        self.climate_model = ClimateRiskModel()
        self.network_model = NetworkRiskModel()
        self.scoring = UnifiedRiskScoring()
        self.profile_builder = RiskProfileBuilder()
        self.llm_reasoner = LLMReasoner(use_llm=True)  # Can disable for testing
        self.region_detector = RegionDetector()
    
    def parse_inputs(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and sanitize shipment inputs
        
        Args:
            shipment_data: Raw shipment data dictionary
            
        Returns:
            Parsed and sanitized inputs
        """
        # Sanitize input data
        sanitized = sanitize_input(shipment_data)
        
        # Extract key fields
        parsed = {
            "route": sanitized.get("route") or sanitized.get("trade_route"),
            "pol": sanitized.get("pol") or sanitized.get("port_of_loading"),
            "pod": sanitized.get("pod") or sanitized.get("port_of_discharge"),
            "carrier": sanitized.get("carrier"),
            "etd": sanitized.get("etd") or sanitized.get("departure_date"),
            "eta": sanitized.get("eta") or sanitized.get("arrival_date"),
            "cargo_value": sanitized.get("cargo_value") or sanitized.get("shipment_value"),
            "cargo_type": sanitized.get("cargo_type"),
            "transit_time": sanitized.get("transit_time"),
            "container_type": sanitized.get("container_type"),
            "priority": sanitized.get("priority", "standard"),
            "packaging_quality": sanitized.get("packaging_quality", 0.5),
            "container_match": sanitized.get("container_match", 0.5),
            "carrier_rating": sanitized.get("carrier_rating", 0.5),
        }
        
        # Normalize values
        for key in ["cargo_value", "transit_time", "packaging_quality", "container_match", "carrier_rating"]:
            if parsed.get(key) is not None:
                try:
                    parsed[key] = float(parsed[key])
                except (ValueError, TypeError):
                    parsed[key] = None
        
        return parsed
    
    def extract_risk_context(self, inputs: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract risk context for FAHP
        
        Args:
            inputs: Parsed inputs
            
        Returns:
            Risk context dictionary
        """
        # Build risk context from inputs
        context = {}
        
        # Delay risk (based on transit time, route complexity)
        transit_time = inputs.get("transit_time")
        if transit_time:
            # Longer transit = higher delay risk
            context["delay"] = min(1.0, transit_time / 30.0)
        else:
            context["delay"] = 0.5  # Default
        
        # Port risk (based on POL/POD - simplified)
        # CRITICAL FIX: Handle None values before calling .upper()
        pol = inputs.get("pol") or ""
        pod = inputs.get("pod") or ""
        # Ensure both are strings (not None)
        pol = str(pol) if pol is not None else ""
        pod = str(pod) if pod is not None else ""
        if pol or pod:
            # Assume major ports have higher congestion risk
            combined = (pol + pod).upper()
            context["port"] = 0.6 if any(x in combined for x in ["SINGAPORE", "ROTTERDAM", "SHANGHAI"]) else 0.4
        else:
            context["port"] = 0.5
        context["climate"] = 0.5
        
        # Carrier risk (based on rating)
        carrier_rating = inputs.get("carrier_rating")
        if carrier_rating is None:
            carrier_rating = 0.5
        else:
            try:
                carrier_rating = float(carrier_rating)
            except (TypeError, ValueError):
                carrier_rating = 0.5
        context["carrier"] = 1.0 - carrier_rating  # Invert: lower rating = higher risk
        context["esg"] = 0.3
        
        # Equipment risk (based on container match)
        container_match = inputs.get("container_match")
        if container_match is None:
            container_match = 0.5
        else:
            try:
                container_match = float(container_match)
            except (TypeError, ValueError):
                container_match = 0.5
        context["equipment"] = 1.0 - container_match  # Lower match = higher risk
        
        return context
    
    async def run(self, shipment_data: Dict[str, Any], language: str = 'en') -> Dict[str, Any]:
        """
        Run complete risk assessment pipeline
        
        Args:
            shipment_data: Shipment data dictionary
            language: Language code (vi, en, zh)
            
        Returns:
            Complete risk assessment result dictionary
        """
        # Step 1: Parse and sanitize inputs
        inputs = self.parse_inputs(shipment_data)
        
        # Step 1.5: Detect region and load region config
        route = inputs.get("route", "")
        pol = inputs.get("pol", "")
        pod = inputs.get("pod", "")
        origin = pol or route.split('_')[0] if route else ""
        destination = pod or route.split('_')[1] if '_' in route else ""
        
        region_code, region_config = self.region_detector.detect_region(origin, destination)
        
        # Step 2: Extract risk context
        risk_context = self.extract_risk_context(inputs)
        
        # Step 3: Run FAHP
        fahp_weights = self.fahp_solver.solve(risk_context=risk_context)
        
        # Step 4: Run TOPSIS
        # Build alternatives (single alternative for this shipment)
        alternatives = [risk_context]
        criteria = list(risk_context.keys())
        
        # Determine criteria directions (all are minimization - lower is better)
        criteria_directions = {c: "minimize" for c in criteria}
        
        topsis_result = self.topsis_solver.solve(
            alternatives=alternatives,
            criteria=criteria,
            weights=fahp_weights,
            criteria_directions=criteria_directions
        )
        
        # Step 5: Run climate model
        climate_result = self.climate_model.compute_climate_risk(
            route=inputs.get("route", "UNKNOWN"),
            departure_date=inputs.get("etd"),
            etd=inputs.get("etd"),
            enso_state="neutral"  # Can be parameterized
        )
        
        # Update risk_context with climate
        risk_context["climate"] = climate_result.overall_risk
        
        # Step 6: Run network model
        network_result = self.network_model.compute_network_risk(
            pol=inputs.get("pol", ""),
            pod=inputs.get("pod", ""),
            carrier=inputs.get("carrier"),
            route=inputs.get("route")
        )
        
        # Step 7: Apply region-based adjustments
        # Adjust climate and network risks based on region weights
        adjusted_climate_risk = climate_result.overall_risk * region_config.get("climate_weight", 1.0)
        adjusted_network_risk = network_result.overall_risk * region_config.get("network_propagation_factor", 1.0)
        
        # Apply region weights to FAHP weights (adjust for strike, ESG, congestion)
        adjusted_fahp_weights = self._apply_region_weights(fahp_weights, risk_context, region_config)
        
        # Step 8: Compute unified score with region adjustments
        score_components = self.scoring.compute_unified_score(
            topsis_score=topsis_result.closeness_coefficient,
            fahp_weights=adjusted_fahp_weights,
            climate_risk=adjusted_climate_risk,
            network_risk=adjusted_network_risk,
            operational_inputs=inputs,
            critical_fields=["route", "pol", "pod", "cargo_value"]
        )
        
        # Apply region-specific final adjustment
        region_final_score = self._apply_region_final_score(
            score_components.final_score,
            risk_context,
            region_config
        )
        score_components.final_score = region_final_score
        
        # Step 9: Build risk profile
        components_dict = {
            "fahp": score_components.fahp_weighted,
            "climate": score_components.climate_risk,
            "network": score_components.network_risk,
            "operational": score_components.operational_risk,
        }
        
        risk_profile = self.profile_builder.build_profile(
            score=score_components.final_score,
            factors=risk_context,
            components=components_dict,
            operational_inputs=inputs,
            confidence=0.85  # Can be computed from data quality
        )
        
        # Step 10: Generate LLM reasoning (region-aware)
        profile_dict = self.profile_builder.profile_to_dict(risk_profile)
        reasoning_result = await self.llm_reasoner.generate_region_reasoning(
            region=region_code,
            lang=language,
            profile=profile_dict,
            factors=risk_context,
            score=score_components.final_score,
            region_config=region_config
        )
        
        # Step 11: Build final result
        result = {
            "risk_score": round(score_components.final_score, 2),
            "risk_level": risk_profile.level,
            "confidence": round(reasoning_result.confidence_score, 2),
            "profile": {
                "score": risk_profile.score,
                "level": risk_profile.level,
                "confidence": risk_profile.confidence,
                "explanation": risk_profile.explanation,
                "factors": risk_profile.factors,
                "matrix": {
                    "probability": risk_profile.matrix.probability,
                    "severity": risk_profile.matrix.severity,
                    "quadrant": risk_profile.matrix.quadrant,
                    "description": risk_profile.matrix.description,
                },
            },
            # Drivers: Use refined derivation logic (Engine v3)
            # This ensures drivers are structured, meaningful, and follow strict rules
            "drivers": drivers_to_dict_list(
                derive_risk_drivers(
                    factors=risk_profile.factors,
                    total_risk_score=score_components.final_score,
                    components=components_dict
                )
            ),
            "recommendations": reasoning_result.suggestions + risk_profile.recommendations,
            "reasoning": {
                "explanation": reasoning_result.explanation,
                "business_justification": reasoning_result.business_justification,
            },
            "components": {
                "fahp_weighted": round(score_components.fahp_weighted, 3),
                "climate_risk": round(climate_result.overall_risk, 3),
                "network_risk": round(network_result.overall_risk, 3),
                "operational_risk": round(score_components.operational_risk, 3),
                "missing_data_penalty": round(score_components.missing_data_penalty, 3),
            },
            "details": {
                "climate": {
                    "storm_probability": round(climate_result.storm_probability, 3),
                    "wind_index": round(climate_result.wind_index, 3),
                    "rainfall_intensity": round(climate_result.rainfall_intensity, 3),
                },
                "network": {
                    "port_centrality": round(network_result.port_centrality, 3),
                    "carrier_redundancy": round(network_result.carrier_redundancy, 3),
                    "propagation_factor": round(network_result.propagation_factor, 3),
                },
                "fahp_weights": {k: round(v, 3) for k, v in fahp_weights.items()},
                "topsis_score": round(topsis_result.closeness_coefficient, 3),
            },
            "region": {
                "code": region_code,
                "name": region_config.get("region_name", region_code),
                "config": {
                    "climate_weight": region_config.get("climate_weight"),
                    "congestion_weight": region_config.get("congestion_weight"),
                    "strike_weight": region_config.get("strike_weight"),
                    "esg_weight": region_config.get("esg_weight"),
                }
            },
        }
        
        return result
    
    def _apply_region_weights(self, fahp_weights: Dict[str, float], 
                              risk_context: Dict[str, float],
                              region_config: Dict) -> Dict[str, float]:
        """
        Apply region-specific weights to FAHP weights
        
        Args:
            fahp_weights: Original FAHP weights
            risk_context: Risk context factors
            region_config: Region configuration
            
        Returns:
            Adjusted FAHP weights
        """
        adjusted = fahp_weights.copy()
        
        # Adjust port/congestion weight
        if "port" in adjusted:
            adjusted["port"] *= region_config.get("congestion_weight", 1.0)
        
        # Adjust climate weight
        if "climate" in adjusted:
            adjusted["climate"] *= region_config.get("climate_weight", 1.0)
        
        # Normalize to sum to 1
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}
        
        return adjusted
    
    def _apply_region_final_score(self, base_score: float,
                                  risk_context: Dict[str, float],
                                  region_config: Dict) -> float:
        """
        Apply region-specific final score adjustment
        
        Args:
            base_score: Base risk score (0-100)
            risk_context: Risk context
            region_config: Region configuration
            
        Returns:
            Adjusted final score (0-100)
        """
        # Extract component risks
        congestion_risk = risk_context.get("port", 0.5)
        climate_risk = risk_context.get("climate", 0.5)
        strike_risk = risk_context.get("strike", 0.3)  # Can be derived from carrier/port
        esg_risk = risk_context.get("esg", 0.3)
        
        # Apply region weights to components
        weighted_components = (
            base_score * 0.5 +  # Keep base score weight
            congestion_risk * region_config.get("congestion_weight", 0.7) * 25 +
            climate_risk * region_config.get("climate_weight", 0.6) * 15 +
            strike_risk * region_config.get("strike_weight", 0.5) * 5 +
            esg_risk * region_config.get("esg_weight", 0.45) * 5
        )
        
        # Normalize to 0-100
        final_score = min(100.0, max(0.0, weighted_components))
        
        return final_score


