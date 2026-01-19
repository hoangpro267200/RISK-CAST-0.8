from typing import List, Dict, Tuple

from app.models.shipment import Shipment


def group_shipments_by_lane(shipments: List[Shipment]) -> Dict[Tuple[str, str], List[Shipment]]:
    """
    Group shipments by (pol, pod).
    """
    grouped = {}
    for s in shipments:
        key = (s.pol, s.pod)
        grouped.setdefault(key, []).append(s)
    return grouped


def extract_lcl_profile(shipment: Shipment) -> dict:
    """
    Extract minimal LCL profile for packing.
    """
    cargo = shipment.cargo_profile or {}
    return {
        "shipment_id": shipment.id,
        "weight": float(cargo.get("weight") or cargo.get("weight_kg") or 0.0),
        "volume": float(cargo.get("volume") or cargo.get("volume_cbm") or 0.0),
        "pol": shipment.pol,
        "pod": shipment.pod,
        "etd": shipment.etd,
    }

