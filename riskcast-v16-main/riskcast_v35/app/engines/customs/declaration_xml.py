import xml.etree.ElementTree as ET

from app.models.shipment import Shipment


def build_customs_declaration_xml(shipment: Shipment, hs_code: str) -> str:
    """
    Build a minimal customs declaration XML.
    """
    root = ET.Element("Declaration")
    ET.SubElement(root, "ShipmentRef").text = str(shipment.id)
    ET.SubElement(root, "Shipper").text = shipment.shipper_name or ""
    ET.SubElement(root, "Consignee").text = shipment.consignee_name or ""
    ET.SubElement(root, "POL").text = shipment.pol
    ET.SubElement(root, "POD").text = shipment.pod
    ET.SubElement(root, "HSCode").text = hs_code
    cargo = shipment.cargo_profile or {}
    ET.SubElement(root, "GoodsDescription").text = cargo.get("description") or ""
    ET.SubElement(root, "TotalWeight").text = str(cargo.get("weight") or cargo.get("weight_kg") or 0)
    ET.SubElement(root, "TotalVolume").text = str(cargo.get("volume") or cargo.get("volume_cbm") or 0)
    return ET.tostring(root, encoding="unicode")









