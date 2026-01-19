from fastapi import APIRouter
from app.services import kpi_service, shipment_service
from app.utils.response import success, failure
from app.utils.logger import log_route

router = APIRouter(prefix="/kpi", tags=["kpi"])


@router.get("/{shipment_id}")
@log_route
async def get_kpi(shipment_id: str):
    try:
        shipment = await shipment_service.get_shipment(shipment_id)
        data = await kpi_service.build_kpi(shipment.dict())
        return success(data.dict())
    except Exception as e:
        return failure(str(e))




