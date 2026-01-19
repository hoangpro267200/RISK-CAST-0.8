from typing import Dict


async def generate_ai_insight(shipment: Dict) -> Dict:
    name = shipment.get("shipmentId") or "shipment"
    return {"insight": f"Insight for {name}: risk is moderate with congestion watch."}




