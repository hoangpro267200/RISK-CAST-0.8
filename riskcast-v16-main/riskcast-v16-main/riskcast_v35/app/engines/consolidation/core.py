from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.engines.consolidation.grouping import extract_lcl_profile, group_shipments_by_lane
from app.engines.consolidation.optimizer_lp import greedy_pack_into_containers
from app.engines.consolidation.savings_calculator import compute_saving_vs_lcl
from app.schemas.consolidation import (
    ConsolidationPlanRequest,
    ConsolidationPlanResponse,
    ContainerAssignment,
)
from app.services.consolidation_service import ConsolidationPlanService
from app.services.rate_service import RateService
from app.services.shipment_service import ShipmentService


class ConsolidationEngine:
    """Consolidates multiple LCL shipments into FCL containers (greedy v1)."""

    def __init__(self, db: Session, shipment_service: ShipmentService, rate_service: RateService):
        self.db = db
        self.shipment_service = shipment_service
        self.rate_service = rate_service
        self.plan_service = ConsolidationPlanService(db)

    def build_plan(self, request: ConsolidationPlanRequest) -> ConsolidationPlanResponse:
        shipments = self._load_shipments(request)
        if not shipments:
            raise ValueError("No shipments found for consolidation")

        grouped = group_shipments_by_lane(shipments)
        # For v1 take first lane group
        lane_key, lane_shipments = next(iter(grouped.items()))
        lcl_profiles = [extract_lcl_profile(s) for s in lane_shipments]

        containers = greedy_pack_into_containers(lcl_profiles, request.container_capacity_cbm)
        savings = compute_saving_vs_lcl(
            lcl_profiles,
            containers,
            request.lcl_rate_per_cbm,
            request.fcl_rate_per_container,
        )

        plan = self.plan_service.create_plan(
            pol=lane_key[0],
            pod=lane_key[1],
            containers=containers,
            baseline_lcl_cost=savings["baseline_lcl_cost"],
            optimized_fcl_cost=savings["optimized_fcl_cost"],
            saving_amount=savings["saving_amount"],
            saving_percent=savings["saving_percent"],
        )

        return ConsolidationPlanResponse(
            planId=plan.id,
            pol=plan.pol,
            pod=plan.pod,
            containers=[
                ContainerAssignment(
                    containerId=c["container_id"],
                    totalVolume=c["total_volume"],
                    totalWeight=c["total_weight"],
                    shipmentIds=[s["shipment_id"] for s in c["shipments"]],
                )
                for c in containers
            ],
            baselineLclCost=float(savings["baseline_lcl_cost"]),
            optimizedFclCost=float(savings["optimized_fcl_cost"]),
            savingAmount=float(savings["saving_amount"]),
            savingPercent=float(savings["saving_percent"]),
            createdAt=plan.created_at or datetime.utcnow(),
        )

    def _load_shipments(self, request: ConsolidationPlanRequest) -> List:
        if request.shipment_ids:
            return self.shipment_service.get_shipments_by_ids(request.shipment_ids)
        if request.pol and request.pod:
            return self.shipment_service.list_shipments_by_lane(
                request.pol, request.pod, request.etd_from, request.etd_to
            )
        return []
