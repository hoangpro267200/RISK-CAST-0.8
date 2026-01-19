from sqlalchemy.orm import Session


class VesselMapper:
    \"\"\"Links AIS vessel data to shipments.\"\"\"

    def __init__(self, db: Session):
        self.db = db

    def map_vessel_to_shipments(self, vessel_imo: str) -> list:
        return []

