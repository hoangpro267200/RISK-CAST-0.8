"""
Seed resolution strategies for the risk engine RNG contract.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Optional


class SeedStrategy(Enum):
    """Strategy for resolving the RNG seed."""

    EXPLICIT = "explicit"
    """Use an explicitly provided seed."""

    HASH_BASED = "hash_based"
    """Use a precomputed hash (e.g. from input) as seed."""

    TIMESTAMP_BASED = "timestamp_based"
    """Use current timestamp-derived value (non-reproducible)."""


def resolve_seed(
    strategy: SeedStrategy,
    input_hash: Optional[int] = None,
    explicit_seed: Optional[int] = None,
) -> int:
    """
    Resolve the final seed integer from strategy and inputs.

    Args:
        strategy: Which strategy to use.
        input_hash: Hash value for HASH_BASED (e.g. hash of case payload).
        explicit_seed: User-provided seed for EXPLICIT.

    Returns:
        Resolved seed as non-negative int (32-bit compatible).

    Raises:
        ValueError: When required input for the chosen strategy is missing.
    """
    if strategy == SeedStrategy.EXPLICIT:
        if explicit_seed is None:
            raise ValueError("explicit_seed is required when strategy is EXPLICIT")
        return int(explicit_seed) % (2**32)

    if strategy == SeedStrategy.HASH_BASED:
        if input_hash is None:
            raise ValueError("input_hash is required when strategy is HASH_BASED")
        return int(input_hash) % (2**32)

    if strategy == SeedStrategy.TIMESTAMP_BASED:
        ns = time.time_ns()
        return ns % (2**32)

    raise ValueError(f"Unknown SeedStrategy: {strategy!r}")
