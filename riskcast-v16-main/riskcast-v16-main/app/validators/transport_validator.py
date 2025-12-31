from datetime import datetime
from typing import List
from app.models.transport import Transport, RouteLeg


def validate_transport(data: dict) -> Transport:
    payload = dict(data or {})
    legs = validate_legs(payload.get("legs") or [])
    return Transport(
        mode=pascal(payload.get("mode") or "Unknown"),
        incoterm=str(payload.get("incoterm") or "N/A"),
        origin=str(payload.get("origin") or "N/A"),
        destination=str(payload.get("destination") or "N/A"),
        eta=parse_date(payload.get("eta")),
        legs=legs,
    )


def validate_legs(legs: List[dict]) -> List[RouteLeg]:
    safe = []
    for idx, leg in enumerate(legs):
        safe.append(
            RouteLeg(
                legNumber=int(leg.get("legNumber") or leg.get("index") or idx + 1),
                fromPort=str(leg.get("fromPort") or leg.get("from") or "N/A"),
                toPort=str(leg.get("toPort") or leg.get("to") or "N/A"),
                mode=pascal(leg.get("mode") or "Unknown"),
                eta=parse_date(leg.get("eta")),
                status=str(leg.get("status") or "Pending"),
            )
        )
    return sorted(safe, key=lambda l: l.legNumber)


def pascal(value: str) -> str:
    s = str(value or "").strip()
    return s.capitalize() if s else "Unknown"


def parse_date(val):
    if not val:
        return None
    try:
        return val if isinstance(val, datetime) else datetime.fromisoformat(str(val))
    except Exception:
        return None




