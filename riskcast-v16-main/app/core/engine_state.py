"""
ENGINE-FIRST ARCHITECTURE: Shared Backend State for Engine Results

This module provides shared storage for Engine v2 results.
Supports both in-memory (legacy) and MySQL (new) storage.

CRITICAL ARCHITECTURE RULES:
- Results page MUST always render data that has passed through the CORE RISK ENGINE
- MySQL is the authoritative source (if enabled)
- In-memory is fallback for backward compatibility
- No recomputation, no UI-side logic, pure pass-through
"""
import os
from typing import Dict, Any

# Check if MySQL is enabled
USE_MYSQL = os.getenv("USE_MYSQL", "false").lower() == "true"

if USE_MYSQL:
    # Use MySQL-based storage
    try:
        from app.core.engine_state_mysql import set_last_result_v2, get_last_result_v2
        print("[Engine State] Using MySQL storage")
    except ImportError as e:
        print(f"[Engine State] MySQL not available, falling back to in-memory: {e}")
        USE_MYSQL = False

if not USE_MYSQL:
    # Fallback to in-memory storage (legacy)
    _LAST_RESULT_V2: Dict[str, Any] = {}
    
    def set_last_result_v2(result: Dict[str, Any]) -> None:
        """
        Store Engine v2 analysis result in shared backend state (in-memory).
        
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
        Get the latest Engine v2 analysis result from shared backend state (in-memory).
        
        Returns:
            Complete engine result object or empty dict if no analysis has been run
        
        ARCHITECTURE GUARANTEE:
        - Returns exact object produced by v2 engine
        - No transformation, no computation, pure retrieval
        """
        try:
            if _LAST_RESULT_V2 and isinstance(_LAST_RESULT_V2, dict):
                return _LAST_RESULT_V2.copy()
            return {}
        except Exception:
            # If anything goes wrong, return empty dict
            return {}
