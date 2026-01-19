"""
RISKCAST Engine v2 - Risk Driver Derivation (Engine v3 Refinement)

This module implements strict rules for deriving meaningful risk drivers from engine output.

PHILOSOPHY:
Risk drivers are explanations, not exhaust logs. If the engine cannot confidently explain
why risk exists, it should stay silent (return empty array).

RULES (STRICT):
1. Eliminate zero-impact drivers (impact <= 0)
2. Enforce minimum significance threshold (MIN_DRIVER_IMPACT = 5%)
3. Limit driver count (MAX_DRIVERS = 3)
4. Ensure semantic quality of driver names (human-readable, causal)
5. Distinct from breakdown factors (aggregated causes)
6. Low-risk behavior (empty array preferred for riskScore < 30)
7. Never emit placeholder drivers ("Unknown", "Other", "Misc", empty strings)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RiskDriver:
    """Risk driver with impact and optional description"""
    name: str  # Human-readable, domain meaningful
    impact: float  # 0-100 (% contribution to total risk)
    description: Optional[str] = None  # Optional explanation


# ============================================================================
# CONSTANTS
# ============================================================================

MIN_DRIVER_IMPACT = 5.0  # Minimum % of total risk to be considered a driver
MAX_DRIVERS = 3  # Maximum number of drivers to emit


# ============================================================================
# DRIVER NAME MAPPING (Factor Key → Human-Readable Driver Name)
# ============================================================================

DRIVER_NAME_MAP = {
    # Climate-related
    "climate": "Weather Disruption Risk",
    "weather": "Weather Disruption Risk",
    "storm": "Weather Disruption Risk",
    "wind": "Weather Disruption Risk",
    "rainfall": "Weather Disruption Risk",
    
    # Port/Network-related
    "port": "Port Congestion Risk",
    "congestion": "Port Congestion Risk",
    "network": "Network Disruption Risk",
    "propagation": "Network Disruption Risk",
    "centrality": "Network Disruption Risk",
    
    # Carrier-related
    "carrier": "Carrier Reliability Risk",
    "reliability": "Carrier Reliability Risk",
    "performance": "Carrier Reliability Risk",
    
    # Operational
    "delay": "Operational Delay Risk",
    "transit": "Transit Time Risk",
    "equipment": "Equipment Mismatch Risk",
    "packaging": "Packaging Quality Risk",
    
    # ESG
    "esg": "ESG Compliance Risk",
    "strike": "Labor Disruption Risk",
    
    # Financial
    "financial": "Financial Exposure Risk",
    "cargo_value": "High-Value Cargo Risk",
}


# ============================================================================
# FACTOR AGGREGATION RULES
# ============================================================================

# Map factor keys to aggregated driver categories
FACTOR_AGGREGATION = {
    "climate": ["climate", "weather", "storm", "wind", "rainfall"],
    "port": ["port", "congestion"],
    "network": ["network", "propagation", "centrality"],
    "carrier": ["carrier", "reliability", "performance"],
    "delay": ["delay", "transit"],
    "equipment": ["equipment", "packaging"],
    "esg": ["esg", "strike"],
}


def _get_driver_name(factor_key: str) -> Optional[str]:
    """
    Get human-readable driver name from factor key.
    
    Returns None if factor cannot be confidently mapped to a meaningful name.
    This ensures we never emit placeholder drivers.
    """
    # Direct mapping
    if factor_key in DRIVER_NAME_MAP:
        return DRIVER_NAME_MAP[factor_key]
    
    # Try aggregation groups
    for driver_category, factor_list in FACTOR_AGGREGATION.items():
        if factor_key in factor_list:
            return DRIVER_NAME_MAP.get(driver_category)
    
    # If no mapping found, return None (will be filtered out)
    return None


def _aggregate_factors(factors: Dict[str, float]) -> Dict[str, float]:
    """
    Aggregate related factors into driver categories using dominance-based aggregation.
    
    Risk drivers represent dominant causes, not accumulated noise.
    Aggregation reflects worst-case dominance, not additive magnitude.
    
    Example:
        port_delay (0.7) + berth_utilization (0.5) → Port Congestion Risk (0.7)
        storm_prob (0.8) + wave_height (0.6) → Weather Disruption Risk (0.8)
    
    Args:
        factors: Risk factor breakdown (factor_key → value, 0-1 or 0-100 scale)
    
    Returns:
        Aggregated driver categories (category → normalized value 0-1)
    """
    aggregated = {}
    
    for factor_key, factor_value in factors.items():
        # Normalize factor_value to 0-1 scale for consistent aggregation
        if factor_value > 1.0:
            normalized_factor_value = factor_value / 100.0
        else:
            normalized_factor_value = factor_value
        
        # Find which driver category this factor belongs to
        driver_category = None
        for category, factor_list in FACTOR_AGGREGATION.items():
            if factor_key in factor_list:
                driver_category = category
                break
        
        # If no category found, use factor key directly
        if driver_category is None:
            driver_category = factor_key
        
        # Dominance-based aggregation: use max, not sum
        # This reflects worst-case dominance, not accumulated noise
        if driver_category not in aggregated:
            aggregated[driver_category] = 0.0
        aggregated[driver_category] = max(
            aggregated[driver_category],
            normalized_factor_value
        )
    
    return aggregated


def _calculate_relative_impact(
    driver_value: float,
    total_aggregated_value: float
) -> float:
    """
    Calculate impact as relative contribution percentage.
    
    Driver impact MUST represent relative contribution (%) of each driver
    to the total aggregated risk. This ensures impacts sum to ~100%.
    
    Args:
        driver_value: Aggregated driver value (0-1 scale, normalized)
        total_aggregated_value: Sum of all aggregated driver values
    
    Returns:
        Impact percentage (0-100), rounded to 1 decimal
    """
    if total_aggregated_value <= 0:
        return 0.0
    
    # Calculate relative contribution
    # impact = (driver_value / total_aggregated_value) * 100
    impact = (driver_value / total_aggregated_value) * 100.0
    
    # Clamp to valid range and round to 1 decimal
    impact = min(100.0, max(0.0, impact))
    return round(impact, 1)


def derive_risk_drivers(
    factors: Dict[str, float],
    total_risk_score: float,
    components: Optional[Dict[str, float]] = None
) -> List[RiskDriver]:
    """
    Derive risk drivers from factors following strict rules.
    
    Args:
        factors: Risk factor breakdown (factor_key → value)
        total_risk_score: Total risk score (0-100)
        components: Optional component breakdown for additional context
    
    Returns:
        List of RiskDriver objects (max 3, filtered by impact threshold)
    
    Rules Applied:
        1. Eliminate zero-impact drivers
        2. Enforce MIN_DRIVER_IMPACT threshold (5%)
        3. Limit to MAX_DRIVERS (3)
        4. Ensure semantic quality (no placeholders)
        5. Low-risk behavior (empty array if riskScore < 30)
        6. Never emit placeholders
    """
    # Rule 6: Low-risk behavior - empty array preferred for riskScore < 30
    if total_risk_score < 30:
        return []
    
    # Step 1: Aggregate related factors (dominance-based)
    aggregated_factors = _aggregate_factors(factors)
    
    # Step 1.5: Calculate total aggregated value for relative impact calculation
    total_aggregated_value = sum(aggregated_factors.values())
    
    # If no aggregated factors, return empty
    if total_aggregated_value <= 0:
        return []
    
    # Step 2: Build driver candidates with impact calculation
    driver_candidates = []
    
    for factor_key, driver_value in aggregated_factors.items():
        # Calculate impact as relative contribution to total aggregated risk
        # This ensures impacts sum to ~100%
        impact = _calculate_relative_impact(driver_value, total_aggregated_value)
        
        # Rule 1: Eliminate zero-impact drivers
        if impact <= 0:
            continue
        
        # Rule 2: Enforce minimum significance threshold
        if impact < MIN_DRIVER_IMPACT:
            continue
        
        # Get human-readable driver name
        driver_name = _get_driver_name(factor_key)
        
        # Rule 4 & 7: Ensure semantic quality - skip if no meaningful name
        if driver_name is None or driver_name.strip() == "":
            continue
        
        # Rule 7: Never emit placeholders
        placeholder_names = ["unknown", "other", "misc", "n/a", "none"]
        if driver_name.lower() in placeholder_names:
            continue
        
        # Generate optional description
        # Convert driver_value back to 0-100 scale for description
        driver_value_pct = driver_value * 100.0
        description = _generate_driver_description(factor_key, driver_value_pct, impact)
        
        driver_candidates.append(RiskDriver(
            name=driver_name,
            impact=impact,  # Already rounded to 1 decimal in _calculate_relative_impact
            description=description
        ))
    
    # Step 3: Sort by impact (descending)
    driver_candidates.sort(key=lambda d: d.impact, reverse=True)
    
    # Step 3: Limit to MAX_DRIVERS (Rule 3)
    top_drivers = driver_candidates[:MAX_DRIVERS]
    
    # Final validation: Ensure all drivers meet minimum threshold
    # (This is redundant but ensures safety)
    valid_drivers = [
        d for d in top_drivers
        if d.impact >= MIN_DRIVER_IMPACT
        and d.name
        and d.name.strip() != ""
        and d.name.lower() not in ["unknown", "other", "misc", "n/a", "none"]
    ]
    
    return valid_drivers


def _generate_driver_description(
    factor_key: str,
    factor_value: float,
    impact: float
) -> Optional[str]:
    """
    Generate optional description for driver.
    
    Returns None if no meaningful description can be generated.
    """
    # Normalize factor_value for description
    if factor_value <= 1.0:
        factor_value_pct = factor_value * 100
    else:
        factor_value_pct = factor_value
    
    descriptions = {
        "climate": f"Climate conditions contribute {impact:.1f}% to overall risk, indicating significant weather-related disruption potential.",
        "port": f"Port congestion and operational factors contribute {impact:.1f}% to overall risk.",
        "network": f"Network dependencies and propagation effects contribute {impact:.1f}% to overall risk.",
        "carrier": f"Carrier reliability concerns contribute {impact:.1f}% to overall risk.",
        "delay": f"Operational delay factors contribute {impact:.1f}% to overall risk.",
        "equipment": f"Equipment and packaging factors contribute {impact:.1f}% to overall risk.",
        "esg": f"ESG and labor-related factors contribute {impact:.1f}% to overall risk.",
    }
    
    # Find matching category
    for category in FACTOR_AGGREGATION.keys():
        if factor_key in FACTOR_AGGREGATION[category]:
            return descriptions.get(category)
    
    # Generic description if no specific match
    return f"This factor contributes {impact:.1f}% to the overall risk assessment."


def drivers_to_dict_list(drivers: List[RiskDriver]) -> List[Dict]:
    """
    Convert RiskDriver objects to dictionary list for JSON serialization.
    
    Returns:
        List of dictionaries with 'name', 'impact', and optionally 'description'
    """
    return [
        {
            "name": driver.name,
            "impact": driver.impact,
            **({"description": driver.description} if driver.description else {})
        }
        for driver in drivers
    ]

