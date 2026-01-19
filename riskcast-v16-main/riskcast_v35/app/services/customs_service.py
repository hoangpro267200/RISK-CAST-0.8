from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.customs import CustomsProfile


class CustomsService:
    """CRUD for customs profiles."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_customs_profile(self, shipment_id: UUID, hs_code: str, declaration_xml: str) -> CustomsProfile:
        profile = (
            self.db.query(CustomsProfile).filter(CustomsProfile.shipment_id == shipment_id).first()
        )
        if profile:
            profile.hs_code = hs_code
            profile.declaration_xml = declaration_xml
        else:
            profile = CustomsProfile(
                shipment_id=shipment_id,
                hs_code=hs_code,
                declaration_xml=declaration_xml,
            )
            self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_customs_profile(self, shipment_id: UUID) -> Optional[CustomsProfile]:
        return self.db.query(CustomsProfile).filter(CustomsProfile.shipment_id == shipment_id).first()









