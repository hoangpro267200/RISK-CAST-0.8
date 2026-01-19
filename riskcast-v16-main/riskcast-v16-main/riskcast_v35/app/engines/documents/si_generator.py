from app.models.shipment import Shipment


def build_si_from_shipment(shipment: Shipment) -> dict:
    """
    Build a simple SI content structure from shipment data.
    TODO: Enrich with container and schedule details.
    """
    docs_info = getattr(shipment, "documents_info", {}) or {}
    return {
        "shipper_name": getattr(shipment, "shipper_name", None),
        "consignee_name": getattr(shipment, "consignee_name", None),
        "notify_party": docs_info.get("notify_party"),
        "pol": shipment.pol,
        "pod": shipment.pod,
        "vessel_voyage": docs_info.get("vessel_voyage"),
        "goods_description": docs_info.get("goods_description"),
        "weight": docs_info.get("weight"),
        "volume": docs_info.get("volume"),
        "container_list": docs_info.get("container_list", []),
    }

