from fastapi import APIRouter
from app.services import transport_service
from app.utils.response import success, failure
from app.utils.logger import log_route

router = APIRouter(prefix="/transport", tags=["transport"])


@router.get("/{shipment_id}")
@log_route
async def get_transport(shipment_id: str):
    try:
        data = await transport_service.get_transport(shipment_id)
        return success(data.dict())
    except Exception as e:
        return failure(str(e))


@router.put("/{shipment_id}")
@log_route
async def update_transport(shipment_id: str, payload: dict):
    try:
        data = await transport_service.update_transport(shipment_id, payload)
        return success(data.dict())
    except Exception as e:
        return failure(str(e))




