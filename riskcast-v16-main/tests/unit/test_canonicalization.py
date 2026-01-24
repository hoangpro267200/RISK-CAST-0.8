"""
Unit tests for risk input canonicalization and schema validation.
"""
from __future__ import annotations

import pytest

from app.core.risk_input.canonicalization import (
    canonicalize_input,
    compute_input_hash,
    validate_input_schema,
    ValidationResult,
)


class TestCanonicalizeInput:
    """canonicalize_input behavior."""

    def test_sorts_keys_recursively(self) -> None:
        a = {"z": 1, "a": 2, "m": 3}
        b = {"m": 3, "z": 1, "a": 2}
        ca = canonicalize_input(a)
        cb = canonicalize_input(b)
        assert list(ca.keys()) == ["a", "m", "z"]
        assert ca == cb

    def test_different_key_order_same_canonical_form(self) -> None:
        a = {"cargo_value": 100000, "distance": 5000, "cargo_type": "standard"}
        b = {"cargo_type": "standard", "cargo_value": 100000, "distance": 5000}
        assert canonicalize_input(a) == canonicalize_input(b)

    def test_normalize_float_precision(self) -> None:
        out = canonicalize_input({"x": 1.123456789, "y": 2.0})
        assert out["x"] == 1.123457
        assert out["y"] == 2.0

    def test_remove_none_values(self) -> None:
        out = canonicalize_input({"a": 1, "b": None, "c": "x"})
        assert "a" in out and "c" in out
        assert "b" not in out

    def test_normalize_string_whitespace(self) -> None:
        out = canonicalize_input({"s": "  a   b\t\nc  "})
        assert out["s"] == "a b c"

    def test_normalize_dates_iso8601(self) -> None:
        out = canonicalize_input({"etd": "2025-12-01", "shipment_month": "2025-11"})
        assert out["etd"] == "2025-12-01"
        assert out["shipment_month"] == "2025-11-01"

    def test_nested_dict_sorted(self) -> None:
        out = canonicalize_input({"outer": {"z": 1, "a": 2}})
        assert list(out["outer"].keys()) == ["a", "z"]

    def test_list_drops_none(self) -> None:
        out = canonicalize_input({"tags": [1, None, "a", None, 2]})
        assert out["tags"] == [1, "a", 2]

    def test_nested_list_of_dicts(self) -> None:
        out = canonicalize_input({"items": [{"z": 1, "a": 2}, {"b": 3, "c": 4}]})
        assert out["items"][0] == {"a": 2, "z": 1}
        assert out["items"][1] == {"b": 3, "c": 4}

    def test_empty_dict_and_list(self) -> None:
        out = canonicalize_input({"a": {}, "b": [], "c": 1})
        assert out["a"] == {}
        assert out["b"] == []
        assert out["c"] == 1

    def test_date_various_formats(self) -> None:
        from datetime import datetime

        out1 = canonicalize_input({"date": "2025-12-01"})
        out2 = canonicalize_input({"date": datetime(2025, 12, 1)})
        out3 = canonicalize_input({"date": "01/12/2025"})  # DD/MM/YYYY format
        assert out1["date"] == "2025-12-01"
        assert out2["date"] == "2025-12-01"
        assert out3["date"] == "2025-12-01"


class TestComputeInputHash:
    """compute_input_hash behavior."""

    def test_equivalent_inputs_same_hash(self) -> None:
        a = {"cargo_value": 100000, "distance": 5000}
        b = {"distance": 5000, "cargo_value": 100000}
        ca = canonicalize_input(a)
        cb = canonicalize_input(b)
        assert compute_input_hash(ca) == compute_input_hash(cb)

    def test_semantically_identical_same_hash(self) -> None:
        a = canonicalize_input({"x": 1.0000001, "y": 2.0})
        b = canonicalize_input({"x": 1.0000002, "y": 2.0})
        assert compute_input_hash(a) == compute_input_hash(b)

    def test_different_inputs_different_hash(self) -> None:
        ca = canonicalize_input({"cargo_value": 100})
        cb = canonicalize_input({"cargo_value": 200})
        assert compute_input_hash(ca) != compute_input_hash(cb)

    def test_hash_is_sha256_hex(self) -> None:
        h = compute_input_hash(canonicalize_input({"a": 1}))
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_nested_structures_same_hash(self) -> None:
        a = canonicalize_input({"x": {"a": 1, "b": 2}, "y": [3, 4]})
        b = canonicalize_input({"y": [3, 4], "x": {"b": 2, "a": 1}})
        assert compute_input_hash(a) == compute_input_hash(b)


class TestValidateInputSchema:
    """validate_input_schema behavior."""

    def test_valid_input_passes(self) -> None:
        r = validate_input_schema({"cargo_value": 100000}, "v1")
        assert r.valid is True
        assert r.errors == []

    def test_missing_required_fails(self) -> None:
        r = validate_input_schema({"distance": 5000}, "v1")
        assert r.valid is False
        assert any("cargo_value" in e for e in r.errors)

    def test_schema_validation_catches_missing_required(self) -> None:
        r = validate_input_schema({}, "v1")
        assert r.valid is False
        assert "Missing required field: cargo_value" in r.errors

    def test_type_error_reported(self) -> None:
        r = validate_input_schema({"cargo_value": "not-a-number"}, "v1")
        assert r.valid is False
        assert any("cargo_value" in e and "number" in e for e in r.errors)

    def test_unknown_version_skips_validation(self) -> None:
        r = validate_input_schema({"anything": 1}, "nonexistent")
        assert r.valid is True
        assert r.errors == []

    def test_nested_object_validation(self) -> None:
        r = validate_input_schema({"cargo_value": 100000, "buyer": {"name": "Test"}}, "v1")
        assert r.valid is True

    def test_multiple_type_errors(self) -> None:
        r = validate_input_schema(
            {"cargo_value": "not-number", "packages": "not-int", "cargo_type": 123}, "v1"
        )
        assert r.valid is False
        assert len(r.errors) >= 2


class TestValidationResult:
    """ValidationResult dataclass."""

    def test_result_structure(self) -> None:
        r = ValidationResult(valid=False, errors=["e1", "e2"])
        assert r.valid is False
        assert r.errors == ["e1", "e2"]
