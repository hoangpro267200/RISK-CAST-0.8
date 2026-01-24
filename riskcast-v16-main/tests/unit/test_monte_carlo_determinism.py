"""
Unit tests for Monte Carlo Engine Determinism (RC-D001)

CRITICAL: These tests verify that the risk engine produces deterministic
outputs - same input must always produce same output.
"""
import pytest
import numpy as np

from app.core.engine.monte_carlo_v22 import MonteCarloEngineV22
from app.core.engine.risk_engine_v16 import (
    RiskLayer,
    run_monte_carlo,
    MonteCarloResult,
    RiskConfig,
)


def _make_v16_mc_input():
    """Minimal input_data for run_monte_carlo (v16)."""
    layers = {
        "route_complexity": RiskLayer("Route Complexity", base_score=5.0, volatility=0.2),
        "cargo_sensitivity": RiskLayer("Cargo Sensitivity", base_score=4.0, volatility=0.25),
        "weather_exposure": RiskLayer("Weather Exposure", base_score=6.0, volatility=0.15),
    }
    # Order matches layers.keys()
    weights = np.array([0.4, 0.35, 0.25])
    context = {"volatility_mult": 1.0}
    return {"layers": layers, "weights": weights, "context": context}


# Use engine min iterations (10000) for determinism tests; engine clamps to [MC_MIN, MC_MAX].
ITERATIONS = max(1000, RiskConfig.MC_ITERATIONS_MIN)


class TestMonteCarloDeterminism:
    """Test suite for Monte Carlo determinism (V22 engine)."""

    def test_deterministic_with_explicit_seed(self):
        """
        Test that explicit seed produces identical results.

        Reproduces: RC-D001
        """
        transport = {"transit_time": 14}
        cargo = {"insurance_value": 100000}
        layer_scores = {
            "carrier_performance": 50,
            "port_congestion": 40,
            "weather_climate": 35,
            "documentation_complexity": 40,
            "market_volatility": 40,
            "cargo_sensitivity": 40,
        }

        engine1 = MonteCarloEngineV22(n_runs=1000, random_seed=42)
        result1 = engine1.run_simulation(transport, cargo, layer_scores)

        engine2 = MonteCarloEngineV22(n_runs=1000, random_seed=42)
        result2 = engine2.run_simulation(transport, cargo, layer_scores)

        assert result1["eta_stats"]["mean"] == result2["eta_stats"]["mean"]
        assert result1["loss_stats"]["expected_loss"] == result2["loss_stats"]["expected_loss"]
        assert result1["random_seed"] == result2["random_seed"] == 42

    def test_deterministic_without_seed(self):
        """
        When no seed is provided, engine generates seed from input hash.
        Same input → same seed → same output.
        """
        transport = {"transit_time": 20}
        cargo = {"insurance_value": 50000}
        layer_scores = {
            "carrier_performance": 60,
            "port_congestion": 50,
            "weather_climate": 45,
            "documentation_complexity": 30,
            "market_volatility": 35,
            "cargo_sensitivity": 55,
        }

        engine1 = MonteCarloEngineV22(n_runs=1000)
        result1 = engine1.run_simulation(transport, cargo, layer_scores)

        engine2 = MonteCarloEngineV22(n_runs=1000)
        result2 = engine2.run_simulation(transport, cargo, layer_scores)

        assert result1["eta_stats"]["mean"] == result2["eta_stats"]["mean"]
        assert result1["loss_stats"]["expected_loss"] == result2["loss_stats"]["expected_loss"]
        assert result1["random_seed"] == result2["random_seed"]
        assert "random_seed" in result1

    def test_different_inputs_produce_different_results(self):
        """Different inputs → different results."""
        base_transport = {"transit_time": 14}
        base_cargo = {"insurance_value": 100000}
        base_layers = {
            "carrier_performance": 50,
            "port_congestion": 40,
            "weather_climate": 35,
            "documentation_complexity": 40,
            "market_volatility": 40,
            "cargo_sensitivity": 40,
        }

        engine1 = MonteCarloEngineV22(n_runs=1000)
        result1 = engine1.run_simulation(base_transport, base_cargo, base_layers)

        transport2 = {"transit_time": 30}
        engine2 = MonteCarloEngineV22(n_runs=1000)
        result2 = engine2.run_simulation(transport2, base_cargo, base_layers)

        assert result1["eta_stats"]["mean"] != result2["eta_stats"]["mean"]
        assert result1["random_seed"] != result2["random_seed"]

    def test_seed_generation_consistency(self):
        """Seed generation is consistent for same input."""
        transport = {"transit_time": 14}
        cargo = {"insurance_value": 100000}
        layer_scores = {
            "carrier_performance": 50,
            "port_congestion": 40,
            "weather_climate": 35,
            "documentation_complexity": 40,
            "market_volatility": 40,
            "cargo_sensitivity": 40,
        }

        input_data = {"transport": transport, "cargo": cargo, "layer_scores": layer_scores}

        seed1 = MonteCarloEngineV22._generate_deterministic_seed(input_data)
        seed2 = MonteCarloEngineV22._generate_deterministic_seed(input_data)
        seed3 = MonteCarloEngineV22._generate_deterministic_seed(input_data)

        assert seed1 == seed2 == seed3
        assert isinstance(seed1, int)
        assert 0 <= seed1 < 2**31


