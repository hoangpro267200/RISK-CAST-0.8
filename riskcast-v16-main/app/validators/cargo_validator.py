from app.models.cargo import Cargo


def validate_cargo(data: dict) -> Cargo:
    payload = dict(data or {})
    weight = abs(to_float(payload.get("weight", 0)))
    volume = abs(to_float(payload.get("volume", 0)))
    value = abs(to_float(payload.get("value") or payload.get("valueUSD") or 0))
    return Cargo(
        type=str(payload.get("type") or payload.get("cargoType") or "Unknown"),
        hsCode=str(payload.get("hsCode") or "N/A"),
        weight=weight,
        volume=volume,
        value=value,
        insurance=str(payload.get("insurance") or "N/A"),
    )


def to_float(val):
    try:
        return float(val)
    except Exception:
        try:
            return float(str(val).replace(",", ""))
        except Exception:
            return 0.0




