from typing import Any, Dict
from uuid import UUID

from app.engines.documents.si_generator import build_si_from_shipment
from app.engines.documents.bl_generator import build_draft_bl_from_si
from app.engines.documents.validator import compare_si_and_bl
from app.schemas.documents import DocumentCreate
from app.services.document_service import DocumentService
from app.services.shipment_service import ShipmentService


class DocumentsEngine:
    \"\"\"Handles SI and Draft B/L generation and validation.\"\"\"

    def __init__(self, document_service: DocumentService, shipment_service: ShipmentService):
        self.document_service = document_service
        self.shipment_service = shipment_service

    def generate_si(self, shipment_id: UUID):
        shipment = self.shipment_service.get_shipment_by_id(shipment_id)
        if not shipment:
            raise ValueError(\"Shipment not found\")

        si_content = build_si_from_shipment(shipment)
        doc = self.document_service.create_document(
            DocumentCreate(
                shipment_id=shipment_id,
                doc_type=\"SI\",
                content_json=si_content,
                file_path=None,
                status=\"draft\",
            )
        )
        return doc

    def generate_draft_bl(self, shipment_id: UUID):
        shipment = self.shipment_service.get_shipment_by_id(shipment_id)
        if not shipment:
            raise ValueError(\"Shipment not found\")

        si_doc = self._get_latest_doc(shipment_id, \"SI\")
        si_content = si_doc.content_json if si_doc else build_si_from_shipment(shipment)

        bl_content = build_draft_bl_from_si(si_content)
        doc = self.document_service.create_document(
            DocumentCreate(
                shipment_id=shipment_id,
                doc_type=\"BL_DRAFT\",
                content_json=bl_content,
                file_path=None,
                status=\"draft\",
            )
        )
        return doc

    def validate_bl_against_si(self, shipment_id: UUID) -> Dict[str, Any]:
        si_doc = self._get_latest_doc(shipment_id, \"SI\")
        bl_doc = self._get_latest_doc(shipment_id, \"BL_DRAFT\")

        if not si_doc or not bl_doc:
            return {
                \"is_valid\": False,
                \"differences\": [
                    {\"field\": \"document_presence\", \"si\": bool(si_doc), \"bl\": bool(bl_doc)}
                ],
            }

        return compare_si_and_bl(si_doc.content_json, bl_doc.content_json)

    def _get_latest_doc(self, shipment_id: UUID, doc_type: str):
        docs = self.document_service.get_documents_by_shipment(shipment_id)
        for doc in docs:
            if doc.doc_type == doc_type:
                return doc
        return None

