"""
RISKCAST Converters Module
Data format conversion utilities
"""

from typing import Dict, Any, Optional


def convert_shipment_format(data: Dict[str, Any], from_format: str = "option_a", to_format: str = "engine") -> Dict[str, Any]:
    """
    Convert shipment data between different formats
    
    Args:
        data: Input shipment data
        from_format: Source format ("option_a", "engine", "api")
        to_format: Target format ("option_a", "engine", "api")
    
    Returns:
        Converted shipment data
    """
    if from_format == to_format:
        return data
    
    # Add conversion logic here as needed
    return data


def normalize_risk_score(score: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """
    Normalize risk score to 0-100 range
    
    Args:
        score: Raw risk score
        min_val: Minimum value in original range
        max_val: Maximum value in original range
    
    Returns:
        Normalized score (0-100)
    """
    if max_val == min_val:
        return 50.0
    
    normalized = ((score - min_val) / (max_val - min_val)) * 100
    return max(0.0, min(100.0, normalized))





















