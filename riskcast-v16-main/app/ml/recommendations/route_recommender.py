"""
Route Recommendation Engine

Features:
1. Alternative route suggestions
2. Risk-optimized routing
3. Cost-optimized routing
4. Transit time optimization
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import heapq

from app.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class RouteOption:
    """A route option."""
    route_id: str
    origin_port: str
    destination_port: str
    via_ports: List[str]
    carriers: List[str]
    transit_days: int
    risk_score: float
    estimated_cost_usd: float
    reliability_score: float
    congestion_score: float  # 0 = no congestion, 1 = severe
    reasoning: List[str]


@dataclass
class RouteRecommendation:
    """Route recommendation result."""
    recommended_route: RouteOption
    alternative_routes: List[RouteOption]
    optimization_type: str  # "risk", "cost", "time", "balanced"
    savings_vs_default: Dict[str, float]
    warnings: List[str]


class RouteRecommender:
    """
    Recommends optimal shipping routes based on various criteria.
    """
    
    # Major port connections with base transit times and costs
    PORT_CONNECTIONS = {
        # Asia to North America
        ("CNSHA", "USLAX"): {"days": 14, "cost_per_teu": 2500, "risk": 0.3},
        ("CNSHA", "USNYC"): {"days": 28, "cost_per_teu": 3200, "risk": 0.35},
        ("CNNBO", "USLAX"): {"days": 15, "cost_per_teu": 2400, "risk": 0.28},
        ("JPYOK", "USLAX"): {"days": 12, "cost_per_teu": 2800, "risk": 0.25},
        
        # Asia to Europe
        ("CNSHA", "NLRTM"): {"days": 30, "cost_per_teu": 2800, "risk": 0.32},
        ("CNSHA", "DEHAM"): {"days": 32, "cost_per_teu": 2900, "risk": 0.33},
        ("SGSIN", "NLRTM"): {"days": 22, "cost_per_teu": 2200, "risk": 0.28},
        
        # Europe to North America
        ("NLRTM", "USNYC"): {"days": 10, "cost_per_teu": 1800, "risk": 0.20},
        ("DEHAM", "USNYC"): {"days": 11, "cost_per_teu": 1900, "risk": 0.22},
        ("GBFXT", "USNYC"): {"days": 9, "cost_per_teu": 1700, "risk": 0.18},
        
        # Via transshipment hubs
        ("CNSHA", "SGSIN"): {"days": 6, "cost_per_teu": 800, "risk": 0.15},
        ("SGSIN", "USLAX"): {"days": 18, "cost_per_teu": 2000, "risk": 0.30},
    }
    
    # Carrier performance data
    CARRIER_PERFORMANCE = {
        "MAEU": {"reliability": 0.92, "delay_days_avg": 1.5},
        "MSCU": {"reliability": 0.88, "delay_days_avg": 2.0},
        "CMDU": {"reliability": 0.90, "delay_days_avg": 1.8},
        "COSU": {"reliability": 0.85, "delay_days_avg": 2.5},
        "EGLV": {"reliability": 0.87, "delay_days_avg": 2.2},
        "ONEY": {"reliability": 0.89, "delay_days_avg": 1.9},
    }
    
    def __init__(self):
        self.current_congestion: Dict[str, float] = {}
        self.current_weather_risks: Dict[str, float] = {}
    
    def update_real_time_data(
        self,
        congestion: Dict[str, float],
        weather_risks: Dict[str, float]
    ):
        """Update real-time congestion and weather data."""
        self.current_congestion = congestion
        self.current_weather_risks = weather_risks
    
    def recommend_routes(
        self,
        origin_port: str,
        destination_port: str,
        cargo_value_usd: float,
        container_count: int = 1,
        departure_date: Optional[datetime] = None,
        optimization: str = "balanced",  # "risk", "cost", "time", "balanced"
        max_transit_days: Optional[int] = None
    ) -> RouteRecommendation:
        """
        Recommend optimal routes.
        """
        # Find all possible routes
        all_routes = self._find_all_routes(origin_port, destination_port)
        
        if not all_routes:
            # Return direct route estimation
            direct_route = self._estimate_direct_route(
                origin_port, destination_port, container_count
            )
            return RouteRecommendation(
                recommended_route=direct_route,
                alternative_routes=[],
                optimization_type=optimization,
                savings_vs_default={},
                warnings=["No established routes found, using estimation"]
            )
        
        # Score and rank routes
        scored_routes = []
        for route in all_routes:
            score = self._score_route(route, optimization, cargo_value_usd)
            scored_routes.append((score, route))
        
        # Sort by score (higher is better)
        scored_routes.sort(reverse=True, key=lambda x: x[0])
        
        # Filter by max transit days if specified
        if max_transit_days:
            scored_routes = [
                (s, r) for s, r in scored_routes
                if r.transit_days <= max_transit_days
            ]
        
        if not scored_routes:
            return RouteRecommendation(
                recommended_route=all_routes[0],
                alternative_routes=[],
                optimization_type=optimization,
                savings_vs_default={},
                warnings=["No routes meet transit time requirements"]
            )
        
        # Top route is recommended
        recommended = scored_routes[0][1]
        alternatives = [r for _, r in scored_routes[1:4]]  # Up to 3 alternatives
        
        # Calculate savings vs default (first found route)
        default_route = all_routes[0]
        savings = self._calculate_savings(recommended, default_route)
        
        # Generate warnings
        warnings = self._generate_warnings(recommended)
        
        return RouteRecommendation(
            recommended_route=recommended,
            alternative_routes=alternatives,
            optimization_type=optimization,
            savings_vs_default=savings,
            warnings=warnings
        )
    
    def _find_all_routes(
        self,
        origin: str,
        destination: str
    ) -> List[RouteOption]:
        """Find all possible routes between two ports."""
        routes = []
        
        # Direct route
        direct_key = (origin, destination)
        if direct_key in self.PORT_CONNECTIONS:
            conn = self.PORT_CONNECTIONS[direct_key]
            routes.append(self._create_route_option(
                origin, destination, [], conn
            ))
        
        # Routes via transshipment
        transship_hubs = ["SGSIN", "AEDXB", "MAPTM", "NLRTM"]
        
        for hub in transship_hubs:
            if hub == origin or hub == destination:
                continue
            
            leg1_key = (origin, hub)
            leg2_key = (hub, destination)
            
            if leg1_key in self.PORT_CONNECTIONS and leg2_key in self.PORT_CONNECTIONS:
                leg1 = self.PORT_CONNECTIONS[leg1_key]
                leg2 = self.PORT_CONNECTIONS[leg2_key]
                
                combined = {
                    "days": leg1["days"] + leg2["days"] + 2,  # 2 days for transshipment
                    "cost_per_teu": leg1["cost_per_teu"] + leg2["cost_per_teu"] + 200,
                    "risk": 1 - (1 - leg1["risk"]) * (1 - leg2["risk"])  # Combined risk
                }
                
                routes.append(self._create_route_option(
                    origin, destination, [hub], combined
                ))
        
        return routes
    
    def _create_route_option(
        self,
        origin: str,
        destination: str,
        via_ports: List[str],
        connection: Dict
    ) -> RouteOption:
        """Create a route option from connection data."""
        # Adjust for current conditions
        congestion = max(
            self.current_congestion.get(origin, 0),
            self.current_congestion.get(destination, 0),
            *[self.current_congestion.get(p, 0) for p in via_ports]
        )
        
        weather_risk = max(
            self.current_weather_risks.get(origin, 0),
            self.current_weather_risks.get(destination, 0)
        )
        
        # Adjust transit days for congestion
        adjusted_days = int(connection["days"] * (1 + congestion * 0.3))
        
        # Adjust risk for weather
        adjusted_risk = min(connection["risk"] + weather_risk * 0.2, 0.95)
        
        # Select carriers
        carriers = self._select_carriers(origin, destination)
        reliability = sum(
            self.CARRIER_PERFORMANCE.get(c, {}).get("reliability", 0.8)
            for c in carriers
        ) / len(carriers)
        
        # Generate reasoning
        reasoning = []
        if via_ports:
            reasoning.append(f"Transshipment via {', '.join(via_ports)}")
        if congestion > 0.3:
            reasoning.append(f"Current congestion may add {int(congestion * connection['days'] * 0.3)} days")
        if weather_risk > 0.2:
            reasoning.append("Weather conditions may impact transit")
        
        route_id = f"{origin}-{'-'.join(via_ports)}-{destination}" if via_ports else f"{origin}-{destination}"
        
        return RouteOption(
            route_id=route_id,
            origin_port=origin,
            destination_port=destination,
            via_ports=via_ports,
            carriers=carriers,
            transit_days=adjusted_days,
            risk_score=adjusted_risk,
            estimated_cost_usd=connection["cost_per_teu"],
            reliability_score=reliability,
            congestion_score=congestion,
            reasoning=reasoning
        )
    
    def _select_carriers(self, origin: str, destination: str) -> List[str]:
        """Select available carriers for route."""
        # In real implementation, this would check actual carrier schedules
        # For now, return top carriers by reliability
        carriers = sorted(
            self.CARRIER_PERFORMANCE.keys(),
            key=lambda c: self.CARRIER_PERFORMANCE[c]["reliability"],
            reverse=True
        )
        return carriers[:3]
    
    def _score_route(
        self,
        route: RouteOption,
        optimization: str,
        cargo_value_usd: float
    ) -> float:
        """Score a route based on optimization criteria."""
        # Normalize metrics to 0-1 scale (higher is better)
        time_score = 1 - (route.transit_days / 60)  # Max 60 days
        cost_score = 1 - (route.estimated_cost_usd / 5000)  # Max $5000/TEU
        risk_score = 1 - route.risk_score
        reliability_score = route.reliability_score
        
        # Weights based on optimization type
        weights = {
            "risk": {"time": 0.1, "cost": 0.1, "risk": 0.6, "reliability": 0.2},
            "cost": {"time": 0.2, "cost": 0.5, "risk": 0.15, "reliability": 0.15},
            "time": {"time": 0.5, "cost": 0.15, "risk": 0.2, "reliability": 0.15},
            "balanced": {"time": 0.25, "cost": 0.25, "risk": 0.25, "reliability": 0.25},
        }
        
        w = weights.get(optimization, weights["balanced"])
        
        # Adjust weights based on cargo value
        if cargo_value_usd > 1000000:
            # High value = prioritize risk
            w["risk"] *= 1.5
        
        # Normalize weights
        total = sum(w.values())
        w = {k: v/total for k, v in w.items()}
        
        score = (
            w["time"] * time_score +
            w["cost"] * cost_score +
            w["risk"] * risk_score +
            w["reliability"] * reliability_score
        )
        
        return score
    
    def _calculate_savings(
        self,
        recommended: RouteOption,
        default: RouteOption
    ) -> Dict[str, float]:
        """Calculate savings vs default route."""
        return {
            "transit_days": default.transit_days - recommended.transit_days,
            "cost_usd": default.estimated_cost_usd - recommended.estimated_cost_usd,
            "risk_reduction": default.risk_score - recommended.risk_score
        }
    
    def _generate_warnings(self, route: RouteOption) -> List[str]:
        """Generate warnings for a route."""
        warnings = []
        
        if route.congestion_score > 0.5:
            warnings.append(f"High congestion at ports may cause delays")
        
        if route.risk_score > 0.5:
            warnings.append(f"Elevated risk on this route ({route.risk_score:.0%})")
        
        if route.reliability_score < 0.85:
            warnings.append(f"Carrier reliability below average")
        
        if len(route.via_ports) > 1:
            warnings.append("Multiple transshipments increase handling risk")
        
        return warnings
    
    def _estimate_direct_route(
        self,
        origin: str,
        destination: str,
        container_count: int
    ) -> RouteOption:
        """Estimate a direct route when no data available."""
        # Very rough estimation based on geographic assumptions
        return RouteOption(
            route_id=f"{origin}-{destination}-EST",
            origin_port=origin,
            destination_port=destination,
            via_ports=[],
            carriers=["MAEU", "MSCU"],
            transit_days=21,
            risk_score=0.35,
            estimated_cost_usd=2500 * container_count,
            reliability_score=0.85,
            congestion_score=0.3,
            reasoning=["Estimated route - actual transit may vary"]
        )
