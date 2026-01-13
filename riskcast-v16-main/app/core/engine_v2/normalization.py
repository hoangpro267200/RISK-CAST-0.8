"""
RISKCAST Engine v2 - Normalization Utilities
Normalizes various inputs to 0-1 range for consistent scoring
"""

import numpy as np
from typing import Dict, List, Union, Optional


def min_max_normalize(value: float, min_val: float, max_val: float, reverse: bool = False) -> float:
    """
    Min-max normalization to 0-1 range
    
    Args:
        value: Value to normalize
        min_val: Minimum value in range
        max_val: Maximum value in range
        reverse: If True, reverses the scale (high input = low output)
        
    Returns:
        Normalized value between 0 and 1
    """
    if max_val == min_val:
        return 0.5  # Neutral value if no range
    
    normalized = (value - min_val) / (max_val - min_val)
    normalized = max(0.0, min(1.0, normalized))  # Clamp to [0, 1]
    
    if reverse:
        normalized = 1.0 - normalized
    
    return normalized


def z_score_normalize(value: float, mean: float, std: float) -> float:
    """
    Z-score normalization (with sigmoid for 0-1 range)
    
    Args:
        value: Value to normalize
        mean: Mean of distribution
        std: Standard deviation
        
    Returns:
        Normalized value between 0 and 1 (using sigmoid)
    """
    if std == 0:
        return 0.5
    
    z_score = (value - mean) / std
    # Use sigmoid to map to 0-1 range
    normalized = 1.0 / (1.0 + np.exp(-z_score))
    return float(normalized)


def normalize_matrix(matrix: np.ndarray, method: str = "min_max") -> np.ndarray:
    """
    Normalize a matrix (for TOPSIS)
    
    Args:
        matrix: Input matrix (n alternatives × m criteria)
        method: Normalization method ("min_max" or "vector")
        
    Returns:
        Normalized matrix
    """
    if method == "min_max":
        # Min-max normalization per column
        min_vals = np.min(matrix, axis=0, keepdims=True)
        max_vals = np.max(matrix, axis=0, keepdims=True)
        ranges = max_vals - min_vals
        ranges[ranges == 0] = 1  # Avoid division by zero
        normalized = (matrix - min_vals) / ranges
        return normalized
    elif method == "vector":
        # Vector normalization (Euclidean norm)
        norms = np.sqrt(np.sum(matrix ** 2, axis=0, keepdims=True))
        norms[norms == 0] = 1  # Avoid division by zero
        normalized = matrix / norms
        return normalized
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def normalize_dict(data: Dict[str, float], min_vals: Optional[Dict[str, float]] = None,
                   max_vals: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """
    Normalize a dictionary of values
    
    Args:
        data: Dictionary with values to normalize
        min_vals: Minimum values (if None, uses min from data)
        max_vals: Maximum values (if None, uses max from data)
        
    Returns:
        Normalized dictionary
    """
    if not data:
        return {}
    
    if min_vals is None:
        min_vals = {k: min(v for v in data.values() if isinstance(v, (int, float))) for k in data.keys()}
    
    if max_vals is None:
        max_vals = {k: max(v for v in data.values() if isinstance(v, (int, float))) for k in data.keys()}
    
    normalized = {}
    for key, value in data.items():
        if isinstance(value, (int, float)):
            min_val = min_vals.get(key, min(data.values()))
            max_val = max_vals.get(key, max(data.values()))
            normalized[key] = min_max_normalize(value, min_val, max_val)
        else:
            normalized[key] = value
    
    return normalized


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Clamp value between min and max
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def smooth_step(value: float, edge0: float = 0.0, edge1: float = 1.0) -> float:
    """
    Smooth step function (smooth interpolation between edge0 and edge1)
    
    Args:
        value: Input value
        edge0: Lower edge
        edge1: Upper edge
        
    Returns:
        Smoothed value between 0 and 1
    """
    if value <= edge0:
        return 0.0
    if value >= edge1:
        return 1.0
    
    # Smooth interpolation
    t = (value - edge0) / (edge1 - edge0)
    t = clamp(t)
    return t * t * (3.0 - 2.0 * t)





















