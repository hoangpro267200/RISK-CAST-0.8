"""
Unit tests for engine provenance (seed, seed_strategy, iterations, result_hash, etc.).
"""
from __future__ import annotations

import contextlib
import io
import pytest

from app.core.engine.risk_engine_v16 import (
    calculate_enterprise_risk,
    compute_result_hash,
    RiskEngineResult,
    RiskConfig,
)


def _minimal_shipment() -> dict:
    return {
        "distance": 5000,
        "cargo_type": "standard",
        "cargo_value": 100_000,
        "shipment_value": 110_000,
        "packages": 20,
        "transit_time": 21,
        "pol": "VNSGN",
        "pod": "USLAX",
        "carrier_rating": 4.0,
        "container_match": 8.0,
        "packaging_quality": 7.0,
        "weather_risk": 5.0,
        "port_risk": 4.0,
        "priority": 5.0,
        "priority_profile": "standard",
        "route_type": "standard",
        "climate_stress_index": 5.0,
    }


def _run_wrapper(shipment: dict, seed: int = 42, seed_strategy: str = "explicit") -> dict:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return calculate_enterprise_risk(
            shipment,
            seed=seed,
            seed_strategy=seed_strategy,
        )


class TestProvenanceFields:
    """Provenance fields always present in engine output."""

    def test_provenance_always_present(self) -> None:
        shipment = _minimal_shipment()
        out = _run_wrapper(shipment, seed=42)
        assert "seed" in out
        assert "seed_strategy" in out
        assert "iterations" in out
        assert "iterations_used" in out
        assert "engine_version" in out
        assert "result_hash" in out
        assert "computed_at" in out
        assert isinstance(out["seed"], int)
        assert isinstance(out["seed_strategy"], str)
        assert isinstance(out["engine_version"], str)
        assert isinstance(out["result_hash"], str)
        assert isinstance(out["computed_at"], str)
        assert out["iterations"] == out["iterations_used"]
        assert len(out["result_hash"]) == 64  # SHA256 hex

    def test_iterations_used_present(self) -> None:
        shipment = _minimal_shipment()
        out = _run_wrapper(shipment)
        assert "iterations_used" in out
        assert out["iterations_used"] >= RiskConfig.MC_ITERATIONS_MIN


class TestResultHashStable:
    """result_hash reproducible for identical results."""

    def test_same_input_same_seed_same_hash(self) -> None:
        shipment = _minimal_shipment()
        r1 = _run_wrapper(shipment, seed=99)
        r2 = _run_wrapper(shipment, seed=99)
        assert r1["result_hash"] == r2["result_hash"]

    def test_different_seed_different_hash(self) -> None:
        shipment = _minimal_shipment()
        r1 = _run_wrapper(shipment, seed=1)
        r2 = _run_wrapper(shipment, seed=2)
        assert r1["result_hash"] != r2["result_hash"]


class TestComputeResultHash:
    """compute_result_hash behavior."""

    def test_excludes_computed_at(self) -> None:
        data = {"a": 1, "b": 2, "computed_at": "2025-01-01T00:00:00Z"}
        h1 = compute_result_hash(data)
        data["computed_at"] = "2025-12-31T23:59:59Z"
        h2 = compute_result_hash(data)
        assert h1 == h2

    def test_excludes_calculation_timestamp(self) -> None:
        data = {"x": 1, "calculation_timestamp": 1000.0}
        h1 = compute_result_hash(data)
        data["calculation_timestamp"] = 2000.0
        h2 = compute_result_hash(data)
        assert h1 == h2

    def test_canonical_sorted_keys(self) -> None:
        data1 = {"z": 3, "a": 1, "m": 2}
        data2 = {"a": 1, "m": 2, "z": 3}
        assert compute_result_hash(data1) == compute_result_hash(data2)

    def test_deterministic(self) -> None:
        data = {"risk_score": 5.5, "risk_factors": [{"n": "x", "s": 7}]}
        assert compute_result_hash(data) == compute_result_hash(data)


class TestRiskEngineResult:
    """RiskEngineResult dataclass."""

    def test_can_construct(self) -> None:
        from datetime import datetime, timezone

        r = RiskEngineResult(
            risk_score=5.0,
            risk_factors=[],
            seed=42,
            seed_strategy="explicit",
            iterations=10_000,
            engine_version="v16.0",
            result_hash="a" * 64,
            computed_at=datetime.now(timezone.utc),
        )
        assert r.seed == 42
        assert r.result_hash == "a" * 64
