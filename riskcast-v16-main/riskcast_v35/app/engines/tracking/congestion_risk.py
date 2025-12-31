def estimate_congestion_risk(port_code: str = None) -> float:
    """
    Stub congestion risk estimator.
    TODO: integrate real congestion data later.
    """
    congested_ports = {"SGSIN", "USLAX", "USNYC"}
    if port_code and port_code.upper() in congested_ports:
        return 35.0
    return 15.0









