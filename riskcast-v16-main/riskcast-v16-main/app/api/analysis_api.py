from fastapi import APIRouter
from app.services import analysis_service, shipment_service
from app.utils.response import success, failure
from app.utils.logger import log_route

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run")
@log_route
async def run_analysis(payload: dict):
    shipment_id = payload.get("shipmentId") or payload.get("id") or ""
    try:
        result = await analysis_service.run_full_analysis(shipment_id)
        return success(result)
    except Exception as e:
        return failure(str(e))




