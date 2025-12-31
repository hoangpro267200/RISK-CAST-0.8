from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session

from app.models.consolidation import ConsolidationPlan


class ConsolidationPlanService:
    """CRUD for consolidation plans."""

    def __init__(self, db: Session):
        self.db = db

    def create_plan(
        self,
        pol: str,
        pod: str,
        containers: list,
        baseline_lcl_cost: float,
        optimized_fcl_cost: float,
        saving_amount: float,
        saving_percent: float,
        vessel_voyage: Optional[str] = None,
    ) -> ConsolidationPlan:
        plan = ConsolidationPlan(
            pol=pol,
            pod=pod,
            containers=containers,
            baseline_lcl_cost=baseline_lcl_cost,
            optimized_fcl_cost=optimized_fcl_cost,
            saving_amount=saving_amount,
            saving_percent=saving_percent,
            vessel_voyage=vessel_voyage,
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_plan_by_id(self, plan_id: UUID) -> Optional[ConsolidationPlan]:
        return self.db.query(ConsolidationPlan).filter(ConsolidationPlan.id == plan_id).first()

    def get_latest_plan_for_shipment(self, shipment_id: UUID) -> Optional[ConsolidationPlan]:
        plans = (
            self.db.query(ConsolidationPlan)
            .order_by(ConsolidationPlan.created_at.desc())
            .all()
        )
        for plan in plans:
            containers = plan.containers or []
            for c in containers:
                shipment_ids = [s.get("shipment_id") for s in c.get("shipments", [])]
                if shipment_id in shipment_ids:
                    return plan
        return None

