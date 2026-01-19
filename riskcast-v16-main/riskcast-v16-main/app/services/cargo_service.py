from typing import Dict
from app.validators.cargo_validator import validate_cargo
from app.models.cargo import Cargo


async def get_cargo(shipment_id: str) -> Cargo:
    return Cargo()


async def update_cargo(shipment_id: str, data: Dict) -> Cargo:
    return validate_cargo(data)




