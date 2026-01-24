"""
Unit tests for RNG contract module (rng_contract + seed_strategy).

Ensures:
- No np.random.* global state usage
- Same seed → same sequence
- 100% coverage for app.core.utils.rng_contract and app.core.utils.seed_strategy
"""

from __future__ import annotations

import pytest
import numpy as np

from app.core.utils.rng_contract import (
    DeterministicRNG,
    create_seeded_rng,
    derive_seed,
    requires_rng,
)
from app.core.utils.seed_strategy import SeedStrategy, resolve_seed


class TestCreateSeededRNG:
    """Tests for create_seeded_rng."""

    def test_returns_generator(self) -> None:
        rng = create_seeded_rng(42)
        assert hasattr(rng, "random")
        assert hasattr(rng, "integers")
        assert hasattr(rng, "normal")

    def test_reproducible_same_seed(self) -> None:
        rng1 = create_seeded_rng(12345)
        rng2 = create_seeded_rng(12345)
        a1 = rng1.random(10)
        a2 = rng2.random(10)
        np.testing.assert_array_equal(a1, a2)

    def test_different_seed_different_sequence(self) -> None:
        rng1 = create_seeded_rng(1)
        rng2 = create_seeded_rng(2)
        a1 = rng1.random(10)
        a2 = rng2.random(10)
        with np.testing.assert_raises(AssertionError):
            np.testing.assert_array_equal(a1, a2)


class TestDeriveSeed:
    """Tests for derive_seed."""

    def test_consistent_output(self) -> None:
        s1 = derive_seed(100, "monte_carlo")
        s2 = derive_seed(100, "monte_carlo")
        assert s1 == s2

    def test_different_component_different_seed(self) -> None:
        s1 = derive_seed(100, "monte_carlo")
        s2 = derive_seed(100, "shock_engine")
        assert s1 != s2

    def test_different_base_same_component_different_seed(self) -> None:
        s1 = derive_seed(100, "foo")
        s2 = derive_seed(101, "foo")
        assert s1 != s2

    def test_output_in_valid_range(self) -> None:
        s = derive_seed(0, "x")
        assert 0 <= s < 2**32
        s = derive_seed(2**40, "y")
        assert 0 <= s < 2**32


class TestRequiresRNGDecorator:
    """Tests for @requires_rng decorator."""

    def test_rejects_function_without_rng_param(self) -> None:
        def bad(x: int) -> int:
            return x + 1

        with pytest.raises(TypeError) as exc_info:
            requires_rng(bad)
        assert "rng" in str(exc_info.value).lower()
        assert "bad" in str(exc_info.value)

    def test_rejects_function_with_no_params(self) -> None:
        def no_params() -> int:
            return 42

        with pytest.raises(TypeError) as exc_info:
            requires_rng(no_params)
        assert "rng" in str(exc_info.value).lower()

    def test_accepts_function_with_rng_param(self) -> None:
        rng = create_seeded_rng(7)

        @requires_rng
        def good(rng: np.random.Generator, x: int) -> float:
            return float(rng.random()) + x

        out = good(rng, 10)
        assert isinstance(out, float)
        assert out >= 10 and out < 11

    def test_accepts_rng_as_kwarg(self) -> None:
        rng = create_seeded_rng(8)

        @requires_rng
        def with_kwarg(a: int, rng: np.random.Generator) -> float:
            return a + rng.random()

        out = with_kwarg(1, rng=rng)
        assert 1 <= out < 2


class TestDeterministicRNG:
    """Tests for DeterministicRNG wrapper."""

    def test_reproducible_same_seed(self) -> None:
        d1 = DeterministicRNG(999)
        d2 = DeterministicRNG(999)
        a1 = [d1.random() for _ in range(5)]
        a2 = [d2.random() for _ in range(5)]
        assert a1 == a2

    def test_generator_property(self) -> None:
        d = DeterministicRNG(1)
        g = d.generator
        assert hasattr(g, "random")
        x = g.random(3)
        assert x.shape == (3,)

    def test_random_size(self) -> None:
        d = DeterministicRNG(2)
        arr = d.random(5)
        assert isinstance(arr, np.ndarray)
        assert arr.shape == (5,)
        assert np.all((arr >= 0) & (arr < 1))

    def test_integers(self) -> None:
        d = DeterministicRNG(3)
        vals = d.integers(0, 10, size=20)
        assert isinstance(vals, np.ndarray)
        assert vals.shape == (20,)
        assert np.all((vals >= 0) & (vals < 10))

    def test_normal(self) -> None:
        d = DeterministicRNG(4)
        vals = d.normal(loc=5.0, scale=2.0, size=100)
        assert vals.shape == (100,)
        assert np.abs(np.mean(vals) - 5.0) < 1.0

    def test_uniform(self) -> None:
        d = DeterministicRNG(5)
        vals = d.uniform(low=1.0, high=3.0, size=50)
        assert np.all((vals >= 1.0) & (vals < 3.0))


class TestSeedStrategy:
    """Tests for SeedStrategy enum and resolve_seed."""

    def test_explicit_uses_explicit_seed(self) -> None:
        seed = resolve_seed(SeedStrategy.EXPLICIT, explicit_seed=12345)
        assert seed == 12345

    def test_explicit_rejects_missing_explicit_seed(self) -> None:
        with pytest.raises(ValueError) as exc_info:
            resolve_seed(SeedStrategy.EXPLICIT, input_hash=1)
        assert "explicit_seed" in str(exc_info.value).lower()

    def test_hash_based_uses_input_hash(self) -> None:
        h = 98765
        seed = resolve_seed(SeedStrategy.HASH_BASED, input_hash=h)
        assert seed == 98765

    def test_hash_based_rejects_missing_input_hash(self) -> None:
        with pytest.raises(ValueError) as exc_info:
            resolve_seed(SeedStrategy.HASH_BASED, explicit_seed=1)
        assert "input_hash" in str(exc_info.value).lower()

    def test_timestamp_based_returns_int(self) -> None:
        seed = resolve_seed(SeedStrategy.TIMESTAMP_BASED)
        assert isinstance(seed, int)
        assert 0 <= seed < 2**32

    def test_explicit_folds_to_32bit(self) -> None:
        seed = resolve_seed(SeedStrategy.EXPLICIT, explicit_seed=2**40 + 100)
        assert 0 <= seed < 2**32

    def test_hash_based_folds_to_32bit(self) -> None:
        seed = resolve_seed(SeedStrategy.HASH_BASED, input_hash=-(2**50))
        assert 0 <= seed < 2**32

    def test_enum_values(self) -> None:
        assert SeedStrategy.EXPLICIT.value == "explicit"
        assert SeedStrategy.HASH_BASED.value == "hash_based"
        assert SeedStrategy.TIMESTAMP_BASED.value == "timestamp_based"

    def test_unknown_strategy_raises(self) -> None:
        from enum import Enum

        class Other(Enum):
            X = "x"

        with pytest.raises(ValueError) as exc_info:
            resolve_seed(Other.X)  # type: ignore[arg-type]
        assert "Unknown" in str(exc_info.value)
