"""
RISKCAST Adapters

This module provides adapters for converting between legacy formats and
the canonical engine interface.

ARCHITECTURE: ENGINE-FIRST
- All legacy endpoints use adapters to call the canonical engine
- Adapters handle format conversion (input and output)
- Deprecation warnings are logged when legacy formats are used
"""
from app.core.adapters.legacy_adapter import (
    adapt_v14_to_canonical,
    adapt_canonical_to_v14,
    run_risk_engine_v14_adapted,
)

__all__ = [
    "adapt_v14_to_canonical",
    "adapt_canonical_to_v14",
    "run_risk_engine_v14_adapted",
]