class TestV16RunMonteCarloDeterminism:
    """Determinism tests for v16 run_monte_carlo (seeded RNG)."""

    def test_same_input_same_seed_same_result(self):
        """Same input + same seed → identical results."""
        input_data = _make_v16_mc_input()
        seed = 42

        r1 = run_monte_carlo(input_data, ITERATIONS, seed)
        r2 = run_monte_carlo(input_data, ITERATIONS, seed)

        assert isinstance(r1, MonteCarloResult)
        assert r1.seed == r2.seed == seed
        assert r1.iterations == r2.iterations
        np.testing.assert_array_equal(r1.risk_distribution, r2.risk_distribution)
        assert r1.metrics["mean"] == r2.metrics["mean"]
        assert r1.metrics["var_95"] == r2.metrics["var_95"]

    def test_different_seed_different_result(self):
        """Same input + different seed → different results."""
        input_data = _make_v16_mc_input()

        r1 = run_monte_carlo(input_data, ITERATIONS, 42)
        r2 = run_monte_carlo(input_data, ITERATIONS, 99)

        assert r1.seed != r2.seed
        with np.testing.assert_raises(AssertionError):
            np.testing.assert_array_equal(r1.risk_distribution, r2.risk_distribution)
        assert r1.metrics["mean"] != r2.metrics["mean"]

    def test_1000_iterations_reproducible(self):
        """Run with same iterations + seed multiple times → reproducible."""
        input_data = _make_v16_mc_input()
        seed = 123
        n = ITERATIONS

        r1 = run_monte_carlo(input_data, n, seed)
        r2 = run_monte_carlo(input_data, n, seed)
        r3 = run_monte_carlo(input_data, n, seed)

        np.testing.assert_array_equal(r1.risk_distribution, r2.risk_distribution)
        np.testing.assert_array_equal(r2.risk_distribution, r3.risk_distribution)
        assert r1.metrics["mean"] == r2.metrics["mean"] == r3.metrics["mean"]

    def test_run_three_times_identical(self):
        """Acceptance: run 3 times with same seed → identical results."""
        input_data = _make_v16_mc_input()
        seed = 7

        results = [run_monte_carlo(input_data, ITERATIONS, seed) for _ in range(3)]

        for i in range(1, 3):
            np.testing.assert_array_equal(results[0].risk_distribution, results[i].risk_distribution)
            assert results[0].metrics["mean"] == results[i].metrics["mean"]
            assert results[0].metrics["std"] == results[i].metrics["std"]

    def test_run_monte_carlo_with_explicit_rng(self):
        """Passing rng explicitly uses it; result still deterministic when same rng state."""
        from app.core.utils.rng_contract import create_seeded_rng

        input_data = _make_v16_mc_input()
        seed = 100
        rng = create_seeded_rng(seed)

        r1 = run_monte_carlo(input_data, ITERATIONS, seed, rng=None)
        rng2 = create_seeded_rng(seed)
        r2 = run_monte_carlo(input_data, ITERATIONS, seed, rng=rng2)

        np.testing.assert_array_equal(r1.risk_distribution, r2.risk_distribution)
