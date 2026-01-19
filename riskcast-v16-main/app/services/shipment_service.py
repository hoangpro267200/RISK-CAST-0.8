from functools import lru_cache
from typing import Dict
from app.validators.shipment_validator import validate_shipment
from app.models.shipment_schema import Shipment


@lru_cache(maxsize=128)
def _cache_get(shipment_id: str) -> Shipment:
    # placeholder cache, would hook to DB/redis
    return Shipment(shipmentId=shipment_id)


async def get_shipment(shipment_id: str) -> Shipment:
    return _cache_get(shipment_id)


async def update_shipment(shipment_id: str, data: Dict) -> Shipment:
    shipment = validate_shipment({"shipmentId": shipment_id, **(data or {})})
    _cache_get.cache_clear()
    _cache_get.cache_update({(shipment_id,): shipment}) if hasattr(_cache_get, "cache_update") else None
    return shipment


async def create_shipment(data: Dict) -> Shipment:
    shipment = validate_shipment(data)
    return shipment


async def delete_shipment(shipment_id: str) -> bool:
    _cache_get.cache_clear()
    return True




