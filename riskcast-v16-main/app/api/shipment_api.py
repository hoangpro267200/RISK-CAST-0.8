from fastapi import APIRouter, HTTPException
from app.services import shipment_service
from app.utils.response import success, failure
from app.utils.logger import log_route

router = APIRouter(prefix="/shipment", tags=["shipment"])


@router.get("/{shipment_id}")
@log_route
async def get_shipment(shipment_id: str):
    try:
        data = await shipment_service.get_shipment(shipment_id)
        return success(data.dict())
    except Exception as e:
        return failure(str(e))


@router.post("")
@log_route
async def create_shipment(payload: dict):
    try:
        data = await shipment_service.create_shipment(payload)
        return success(data.dict())
    except Exception as e:
        return failure(str(e))


@router.put("/{shipment_id}")
@log_route
async def update_shipment(shipment_id: str, payload: dict):
    try:
        data = await shipment_service.update_shipment(shipment_id, payload)
        return success(data.dict())
    except Exception as e:
        return failure(str(e))


@router.delete("/{shipment_id}")
@log_route
async def delete_shipment(shipment_id: str):
    try:
        await shipment_service.delete_shipment(shipment_id)
        return success(True)
    except Exception as e:
        return failure(str(e))




