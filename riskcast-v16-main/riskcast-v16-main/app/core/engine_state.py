"""
ENGINE-FIRST ARCHITECTURE: Shared Backend State for Engine Results

This module provides a shared in-memory state for Engine v2 results.
This is the SINGLE SOURCE OF TRUTH for ResultsOS v4000.

CRITICAL ARCHITECTURE RULES:
- Results page MUST always render data that has passed through the CORE RISK ENGINE
- Storage (localStorage/sessionStorage) is ONLY a fallback for legacy support
- No recomputation, no UI-side logic, pure pass-through
"""

from typing import Dict, Any

# Shared in-memory state for Engine v2 results (authoritative)
# This is set when POST /api/v1/risk/v2/analyze is called
# Results page reads from this via GET /results/data
_LAST_RESULT_V2: Dict[str, Any] = {}


def set_last_result_v2(result: Dict[str, Any]) -> None:
    """
    Store Engine v2 analysis result in shared backend state.
    
    This function is called by /api/v1/risk/v2/analyze endpoint
    after the engine completes execution.
    
    Args:
        result: Complete engine result object (authoritative, immutable)
    
    ARCHITECTURE GUARANTEE:
    - This is the ONLY place where v2 engine results are stored
    - Results page reads from this via GET /results/data
    - No recomputation, no UI-side logic, pure pass-through
    """
    global _LAST_RESULT_V2
    _LAST_RESULT_V2 = result.copy() if result else {}


def get_last_result_v2() -> Dict[str, Any]:
    """
    Get the latest Engine v2 analysis result from shared backend state.
    
    Returns:
        Complete engine result object or empty dict if no analysis has been run
    
    ARCHITECTURE GUARANTEE:
    - Returns exact object produced by v2 engine
    - No transformation, no computation, pure retrieval
    """
    return _LAST_RESULT_V2.copy() if _LAST_RESULT_V2 else {}


