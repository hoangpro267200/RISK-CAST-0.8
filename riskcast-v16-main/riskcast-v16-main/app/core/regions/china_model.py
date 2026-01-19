"""
RISKCAST Region Model - China
China-specific risk calibration
"""

CHINA_REGION_CONFIG = {
    "region_code": "CN",
    "region_name": "China",
    "climate_weight": 0.45,  # Medium: less severe than SEA but still present
    "congestion_weight": 0.95,  # Very high: extreme congestion at major ports
    "strike_weight": 0.10,  # Very low: strict labor control
    "esg_weight": 0.15,  # Low: developing framework
    "seasonality_pattern": {
        "q1": {"new_year": 0.9, "congestion": 0.8},  # Chinese New Year
        "q2": {"normal": 0.5},
        "q3": {"typhoon": 0.4},
        "q4": {"golden_week": 0.85, "congestion": 0.9},  # Golden Week
    },
    "network_propagation_factor": 0.80,  # High: major manufacturing hubs create dependencies
    "description": "China: Extreme port congestion at major ports (Ningbo, Shanghai, Shenzhen), very low strike risk, low ESG weight. Golden Week causes predictable congestion spikes. Chinese New Year significantly impacts Q1 operations.",
    "characteristics": [
        "Golden Week causes predictable congestion spikes in Ningbo, Shanghai, and Shenzhen",
        "Chinese New Year (Q1) creates major disruptions",
        "Extreme congestion at major container ports",
        "Very low labor strike risk due to labor regulations",
        "High network dependency on manufacturing hubs"
    ],
    "major_ports": ["NGB", "SHA", "SZX", "QIN", "XMN", "YAN"],
    "peak_seasons": ["Q1", "Q4"],
}















