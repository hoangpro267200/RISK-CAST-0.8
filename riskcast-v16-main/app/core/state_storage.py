"""
RISKCAST State Storage

Provides persistent storage for shipment state (RISKCAST_STATE).
Supports both file-based (default) and MySQL (optional) backends.

ARCHITECTURE:
- Backend is authoritative source of truth
- localStorage is cache/offline fallback
- Conflict resolution: last-write-wins with updated_at timestamp
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Check if MySQL is enabled
USE_MYSQL = os.getenv("USE_MYSQL", "false").lower() == "true"

# File-based storage configuration
STATE_STORAGE_DIR = Path(__file__).parent.parent.parent / "data" / "state"
STATE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def generate_shipment_id(state: Dict[str, Any]) -> str:
    """
    Generate deterministic shipment ID from state
    
    Uses route + cargo + timestamp to create unique ID
    
    Args:
        state: RISKCAST_STATE dictionary
        
    Returns:
        Shipment ID (hex string)
    """
    # Extract key identifying fields
    shipment = state.get("shipment", {})
    trade_route = shipment.get("trade_route", {})
    
    # Build identifier string
    identifier_parts = [
        trade_route.get("pol", ""),
        trade_route.get("pod", ""),
        trade_route.get("mode", ""),
        shipment.get("cargo_packing", {}).get("cargo_type", ""),
        str(datetime.now().isoformat()[:10])  # Date for uniqueness
    ]
    
    identifier = "|".join(str(p) for p in identifier_parts)
    
    # Generate hash
    shipment_id = hashlib.md5(identifier.encode('utf-8')).hexdigest()[:16]
    
    return shipment_id


def save_state_file_based(shipment_id: str, state: Dict[str, Any]) -> bool:
    """
    Save state to file-based storage
    
    Args:
        shipment_id: Shipment identifier
        state: RISKCAST_STATE dictionary
        
    Returns:
        True if successful
    """
    try:
        # Add metadata
        state_with_meta = {
            "shipment_id": shipment_id,
            "state": state,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "created_at": datetime.utcnow().isoformat() + "Z"  # Will be updated if file exists
        }
        
        # Load existing to preserve created_at
        existing = load_state_file_based(shipment_id)
        if existing and "created_at" in existing:
            state_with_meta["created_at"] = existing["created_at"]
        
        # Save to file
        state_file = STATE_STORAGE_DIR / f"{shipment_id}.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_with_meta, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[State Storage] Saved state for shipment {shipment_id}")
        return True
        
    except Exception as e:
        logger.error(f"[State Storage] Error saving state for {shipment_id}: {e}")
        return False


def load_state_file_based(shipment_id: str) -> Optional[Dict[str, Any]]:
    """
    Load state from file-based storage
    
    Args:
        shipment_id: Shipment identifier
        
    Returns:
        State dictionary with metadata or None if not found
    """
    try:
        state_file = STATE_STORAGE_DIR / f"{shipment_id}.json"
        
        if not state_file.exists():
            return None
        
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
        
    except Exception as e:
        logger.error(f"[State Storage] Error loading state for {shipment_id}: {e}")
        return None


def save_state(shipment_id: str, state: Dict[str, Any]) -> bool:
    """
    Save state to storage (MySQL or file-based)
    
    Args:
        shipment_id: Shipment identifier
        state: RISKCAST_STATE dictionary
        
    Returns:
        True if successful
    """
    if USE_MYSQL:
        try:
            from app.core.state_storage_mysql import save_state_mysql
            return save_state_mysql(shipment_id, state)
        except ImportError:
            logger.warning("[State Storage] MySQL not available, falling back to file-based")
            return save_state_file_based(shipment_id, state)
    else:
        return save_state_file_based(shipment_id, state)


def load_state(shipment_id: str) -> Optional[Dict[str, Any]]:
    """
    Load state from storage (MySQL or file-based)
    
    Args:
        shipment_id: Shipment identifier
        
    Returns:
        State dictionary with metadata or None if not found
    """
    if USE_MYSQL:
        try:
            from app.core.state_storage_mysql import load_state_mysql
            return load_state_mysql(shipment_id)
        except ImportError:
            logger.warning("[State Storage] MySQL not available, falling back to file-based")
            return load_state_file_based(shipment_id)
    else:
        return load_state_file_based(shipment_id)


def list_shipments(limit: int = 100) -> list:
    """
    List recent shipments
    
    Args:
        limit: Maximum number of shipments to return
        
    Returns:
        List of shipment metadata
    """
    shipments = []
    
    try:
        if USE_MYSQL:
            try:
                from app.core.state_storage_mysql import list_shipments_mysql
                return list_shipments_mysql(limit)
            except ImportError:
                pass
        
        # File-based: list all state files
        for state_file in sorted(STATE_STORAGE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    shipments.append({
                        "shipment_id": data.get("shipment_id", state_file.stem),
                        "updated_at": data.get("updated_at"),
                        "created_at": data.get("created_at")
                    })
                    if len(shipments) >= limit:
                        break
            except Exception as e:
                logger.warning(f"[State Storage] Error reading {state_file}: {e}")
        
    except Exception as e:
        logger.error(f"[State Storage] Error listing shipments: {e}")
    
    return shipments

