def compute_saving_vs_lcl(
    lcl_shipments: list[dict],
    containers: list[dict],
    lcl_rate_per_cbm: float,
    fcl_rate_total: float,
) -> dict:
    baseline = sum((s.get("volume", 0.0) or 0.0) * lcl_rate_per_cbm for s in lcl_shipments)
    optimized = fcl_rate_total * max(len(containers), 1)
    saving_amount = baseline - optimized
    saving_percent = (saving_amount / baseline * 100.0) if baseline else 0.0
    return {
        "baseline_lcl_cost": baseline,
        "optimized_fcl_cost": optimized,
        "saving_amount": saving_amount,
        "saving_percent": saving_percent,
    }

