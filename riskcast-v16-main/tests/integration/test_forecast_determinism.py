"""
Integration tests for forecast determinism (v16 engine).

Verifies that the full forecast pipeline produces byte-identical outputs
for the same input and seed. No unseeded random in forecast path.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import pytest

from app.core.engine.risk_engine_v16 import (
    EnterpriseRiskEngineV16,
    EnterpriseRiskEngine,
    RiskConfig,
)


def _minimal_shipment() -> dict:
    """Minimal shipment input for V16 (parseable by _parse_enhanced_data)."""
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
        "carrier_ontime_percent": 92.0,
        "container_match": 8.0,
        "packaging_quality": 7.0,
        "weather_risk": 5.0,
        "port_risk": 4.0,
        "priority": 5.0,
        "priority_profile": "standard",
        "route_type": "standard",
        "climate_stress_index": 5.0,
    }


def _run_v16_calculate_risk(shipment: dict, seed: int, suppress_print: bool = True) -> dict:
    """Run V16 calculate_risk with fixed seed. Optionally suppress engine prints."""
    it = max(RiskConfig.MC_ITERATIONS_MIN, 12_000)
    engine = EnterpriseRiskEngineV16(mc_iterations=it)
    if suppress_print:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = engine.calculate_risk(shipment, seed=seed)
    else:
        result = engine.calculate_risk(shipment, seed=seed)
    return result


def _run_v14_calculate_risk(shipment: dict, seed: int, suppress_print: bool = True) -> dict:
    """Run v14-style EnterpriseRiskEngine.calculate_risk with fixed seed."""
    engine = EnterpriseRiskEngine()
    if suppress_print:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            metrics = engine.calculate_risk(shipment, seed=seed)
    else:
        metrics = engine.calculate_risk(shipment, seed=seed)
    # RiskMetrics-like; we care about .forecast
    return {
        "forecast": metrics.forecast,
        "delay_probability": metrics.delay_probability,
        "delay_days_estimate": metrics.delay_days_estimate,
    }


class TestForecastDeterminism:
    """Full forecast pipeline determinism with fixed seed."""

    def test_v16_forecast_byte_identical_same_seed(self):
        """V16: same input + same seed → byte-identical forecast (and related outputs)."""
        shipment = _minimal_shipment()
        seed = 42

        r1 = _run_v16_calculate_risk(shipment, seed)
        r2 = _run_v16_calculate_risk(shipment, seed)

        assert "forecast" in r1 and "forecast" in r2
        f1, f2 = r1["forecast"], r2["forecast"]

        assert f1["days"] == f2["days"]
        assert f1["values"] == f2["values"]
        assert f1["confidence_upper"] == f2["confidence_upper"]
        assert f1["confidence_lower"] == f2["confidence_lower"]
        assert f1["mean_reversion_target"] == f2["mean_reversion_target"]
        assert f1["current_volatility"] == f2["current_volatility"]

        b1 = json.dumps(f1, sort_keys=True).encode()
        b2 = json.dumps(f2, sort_keys=True).encode()
        assert b1 == b2, "Forecast output must be byte-identical"

        assert r1["delay_probability"] == r2["delay_probability"]
        assert r1["delay_days_estimate"] == r2["delay_days_estimate"]
        assert r1["overall_risk"] == r2["overall_risk"]

    def test_v16_forecast_three_runs_identical(self):
        """V16: run 3 times with same seed → identical forecast."""
        shipment = _minimal_shipment()
        seed = 123

        results = [_run_v16_calculate_risk(shipment, seed) for _ in range(3)]

        for i in range(1, 3):
            assert results[0]["forecast"]["values"] == results[i]["forecast"]["values"]
            assert results[0]["forecast"]["confidence_upper"] == results[i]["forecast"]["confidence_upper"]
            assert results[0]["forecast"]["confidence_lower"] == results[i]["forecast"]["confidence_lower"]
        b0 = json.dumps(results[0]["forecast"], sort_keys=True).encode()
        for i in range(1, 3):
            assert json.dumps(results[i]["forecast"], sort_keys=True).encode() == b0

    def test_v16_different_seed_different_forecast(self):
        """V16: same input + different seed → different forecast."""
        shipment = _minimal_shipment()

        r1 = _run_v16_calculate_risk(shipment, 1)
        r2 = _run_v16_calculate_risk(shipment, 2)

        assert r1["forecast"]["values"] != r2["forecast"]["values"]
        assert json.dumps(r1["forecast"], sort_keys=True) != json.dumps(r2["forecast"], sort_keys=True)

    def test_v14_forecast_byte_identical_same_seed(self):
        """V14-style engine: same input + same seed → byte-identical forecast."""
        shipment = _minimal_shipment()
        seed = 42

        r1 = _run_v14_calculate_risk(shipment, seed)
        r2 = _run_v14_calculate_risk(shipment, seed)

        assert r1["forecast"]["values"] == r2["forecast"]["values"]
        assert json.dumps(r1["forecast"], sort_keys=True) == json.dumps(r2["forecast"], sort_keys=True)
        assert r1["delay_probability"] == r2["delay_probability"]
