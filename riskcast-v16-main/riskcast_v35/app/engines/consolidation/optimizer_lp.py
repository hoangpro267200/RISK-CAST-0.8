from typing import List, Dict


def greedy_pack_into_containers(lcl_shipments: List[Dict], container_capacity_cbm: float) -> List[Dict]:
    """
    Simple greedy packing by volume descending.
    TODO: Replace with LP optimizer for better utilization.
    """
    sorted_shipments = sorted(lcl_shipments, key=lambda x: x.get("volume", 0), reverse=True)
    containers = []
    current = {"container_id": f"CONT-1", "total_volume": 0.0, "total_weight": 0.0, "shipments": []}
    idx = 1

    for s in sorted_shipments:
        vol = s.get("volume", 0.0)
        if current["total_volume"] + vol > container_capacity_cbm and current["shipments"]:
            containers.append(current)
            idx += 1
            current = {"container_id": f"CONT-{idx}", "total_volume": 0.0, "total_weight": 0.0, "shipments": []}
        current["shipments"].append(s)
        current["total_volume"] += vol
        current["total_weight"] += s.get("weight", 0.0)
    if current["shipments"]:
        containers.append(current)
    return containers

