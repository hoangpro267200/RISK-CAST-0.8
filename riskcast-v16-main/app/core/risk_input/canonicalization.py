"""
Canonicalization and hashing for risk inputs.

Ensures semantically identical inputs produce identical hashes
for caching, determinism, and auditability.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_FLOAT_PRECISION = 6
_ISO_DATE_FMT = "%Y-%m-%d"
_SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"


@dataclass
class ValidationResult:
    """Result of schema validation."""

    valid: bool
    errors: List[str] = field(default_factory=list)


def _normalize_whitespace(s: str) -> str:
    if not isinstance(s, str):
        return s
    return " ".join(s.split())


def _normalize_date(value: Any) -> Optional[str]:
    """Convert date-like value to ISO8601 YYYY-MM-DD."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime(_ISO_DATE_FMT)
    s = str(value).strip()
    if not s:
        return None
    # YYYY-MM-DD
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # YYYY-MM
    m = re.match(r"^(\d{4})-(\d{2})(?:-\d{2})?$", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-01"
    # DD/MM/YYYY or MM/DD/YYYY – try common order
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(s[:10], fmt)
            return dt.strftime(_ISO_DATE_FMT)
        except ValueError:
            continue
    return None


def _is_date_like(key: str, value: Any) -> bool:
    if not isinstance(value, (str, datetime)) or value is None:
        return False
    key_lower = key.lower()
    if "date" in key_lower or "etd" in key_lower or "eta" in key_lower or "month" in key_lower:
        return True
    s = str(value).strip()
    if re.match(r"^\d{4}-\d{2}(-\d{2})?", s) or re.match(r"^\d{1,2}/\d{1,2}/\d{4}", s):
        return True
    return False


def canonicalize_input(raw_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Canonicalize raw risk input for stable hashing.

    - Sort all dict keys recursively
    - Normalize numeric precision (floats rounded to 6 decimals)
    - Normalize date-like values to ISO8601 YYYY-MM-DD
    - Remove None values
    - Normalize string whitespace (collapse to single space)
    """
    if not isinstance(raw_input, dict):
        return raw_input

    out: Dict[str, Any] = {}
    for k in sorted(raw_input.keys()):
        v = raw_input[k]
        if v is None:
            continue
        if isinstance(v, dict):
            out[k] = canonicalize_input(v)
        elif isinstance(v, list):
            out[k] = _canonicalize_list(v, k)
        else:
            n = _normalize_leaf(v, k)
            if n is not None:
                out[k] = n
    return out


def _canonicalize_list(lst: List[Any], parent_key: str) -> List[Any]:
    processed: List[Any] = []
    for x in lst:
        if x is None:
            continue
        if isinstance(x, dict):
            y = canonicalize_input(x)
        elif isinstance(x, list):
            y = _canonicalize_list(x, parent_key)
        else:
            y = _normalize_leaf(x, parent_key)
        if y is not None:
            processed.append(y)
    return processed


def _normalize_leaf(value: Any, key: str) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    # Handle numpy scalars
    try:
        import numpy as np
        if isinstance(value, (np.integer, np.floating)):
            if np.issubdtype(type(value), np.integer):
                return int(value)
            return round(float(value), _FLOAT_PRECISION)
        if isinstance(value, np.ndarray):
            return value.tolist()
    except ImportError:
        pass
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(value, _FLOAT_PRECISION)
    if isinstance(value, str):
        s = _normalize_whitespace(value)
        if _is_date_like(key, value):
            d = _normalize_date(value)
            return d if d is not None else s
        return s
    if hasattr(value, "isoformat"):
        return _normalize_date(value) or str(value)
    return value


def compute_input_hash(canonical_input: Dict[str, Any]) -> str:
    """
    Compute SHA256 hash of canonical input.

    Uses JSON serialization with separators=(',', ':') and sorted keys.
    Returns 64-char hex string.
    """
    payload = json.dumps(canonical_input, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_schema(version: str) -> Dict[str, Any]:
    path = _SCHEMAS_DIR / f"{version}.json"
    if not path.is_file():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_input_schema(input_data: Dict[str, Any], schema_version: str) -> ValidationResult:
    """
    Basic schema validation.

    Checks required fields and optional type constraints.
    Returns ValidationResult with valid flag and errors list.
    """
    schema = _load_schema(schema_version)
    errors: List[str] = []

    if not schema:
        return ValidationResult(valid=True, errors=[])  # No schema = skip validation

    required = schema.get("required", [])
    for field in required:
        if field not in input_data:
            errors.append(f"Missing required field: {field}")

    properties = schema.get("properties", {})
    for key, val in input_data.items():
        if key not in properties:
            continue
        prop = properties[key]
        t = prop.get("type")
        if not t:
            continue
        v = val
        if t == "number" and not isinstance(v, (int, float)):
            errors.append(f"Field '{key}' must be number, got {type(v).__name__}")
        elif t == "integer" and not isinstance(v, int):
            errors.append(f"Field '{key}' must be integer, got {type(v).__name__}")
        elif t == "string" and not isinstance(v, str):
            errors.append(f"Field '{key}' must be string, got {type(v).__name__}")
        elif t == "object" and not isinstance(v, dict):
            errors.append(f"Field '{key}' must be object, got {type(v).__name__}")
        elif t == "array" and not isinstance(v, list):
            errors.append(f"Field '{key}' must be array, got {type(v).__name__}")
        elif t == "boolean" and not isinstance(v, bool):
            errors.append(f"Field '{key}' must be boolean, got {type(v).__name__}")

    return ValidationResult(valid=len(errors) == 0, errors=errors)
