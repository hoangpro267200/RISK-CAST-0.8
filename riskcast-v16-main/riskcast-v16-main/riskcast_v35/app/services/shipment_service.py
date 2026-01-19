from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.shipment import Shipment
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate


class ShipmentService:
    """Shipment lifecycle service with basic CRUD and attachment helpers."""

    def __init__(self, db: Session):
        self.db = db

    def create_shipment(self, data: ShipmentCreate) -> Shipment:
        shipment = Shipment(**data.dict(by_alias=True))
        self.db.add(shipment)
        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def get_shipment_by_id(self, shipment_id: UUID) -> Optional[Shipment]:
        return self.db.query(Shipment).filter(Shipment.id == shipment_id).first()

    def list_shipments(
        self, status: Optional[str] = None, pol: Optional[str] = None, pod: Optional[str] = None
    ) -> List[Shipment]:
        query = self.db.query(Shipment)
        if status:
            query = query.filter(Shipment.status == status)
        if pol:
            query = query.filter(Shipment.pol == pol)
        if pod:
            query = query.filter(Shipment.pod == pod)
        return query.all()

    def update_shipment(self, shipment_id: UUID, data: ShipmentUpdate) -> Optional[Shipment]:
        shipment = self.get_shipment_by_id(shipment_id)
        if not shipment:
            return None
        update_data = data.dict(exclude_unset=True, by_alias=True)
        for key, value in update_data.items():
            setattr(shipment, key, value)
        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def delete_shipment(self, shipment_id: UUID) -> bool:
        shipment = self.get_shipment_by_id(shipment_id)
        if not shipment:
            return False
        self.db.delete(shipment)
        self.db.commit()
        return True

    def get_shipments_by_ids(self, shipment_ids: List[UUID]) -> List[Shipment]:
        if not shipment_ids:
            return []
        return self.db.query(Shipment).filter(Shipment.id.in_(shipment_ids)).all()

    def list_shipments_by_lane(
        self,
        pol: str,
        pod: str,
        etd_from: Optional[datetime] = None,
        etd_to: Optional[datetime] = None,
    ) -> List[Shipment]:
        query = self.db.query(Shipment).filter(Shipment.pol == pol, Shipment.pod == pod)
        if etd_from:
            query = query.filter(Shipment.etd >= etd_from)
        if etd_to:
            query = query.filter(Shipment.etd <= etd_to)
        return query.all()

    def attach_price_info(self, shipment_id: UUID, price_info) -> Optional[Shipment]:
        shipment = self.get_shipment_by_id(shipment_id)
        if not shipment:
            return None
        shipment.price_info = price_info
        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def attach_consolidation_info(self, shipment_id: UUID, consolidation_info) -> Optional[Shipment]:
        shipment = self.get_shipment_by_id(shipment_id)
        if not shipment:
            return None
        shipment.consolidation_info = consolidation_info
        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def attach_documents_info(self, shipment_id: UUID, documents_info) -> Optional[Shipment]:
        shipment = self.get_shipment_by_id(shipment_id)
        if not shipment:
            return None
        shipment.documents_info = documents_info
        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def attach_customs_info(self, shipment_id: UUID, customs_info) -> Optional[Shipment]:
        shipment = self.get_shipment_by_id(shipment_id)
        if not shipment:
            return None
        shipment.customs_info = customs_info
        self.db.commit()
        self.db.refresh(shipment)
        return shipment

    def attach_risk_info(self, shipment_id: UUID, risk_info) -> Optional[Shipment]:
        shipment = self.get_shipment_by_id(shipment_id)
        if not shipment:
            return None
        shipment.risk_info = risk_info
        self.db.commit()
        self.db.refresh(shipment)
        return shipment

