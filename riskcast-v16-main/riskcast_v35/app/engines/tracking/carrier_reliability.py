def estimate_carrier_risk(carrier_name: str = None) -> float:
    """
    Stub carrier reliability -> risk conversion.
    """
    reliability_map = {
        "MockLine A": 0.8,
        "MockLine B": 0.7,
        "MockLine C": 0.6,
    }
    reliability = reliability_map.get(carrier_name, 0.75)
    return (1 - reliability) * 100









