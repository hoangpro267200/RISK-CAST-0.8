from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.documents import DocumentCreate


class DocumentService:
    """Document CRUD and template handling service."""

    def __init__(self, db: Session):
        self.db = db

    def create_document(self, data: DocumentCreate) -> Document:
        doc = Document(**data.dict(by_alias=True))
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_documents_by_shipment(self, shipment_id: UUID) -> List[Document]:
        return (
            self.db.query(Document)
            .filter(Document.shipment_id == shipment_id)
            .order_by(Document.created_at.desc())
            .all()
        )

    def update_document_content(self, document_id: UUID, content_json) -> Optional[Document]:
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return None
        doc.content_json = content_json
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def list_documents(self) -> List[Document]:
        return self.db.query(Document).order_by(Document.created_at.desc()).all()

