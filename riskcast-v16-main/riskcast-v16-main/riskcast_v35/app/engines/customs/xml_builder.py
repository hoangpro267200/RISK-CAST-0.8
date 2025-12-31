from app.engines.customs.declaration_xml import build_customs_declaration_xml
from app.models.shipment import Shipment


class VNACCSXMLBuilder:
    """Generates VNACCS-style XML for customs declaration."""

    def build_vnaccs_xml(self, shipment_data: Shipment, customs_profile: dict) -> str:
        hs_code = customs_profile.get("hs_code") if customs_profile else "9999"
        return build_customs_declaration_xml(shipment_data, hs_code)

