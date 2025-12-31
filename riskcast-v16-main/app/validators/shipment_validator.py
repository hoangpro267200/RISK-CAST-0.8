from typing import List
from datetime import datetime
from app.models.shipment_schema import Shipment
from app.models.transport import RouteLeg
from app.validators.transport_validator import validate_transport
from app.validators.cargo_validator import validate_cargo
from app.validators.risk_validator import validate_risk_modules
from app.validators.kpi_validator import validate_kpi


def validate_shipment(payload: dict) -> Shipment:
  data = dict(payload or {})
  shipment_id = str(data.get("shipmentId") or data.get("id") or "").strip()
  transport = validate_transport(data.get("transport") or {})
  cargo = validate_cargo(data.get("cargo") or {})
  risk_modules = validate_risk_modules(data.get("riskModules") or data.get("modules") or [])
  kpi = validate_kpi(data.get("kpi") or {})
  legs = sort_legs(data.get("legs") or transport.legs)
  updated_at = parse_date(data.get("updatedAt"))
  return Shipment(
    shipmentId=shipment_id,
    state=str(data.get("state") or "UNKNOWN"),
    transport=transport,
    cargo=cargo,
    riskModules=risk_modules,
    kpi=kpi,
    legs=legs,
    updatedAt=updated_at,
  )


def sort_legs(legs: List[dict]) -> List[RouteLeg]:
  safe = []
  for idx, leg in enumerate(legs or []):
    safe.append(RouteLeg(
      legNumber=int(leg.get("legNumber") or leg.get("index") or idx + 1),
      fromPort=str(leg.get("fromPort") or leg.get("from") or "N/A"),
      toPort=str(leg.get("toPort") or leg.get("to") or "N/A"),
      mode=str(leg.get("mode") or "Unknown").title(),
      eta=parse_date(leg.get("eta")),
      status=str(leg.get("status") or "Pending")
    ))
  return sorted(safe, key=lambda l: l.legNumber)


def parse_date(val):
  if not val:
    return None
  try:
    return val if isinstance(val, datetime) else datetime.fromisoformat(str(val))
  except Exception:
    return None




