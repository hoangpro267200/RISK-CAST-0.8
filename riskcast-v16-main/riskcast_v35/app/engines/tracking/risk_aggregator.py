def aggregate_risk_components(weather_risk: float, congestion_risk: float, carrier_risk: float) -> dict:
    """
    Combine risk components into total risk.
    """
    total = 0.5 * weather_risk + 0.3 * congestion_risk + 0.2 * carrier_risk
    return {
        "weather_risk": weather_risk,
        "congestion_risk": congestion_risk,
        "carrier_risk": carrier_risk,
        "total_risk": total,
    }









