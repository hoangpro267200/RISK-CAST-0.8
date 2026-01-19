"""
RISKCAST Region Model - Vietnam
Vietnam-specific risk calibration
"""

VN_REGION_CONFIG = {
    "region_code": "VN",
    "region_name": "Vietnam",
    "climate_weight": 0.70,  # High: monsoon seasons, typhoons
    "congestion_weight": 0.85,  # Very high: major ports like Ho Chi Minh, Hai Phong
    "strike_weight": 0.20,  # Low: relatively stable labor relations
    "esg_weight": 0.30,  # Low-medium: developing ESG standards
    "seasonality_pattern": {
        "q2": {"monsoon": 0.8, "typhoon": 0.6},
        "q3": {"monsoon": 0.9, "typhoon": 0.7},
        "q4": {"monsoon": 0.3, "typhoon": 0.2},
        "q1": {"monsoon": 0.2, "typhoon": 0.1},
    },
    "network_propagation_factor": 0.75,  # Medium-high: dependent on major hubs
    "description": "Vietnam: High monsoon/typhoon risk, significant port congestion at major hubs (Ho Chi Minh, Hai Phong), low strike risk, developing ESG framework. Peak risk Q2-Q3.",
    "characteristics": [
        "Strong monsoon seasons (Q2-Q3) increase weather-related delays",
        "Typhoon risk peaks in late Q3",
        "Major ports experience significant congestion",
        "Growing infrastructure but still developing",
        "Lower labor strike frequency compared to other regions"
    ],
    "major_ports": ["SGN", "HPH", "VUT", "DAD"],
    "peak_seasons": ["Q2", "Q3"],
}




















