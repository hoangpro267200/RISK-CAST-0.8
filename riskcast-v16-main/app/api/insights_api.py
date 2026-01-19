from fastapi import APIRouter
from app.services import insights_service, shipment_service
from app.utils.response import success, failure
from app.utils.logger import log_route

router = APIRouter(prefix="/insights", tags=["insights"])


@router.post("/ai")
@log_route
async def ai_insight(payload: dict):
    try:
        shipment_id = payload.get("shipmentId") or ""
        shipment = await shipment_service.get_shipment(shipment_id)
        result = await insights_service.generate_ai_insight(shipment.dict())
        return success(result)
    except Exception as e:
        return failure(str(e))




