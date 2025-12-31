from fastapi import APIRouter
from app.services import cargo_service
from app.utils.response import success, failure
from app.utils.logger import log_route

router = APIRouter(prefix="/cargo", tags=["cargo"])


@router.get("/{shipment_id}")
@log_route
async def get_cargo(shipment_id: str):
    try:
        data = await cargo_service.get_cargo(shipment_id)
        return success(data.dict())
    except Exception as e:
        return failure(str(e))


@router.put("/{shipment_id}")
@log_route
async def update_cargo(shipment_id: str, payload: dict):
    try:
        data = await cargo_service.update_cargo(shipment_id, payload)
        return success(data.dict())
    except Exception as e:
        return failure(str(e))




