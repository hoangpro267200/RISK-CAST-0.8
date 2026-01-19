"""
RISKCAST Region Model - European Union
European Union risk calibration
"""

EU_REGION_CONFIG = {
    "region_code": "EU",
    "region_name": "European Union",
    "climate_weight": 0.40,  # Medium: milder weather, but winter storms
    "congestion_weight": 0.60,  # Medium: well-developed infrastructure
    "strike_weight": 0.80,  # Very high: strong labor unions, frequent strikes
    "esg_weight": 0.75,  # High: strict ESG regulations
    "seasonality_pattern": {
        "q1": {"winter": 0.5, "strike": 0.6},
        "q2": {"normal": 0.4},
        "q3": {"summer": 0.3, "strike": 0.5},
        "q4": {"winter": 0.4, "strike": 0.7},  # Peak strike season
    },
    "network_propagation_factor": 0.70,  # Medium-high: interconnected but resilient
    "description": "European Union: High strike risk due to strong labor unions, strict ESG regulations, medium congestion. Port strikes are common, especially at major hubs like Rotterdam, Hamburg, and Antwerp.",
    "characteristics": [
        "Port strikes are common, especially at major hubs like Rotterdam, Hamburg, and Antwerp",
        "EU strike patterns show peak activity in Q1 and Q4",
        "Strict ESG compliance requirements",
        "Well-developed infrastructure reduces congestion risk",
        "Winter weather can impact northern ports"
    ],
    "major_ports": ["RTM", "HAM", "ANT", "FEL", "BRV", "LON"],
    "peak_seasons": ["Q1", "Q4"],
}




















