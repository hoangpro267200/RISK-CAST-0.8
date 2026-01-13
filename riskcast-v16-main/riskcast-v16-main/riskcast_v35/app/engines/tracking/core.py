from uuid import UUID
from datetime import datetime

from app.schemas.tracking import (
    TrackingEventCreateRequest,
    TrackingEventResponse,
    TrackingTimelineResponse,
    RiskPoint,
)
from app.schemas.risk import RiskSnapshotResponse
from app.services.tracking_service import TrackingService
from app.services.risk_service import RiskService
from app.services.shipment_service import ShipmentService


class TrackingEngine:
    """Manages tracking event ingestion and risk recomputation."""

    def __init__(
        self,
        tracking_service: TrackingService,
        risk_service: RiskService,
        shipment_service: ShipmentService,
    ):
        self.tracking_service = tracking_service
        self.risk_service = risk_service
        self.shipment_service = shipment_service

    def ingest_event(self, request: TrackingEventCreateRequest) -> TrackingEventResponse:
        event = self.tracking_service.create_tracking_event(request)
        # Recompute risk for this shipment
        risk = self.recompute_risk_for_shipment(event.shipment_id)
        return TrackingEventResponse.from_orm(event)

    def get_shipment_timeline(self, shipment_id: UUID) -> TrackingTimelineResponse:
        events = self.tracking_service.get_tracking_for_shipment(shipment_id)
        snapshots = self.risk_service.list_snapshots(shipment_id)

        latest_event = events[0] if events else None
        latest_risk = snapshots[0] if snapshots else None

        return TrackingTimelineResponse(
            shipmentId=shipment_id,
            events=[TrackingEventResponse.from_orm(e) for e in events],
            riskTimeline=[
                RiskPoint(
                    timestamp=rs.timestamp,
                    weatherRisk=rs.weather_risk or 0.0,
                    congestionRisk=rs.congestion_risk or 0.0,
                    carrierRisk=rs.carrier_risk or 0.0,
                    totalRisk=rs.total_risk or 0.0,
                )
                for rs in snapshots
            ],
            latestPosition=TrackingEventResponse.from_orm(latest_event) if latest_event else None,
            latestRisk=RiskPoint(
                timestamp=latest_risk.timestamp,
                weatherRisk=latest_risk.weather_risk or 0.0,
                congestionRisk=latest_risk.congestion_risk or 0.0,
                carrierRisk=latest_risk.carrier_risk or 0.0,
                totalRisk=latest_risk.total_risk or 0.0,
            )
            if latest_risk
            else None,
        )

    def recompute_risk_for_shipment(self, shipment_id: UUID) -> RiskSnapshotResponse:
        latest_event = self.tracking_service.get_latest_event(shipment_id)
        shipment = self.shipment_service.get_shipment_by_id(shipment_id)
        context = {
            "lat": latest_event.lat if latest_event else None,
            "lon": latest_event.lon if latest_event else None,
            "pod": shipment.pod if shipment else None,
            "carrier": (shipment.price_info or {}).get("carrier") if shipment and shipment.price_info else None,
        }
        risk_components = self.risk_service.aggregate_risk(context)
        snapshot = self.risk_service.create_risk_snapshot(
            shipment_id, risk_components, timestamp=latest_event.timestamp if latest_event else datetime.utcnow()
        )
        return RiskSnapshotResponse.from_orm(snapshot)
