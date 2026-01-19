from uuid import UUID

from app.engines.customs.hs_classifier import suggest_hs_from_description
from app.engines.customs.declaration_xml import build_customs_declaration_xml
from app.schemas.customs import (
    HSSuggestionRequest,
    HSSuggestionResponse,
    HSCandidate,
    CustomsDeclarationResponse,
)
from app.services.customs_service import CustomsService
from app.services.shipment_service import ShipmentService


class CustomsEngine:
    """Handles customs-related operations."""

    def __init__(self, customs_service: CustomsService, shipment_service: ShipmentService):
        self.customs_service = customs_service
        self.shipment_service = shipment_service

    def suggest_hs_code(self, request: HSSuggestionRequest) -> HSSuggestionResponse:
        candidates = suggest_hs_from_description(request.description)
        return HSSuggestionResponse(
            description=request.description,
            candidates=[HSCandidate(hsCode=c["hs_code"], label=c["description"], score=c["score"]) for c in candidates],
        )

    def generate_declaration_xml(self, shipment_id: UUID) -> CustomsDeclarationResponse:
        shipment = self.shipment_service.get_shipment_by_id(shipment_id)
        if not shipment:
            raise ValueError("Shipment not found")

        existing = self.customs_service.get_customs_profile(shipment_id)
        hs_code = existing.hs_code if existing and existing.hs_code else "9999"
        xml_content = build_customs_declaration_xml(shipment, hs_code)
        profile = self.customs_service.upsert_customs_profile(shipment_id, hs_code, xml_content)

        # Optionally attach to shipment.customs_info
        try:
            info = shipment.customs_info or {}
            info.update({"hs_code": hs_code, "declaration_xml": xml_content})
            self.shipment_service.attach_customs_info(shipment_id, info)
        except Exception:
            pass

        return CustomsDeclarationResponse(
            shipmentId=shipment_id,
            hsCode=hs_code,
            declarationXml=xml_content,
            createdAt=profile.created_at,
        )

