"""
RISKCAST Region Model - United States
United States risk calibration
"""

US_REGION_CONFIG = {
    "region_code": "US",
    "region_name": "United States",
    "climate_weight": 0.90,  # Very high: hurricanes, winter storms, wildfires
    "congestion_weight": 0.70,  # High: major port congestion, especially LA/LB
    "strike_weight": 0.85,  # Very high: strong unions, ILWU negotiations
    "esg_weight": 0.40,  # Medium: developing framework
    "seasonality_pattern": {
        "q2": {"hurricane_prep": 0.5},
        "q3": {"hurricane": 0.7, "wildfire": 0.6},  # Hurricane season
        "q4": {"hurricane": 0.8, "congestion": 0.8},  # Peak hurricane + peak season
        "q1": {"winter": 0.6, "strike": 0.5},
    },
    "network_propagation_factor": 0.75,  # Medium-high: major gateways create bottlenecks
    "description": "United States: Very high climate risk (hurricanes, winter storms), high congestion at major ports (LA/LB, NYC), very high strike risk. ILWU labor negotiations can cause volatility at LA/LB terminals.",
    "characteristics": [
        "ILWU labor negotiations can cause volatility at LA/LB terminals",
        "Hurricane season (Q3-Q4) significantly impacts Gulf and East Coast ports",
        "Major port congestion at LA/LB, NYC, and other gateways",
        "Winter storms impact northern ports",
        "Strong labor unions create strike risk"
    ],
    "major_ports": ["LAX", "LB", "NYC", "JFK", "SAV", "HOU"],
    "peak_seasons": ["Q3", "Q4"],
}




















