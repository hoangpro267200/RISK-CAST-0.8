"""
RISKCAST Engine v2 - Network Risk Model
Computes network propagation risks based on port centrality, carrier networks, and dependencies
"""

import numpy as np
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class NetworkRiskScore:
    """Network risk assessment result"""
    overall_risk: float  # 0-1
    port_centrality: float  # 0-1
    carrier_redundancy: float  # 0-1
    upstream_dependency: float  # 0-1
    downstream_dependency: float  # 0-1
    propagation_factor: float  # 0-1
    explanation: Dict[str, str]


class NetworkRiskModel:
    """Network risk assessment model"""
    
    # Major port centrality scores (simplified - in production would use actual network analysis)
    PORT_CENTRALITY_SCORES = {
        # Top tier (high centrality = high risk if disrupted)
        "SINGAPORE": 0.95,
        "ROTTERDAM": 0.90,
        "SHANGHAI": 0.88,
        "HONG KONG": 0.85,
        "LOS ANGELES": 0.82,
        
        # Second tier
        "BUSAN": 0.75,
        "DUBAI": 0.73,
        "HAMBURG": 0.70,
        "ANTWERP": 0.68,
        "LONG BEACH": 0.65,
        
        # Default for unknown ports
        "DEFAULT": 0.50,
    }
    
    # Carrier network redundancy (higher = more redundant = lower risk)
    CARRIER_REDUNDANCY = {
        # Major carriers (assumed to have good redundancy)
        "MAERSK": 0.25,  # Low risk score (high redundancy)
        "MSC": 0.25,
        "COSCO": 0.30,
        "CMA CGM": 0.30,
        "EVERGREEN": 0.35,
        "HAPAG LLOYD": 0.30,
        
        # Default for unknown carriers
        "DEFAULT": 0.60,  # Higher risk (lower redundancy)
    }
    
    def __init__(self):
        """Initialize network risk model"""
        pass
    
    def compute_port_centrality(self, pol: str, pod: str) -> float:
        """
        Compute port centrality index (based on betweenness centrality concept)
        
        Args:
            pol: Port of Loading (origin port)
            pod: Port of Discharge (destination port)
            
        Returns:
            Port centrality risk score (0-1, higher = more central = higher disruption risk)
        """
        # CRITICAL FIX: Handle None values before calling .upper()
        pol = str(pol) if pol is not None else ""
        pod = str(pod) if pod is not None else ""
        pol_upper = pol.upper().strip()
        pod_upper = pod.upper().strip()
        
        # Get centrality scores
        pol_centrality = self.PORT_CENTRALITY_SCORES.get(
            pol_upper,
            self._estimate_port_centrality(pol_upper)
        )
        
        pod_centrality = self.PORT_CENTRALITY_SCORES.get(
            pod_upper,
            self._estimate_port_centrality(pod_upper)
        )
        
        # Take maximum (if either port is critical, risk is high)
        max_centrality = max(pol_centrality, pod_centrality)
        
        # If both ports are major hubs, increase risk slightly
        if pol_centrality > 0.7 and pod_centrality > 0.7:
            max_centrality = min(1.0, max_centrality * 1.1)
        
        return max_centrality
    
    def _estimate_port_centrality(self, port: str) -> float:
        """
        Estimate port centrality if not in database
        
        Args:
            port: Port name
            
        Returns:
            Estimated centrality score
        """
        port_upper = port.upper()
        
        # Check for major port keywords
        major_keywords = ["SINGAPORE", "ROTTERDAM", "SHANGHAI", "HONG KONG", "LOS ANGELES"]
        if any(keyword in port_upper for keyword in major_keywords):
            return 0.80
        
        # Regional estimates
        if any(x in port_upper for x in ["PORT", "HARBOR", "TERMINAL"]):
            return 0.55  # Medium
        
        return 0.50  # Default
    
    def compute_carrier_redundancy(self, carrier: Optional[str] = None) -> float:
        """
        Compute carrier network redundancy
        
        Args:
            carrier: Carrier name
            
        Returns:
            Carrier redundancy risk score (0-1, lower = more redundant = lower risk)
        """
        if not carrier:
            return 0.60  # Default (unknown carrier = higher risk)
        
        # CRITICAL FIX: Handle None values before calling .upper()
        carrier = str(carrier) if carrier is not None else ""
        carrier_upper = carrier.upper().strip()
        
        # Exact match
        if carrier_upper in self.CARRIER_REDUNDANCY:
            return self.CARRIER_REDUNDANCY[carrier_upper]
        
        # Partial match
        for known_carrier, score in self.CARRIER_REDUNDANCY.items():
            if known_carrier in carrier_upper or carrier_upper in known_carrier:
                return score
        
        # Estimate based on carrier size (simplified heuristic)
        large_carrier_keywords = ["MAERSK", "MSC", "COSCO", "CMA", "EVERGREEN", "HAPAG"]
        if any(keyword in carrier_upper for keyword in large_carrier_keywords):
            return 0.35
        
        return 0.60  # Default
    
    def compute_upstream_dependency(self, route: str, pol: str) -> float:
        """
        Compute upstream dependency risk (supply chain dependencies before shipment)
        
        Args:
            route: Route identifier
            pol: Port of Loading
            
        Returns:
            Upstream dependency risk (0-1)
        """
        # CRITICAL FIX: Handle None values before calling .upper()
        route = str(route) if route is not None else ""
        pol = str(pol) if pol is not None else ""
        
        # Simplified: assume longer routes have more upstream dependencies
        route_upper = route.upper()
        
        # Intercontinental routes = higher upstream risk
        if any(x in route_upper for x in ["ASIA", "EUROPE", "AMERICA"]):
            base_risk = 0.6
        else:
            base_risk = 0.4
        
        # Major export hubs = higher dependency
        export_hubs = ["SHANGHAI", "SINGAPORE", "HONG KONG", "ROTTERDAM"]
        if any(hub in pol.upper() for hub in export_hubs):
            base_risk *= 1.2
        
        return min(1.0, max(0.0, base_risk))
    
    def compute_downstream_dependency(self, route: str, pod: str) -> float:
        """
        Compute downstream dependency risk (distribution network after arrival)
        
        Args:
            route: Route identifier
            pod: Port of Discharge
            
        Returns:
            Downstream dependency risk (0-1)
        """
        # CRITICAL FIX: Handle None values before calling .upper()
        pod = str(pod) if pod is not None else ""
        
        # Simplified: assume major consumption hubs have higher downstream risk
        import_hubs = ["LOS ANGELES", "LONG BEACH", "ROTTERDAM", "HAMBURG", "NEW YORK"]
        
        pod_upper = pod.upper()
        if any(hub in pod_upper for hub in import_hubs):
            base_risk = 0.7
        else:
            base_risk = 0.5
        
        return min(1.0, max(0.0, base_risk))
    
    def compute_propagation_factor(self, pol: str, pod: str, carrier: Optional[str] = None) -> float:
        """
        Compute disruption propagation factor
        
        Args:
            pol: Port of Loading
            pod: Port of Discharge
            carrier: Carrier name
            
        Returns:
            Propagation factor (0-1, higher = more likely to propagate)
        """
        # High propagation if:
        # 1. Ports are central (high centrality)
        # 2. Carrier has low redundancy
        # 3. Route is long/complex
        
        port_centrality = self.compute_port_centrality(pol, pod)
        carrier_redundancy_risk = self.compute_carrier_redundancy(carrier)
        
        # Combine factors
        propagation = (port_centrality * 0.6 + carrier_redundancy_risk * 0.4)
        
        return min(1.0, max(0.0, propagation))
    
    def compute_network_risk(self, pol: str, pod: str, carrier: Optional[str] = None,
                            route: Optional[str] = None) -> NetworkRiskScore:
        """
        Compute comprehensive network risk score
        
        Args:
            pol: Port of Loading
            pod: Port of Discharge
            carrier: Carrier name
            route: Route identifier
            
        Returns:
            NetworkRiskScore object
        """
        # CRITICAL FIX: Handle None values before using them
        pol = str(pol) if pol is not None else ""
        pod = str(pod) if pod is not None else ""
        route = route or f"{pol}-{pod}"
        route = str(route) if route is not None else ""
        
        # Compute individual components
        port_centrality = self.compute_port_centrality(pol, pod)
        carrier_redundancy = self.compute_carrier_redundancy(carrier)
        upstream = self.compute_upstream_dependency(route, pol)
        downstream = self.compute_downstream_dependency(route, pod)
        propagation = self.compute_propagation_factor(pol, pod, carrier)
        
        # Weighted combination
        overall_risk = (
            port_centrality * 0.25 +
            carrier_redundancy * 0.20 +
            upstream * 0.15 +
            downstream * 0.15 +
            propagation * 0.25
        )
        
        # Clamp to 0-1
        overall_risk = min(1.0, max(0.0, overall_risk))
        
        # Generate explanation
        explanation = {
            "port_centrality": f"Port centrality risk: {port_centrality:.2f} (high centrality = high disruption impact)",
            "carrier_redundancy": f"Carrier redundancy risk: {carrier_redundancy:.2f} (lower = better redundancy)",
            "upstream": f"Upstream dependency: {upstream:.2f}",
            "downstream": f"Downstream dependency: {downstream:.2f}",
            "propagation": f"Disruption propagation factor: {propagation:.2f}",
            "overall": f"Combined network risk: {overall_risk:.1%}"
        }
        
        return NetworkRiskScore(
            overall_risk=overall_risk,
            port_centrality=port_centrality,
            carrier_redundancy=carrier_redundancy,
            upstream_dependency=upstream,
            downstream_dependency=downstream,
            propagation_factor=propagation,
            explanation=explanation
        )
















