"""
RISKCAST Region Model - Global
Global/default risk calibration
"""

GLOBAL_REGION_CONFIG = {
    "region_code": "GLOBAL",
    "region_name": "Global",
    "climate_weight": 0.60,  # Balanced average
    "congestion_weight": 0.70,  # Balanced average
    "strike_weight": 0.50,  # Balanced average
    "esg_weight": 0.45,  # Balanced average
    "seasonality_pattern": {
        "q1": {"normal": 0.5},
        "q2": {"normal": 0.5},
        "q3": {"normal": 0.5},
        "q4": {"normal": 0.5},
    },
    "network_propagation_factor": 0.70,  # Balanced average
    "description": "Global: Balanced risk calibration suitable for international routes without specific region characteristics.",
    "characteristics": [
        "Balanced risk assessment for global routes",
        "No specific regional patterns",
        "Average weights across all factors"
    ],
    "major_ports": [],
    "peak_seasons": [],
}




















