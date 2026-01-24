"""
RNG (Random Number Generator) contract for the risk engine.

Provides deterministic, reproducible random number generation via
numpy.random.Generator. Never uses np.random.* global state.
"""

from __future__ import annotations

import hashlib
import inspect
from functools import wraps
from typing import TYPE_CHECKING, Callable, TypeVar

import numpy as np

if TYPE_CHECKING:
    from numpy.random import Generator

F = TypeVar("F", bound=Callable[..., object])


def create_seeded_rng(seed: int) -> np.random.Generator:
    """
    Create a numpy.random.Generator with the given seed.

    Uses default_rng(seed) only. Never touches np.random.* global state.
    Same seed always yields the same sequence of numbers.

    Args:
        seed: Integer seed for reproducibility.

    Returns:
        numpy.random.Generator instance.
    """
    return np.random.default_rng(seed)


def derive_seed(base_seed: int, component_name: str) -> int:
    """
    Derive a deterministic sub-seed from a base seed and component name.

    Hash-based: SHA-256 of "base_seed:component_name", then take lower 64 bits
    as unsigned int, folded to 32-bit for numpy compatibility.

    Args:
        base_seed: Base seed value.
        component_name: Component identifier (e.g. "monte_carlo", "shock_engine").

    Returns:
        Derived seed integer.
    """
    payload = f"{base_seed}:{component_name}".encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    # Take first 8 bytes, interpret as big-endian unsigned, fold to 32-bit
    raw = int.from_bytes(digest[:8], byteorder="big")
    return raw % (2**32)


def requires_rng(func: F) -> F:
    """
    Decorator that enforces the wrapped function accepts an 'rng' parameter.

    Used to ensure RNG injection (no global state). Raises TypeError if
    the function has no parameter named 'rng'.

    Returns:
        Wrapped function (same signature).
    """

    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> object:
        return func(*args, **kwargs)

    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    if "rng" not in params:
        raise TypeError(
            f"Function {func.__qualname__!r} must accept an 'rng' parameter. "
            f"Found parameters: {params}"
        )
    return wrapper  # type: ignore[return-value]


class DeterministicRNG:
    """
    Wrapper around numpy.random.Generator for deterministic RNG.

    Holds a Generator instance created via create_seeded_rng. All random
    draws go through .generator; no np.random.* global state is used.
    """

    __slots__ = ("_generator",)

    def __init__(self, seed: int) -> None:
        self._generator: np.random.Generator = create_seeded_rng(seed)

    @property
    def generator(self) -> np.random.Generator:
        """The underlying numpy.random.Generator."""
        return self._generator

    def random(self, size: int | tuple[int, ...] | None = None) -> np.ndarray | float:
        """Uniform [0, 1). Delegates to generator.random."""
        return self._generator.random(size)  # type: ignore[return-value]

    def integers(
        self,
        low: int,
        high: int | None = None,
        size: int | tuple[int, ...] | None = None,
        dtype: type = np.int64,
    ) -> np.ndarray | int:
        """Random integers. Delegates to generator.integers."""
        return self._generator.integers(low, high=high, size=size, dtype=dtype)

    def normal(
        self,
        loc: float = 0.0,
        scale: float = 1.0,
        size: int | tuple[int, ...] | None = None,
    ) -> np.ndarray | float:
        """Normal distribution. Delegates to generator.normal."""
        return self._generator.normal(loc=loc, scale=scale, size=size)

    def uniform(
        self,
        low: float = 0.0,
        high: float = 1.0,
        size: int | tuple[int, ...] | None = None,
    ) -> np.ndarray | float:
        """Uniform [low, high). Delegates to generator.uniform."""
        return self._generator.uniform(low=low, high=high, size=size)
