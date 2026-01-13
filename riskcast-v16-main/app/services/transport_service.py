from typing import Dict
from app.validators.transport_validator import validate_transport
from app.models.transport import Transport


async def get_transport(shipment_id: str) -> Transport:
    return Transport(mode="Unknown", incoterm="N/A", origin="N/A", destination="N/A", legs=[])


async def update_transport(shipment_id: str, data: Dict) -> Transport:
    return validate_transport(data)




