"""
RISKCAST Region Model - Southeast Asia
Southeast Asia (SEA) risk calibration
"""

SEA_REGION_CONFIG = {
    "region_code": "SEA",
    "region_name": "Southeast Asia",
    "climate_weight": 0.75,  # Very high: monsoon, typhoons across region
    "congestion_weight": 0.90,  # Very high: Singapore PSA, major transshipment hubs
    "strike_weight": 0.30,  # Low-medium: varies by country
    "esg_weight": 0.35,  # Low-medium: developing standards
    "seasonality_pattern": {
        "q2": {"monsoon": 0.8, "typhoon": 0.5},
        "q3": {"monsoon": 0.85, "typhoon": 0.6},
        "q4": {"monsoon": 0.4, "typhoon": 0.3},
        "q1": {"monsoon": 0.3, "typhoon": 0.2},
    },
    "network_propagation_factor": 0.85,  # High: Singapore as major hub creates cascade effects
    "description": "Southeast Asia: Very high monsoon/typhoon risk, extreme congestion at major transshipment ports (Singapore PSA), medium strike risk, developing ESG standards. Southwest monsoon reduces throughput at major hubs.",
    "characteristics": [
        "Southwest monsoon typically reduces throughput at major transshipment ports such as Singapore PSA",
        "Singapore PSA experiences significant congestion during peak seasons",
        "High network propagation due to hub-and-spoke model",
        "Typhoon risk across Philippines and surrounding areas",
        "Mixed labor relations across countries"
    ],
    "major_ports": ["SIN", "SGN", "BKK", "JKT", "MNL", "HPH"],
    "peak_seasons": ["Q2", "Q3"],
}




















