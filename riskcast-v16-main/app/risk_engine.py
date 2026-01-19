"""
RISKCAST Enterprise AI - Risk Engine Module
Wrapper for risk calculation functions
"""

from typing import Dict, List, Optional, Any
from app.core.engine.risk_engine_v16 import (
    EnterpriseRiskEngine,
    calculate_enterprise_risk,
    compute_partner_risk
)


def compute_overall_risk(shipment_data: Dict, buyer: Optional[Dict] = None, seller: Optional[Dict] = None) -> float:
    """
    Compute overall risk index (0-100)
    
    Args:
        shipment_data: Shipment parameters
        buyer: Optional buyer information
        seller: Optional seller information
    
    Returns:
        Overall risk index (0-100)
    """
    result = calculate_enterprise_risk(shipment_data, buyer, seller)
    return result.get('overall_risk_index', 50.0)


def compute_route_risk(shipment_data: Dict) -> Dict:
    """
    Compute route-specific risk factors
    
    Args:
        shipment_data: Shipment parameters
    
    Returns:
        Dictionary with route risk details
    """
    result = calculate_enterprise_risk(shipment_data)
    
    return {
        'route_risk_score': result.get('risk_factors', {}).get('route_complexity', 5.0) * 10,
        'weather_risk': result.get('risk_factors', {}).get('weather_exposure', 5.0) * 10,
        'port_risk': result.get('risk_factors', {}).get('port_risk', 5.0) * 10,
        'transport_reliability': result.get('reliability_score', 50.0),
        'recommended_mode': shipment_data.get('transport_mode', 'sea')
    }


def compute_esg_score(shipment_data: Dict) -> Dict:
    """
    Compute ESG (Environmental, Social, Governance) score
    
    Args:
        shipment_data: Shipment parameters
    
    Returns:
        Dictionary with ESG metrics
    """
    result = calculate_enterprise_risk(shipment_data)
    
    # Extract ESG-related metrics
    esg_score = result.get('esg_score', 50.0)
    climate_index = shipment_data.get('climate_index', 5.0)
    
    # Calculate components
    green_score = min(100, max(0, (climate_index / 10) * 100))
    social_score = 50.0  # Default, can be enhanced
    governance_score = 50.0  # Default, can be enhanced
    
    # Weighted ESG score
    weighted_esg = (green_score * 0.4) + (social_score * 0.3) + (governance_score * 0.3)
    
    return {
        'esg_score': round(weighted_esg, 2),
        'green_score': round(green_score, 2),
        'social_score': round(social_score, 2),
        'governance_score': round(governance_score, 2),
        'carbon_footprint_kg': _estimate_carbon_footprint(shipment_data),
        'climate_impact': _get_climate_impact_level(climate_index)
    }


def compute_delay_probability(shipment_data: Dict) -> Dict:
    """
    Compute predictive delay probability and factors
    
    Args:
        shipment_data: Shipment parameters
    
    Returns:
        Dictionary with delay analysis
    """
    result = calculate_enterprise_risk(shipment_data)
    
    # Extract delay-related metrics
    delay_probability = result.get('delay_probability', 0.3) * 100
    expected_delay_days = result.get('expected_delay_days', 2.0)
    
    # Identify main delay factors
    risk_factors = result.get('risk_factors', {})
    main_factors = []
    
    if risk_factors.get('weather_exposure', 0) > 6.0:
        main_factors.append('Weather conditions')
    if risk_factors.get('port_risk', 0) > 6.0:
        main_factors.append('Port congestion')
    if risk_factors.get('route_complexity', 0) > 6.0:
        main_factors.append('Route complexity')
    if risk_factors.get('transport_reliability', 0) < 4.0:
        main_factors.append('Carrier reliability')
    
    return {
        'delay_probability_percent': round(delay_probability, 2),
        'expected_delay_days': round(expected_delay_days, 2),
        'main_factors': main_factors,
        'reliability_score': result.get('reliability_score', 50.0),
        'prevention_measures': _get_prevention_measures(main_factors)
    }


def map_risk_to_insurance(shipment_data: Dict, overall_risk: float) -> Dict:
    """
    Map risk level to insurance recommendation
    
    Args:
        shipment_data: Shipment parameters
        overall_risk: Overall risk index (0-100)
    
    Returns:
        Dictionary with insurance guidance
    """
    cargo_value = shipment_data.get('cargo_value', shipment_data.get('shipment_value', 10000))
    
    # Insurance logic
    if overall_risk > 70:
        recommendation = "Must buy"
        coverage_level = "Comprehensive"
        urgency = "High"
    elif overall_risk >= 40:
        recommendation = "Recommended"
        coverage_level = "Standard"
        urgency = "Medium"
    else:
        recommendation = "Optional"
        coverage_level = "Basic"
        urgency = "Low"
    
    # Calculate expected loss
    loss_percentage = min(0.35, max(0.01, overall_risk / 100 * 0.35))
    expected_loss = cargo_value * loss_percentage
    
    return {
        'recommendation': recommendation,
        'coverage_level': coverage_level,
        'urgency': urgency,
        'expected_loss_usd': round(expected_loss, 2),
        'risk_level': _get_risk_level(overall_risk),
        'reasoning': _get_insurance_reasoning(overall_risk, cargo_value)
    }


def generate_summary(shipment_data: Dict, risk_result: Dict) -> str:
    """
    Generate executive summary text
    
    Args:
        shipment_data: Shipment parameters
        risk_result: Risk calculation results
    
    Returns:
        Executive summary string (120 words)
    """
    overall_risk = risk_result.get('overall_risk_index', 50.0)
    risk_level = _get_risk_level(overall_risk)
    expected_loss = risk_result.get('expected_loss', 0)
    reliability = risk_result.get('reliability_score', 50.0)
    
    summary = f"""
    RISKCAST Enterprise Analysis Summary:
    
    Overall Risk Index: {overall_risk:.1f}/100 ({risk_level} risk level).
    Expected Loss: ${expected_loss:,.2f} USD per shipment.
    Delivery Reliability: {reliability:.1f}% on-time probability.
    
    Primary risk drivers include route complexity, weather exposure, and cargo sensitivity.
    Recommended actions: {_get_top_recommendations(risk_result)}.
    
    This analysis leverages Fuzzy AHP weighting, Monte Carlo simulation, and climate-adjusted risk modeling.
    """
    
    # Limit to ~120 words
    words = summary.split()
    if len(words) > 120:
        summary = ' '.join(words[:120]) + '...'
    
    return summary.strip()


# ==================== HELPER FUNCTIONS ====================

def _estimate_carbon_footprint(shipment_data: Dict) -> float:
    """Estimate carbon footprint in kg CO2e"""
    distance = shipment_data.get('distance', 1000)
    mode = shipment_data.get('transport_mode', 'sea')
    
    # CO2e per km per ton (approximate)
    emission_factors = {
        'air': 0.5,
        'sea': 0.01,
        'road': 0.1,
        'rail': 0.03,
        'multimodal': 0.05
    }
    
    factor = emission_factors.get(mode, 0.05)
    cargo_weight_ton = shipment_data.get('cargo_weight_ton', 1.0)
    
    return round(distance * factor * cargo_weight_ton, 2)


def _get_climate_impact_level(climate_index: float) -> str:
    """Get climate impact level description"""
    if climate_index >= 8:
        return "High climate risk - extreme weather likely"
    elif climate_index >= 6:
        return "Moderate climate risk - weather variability"
    else:
        return "Low climate risk - stable conditions"


def _get_prevention_measures(factors: List[str]) -> List[str]:
    """Get prevention measures based on delay factors"""
    measures_map = {
        'Weather conditions': [
            'Monitor weather forecasts closely',
            'Consider alternative routes',
            'Add buffer time to schedule'
        ],
        'Port congestion': [
            'Book port slots in advance',
            'Consider alternative ports',
            'Negotiate priority handling'
        ],
        'Route complexity': [
            'Simplify routing where possible',
            'Use experienced carriers',
            'Add tracking and monitoring'
        ],
        'Carrier reliability': [
            'Select carriers with proven track record',
            'Implement carrier performance monitoring',
            'Have backup carrier options'
        ]
    }
    
    measures = []
    for factor in factors:
        measures.extend(measures_map.get(factor, []))
    
    return list(set(measures))  # Remove duplicates


def _get_risk_level(risk_score: float) -> str:
    """Convert risk score to level"""
    if risk_score >= 67:
        return "High"
    elif risk_score >= 34:
        return "Medium"
    else:
        return "Low"


def _get_insurance_reasoning(risk_score: float, cargo_value: float) -> str:
    """Generate insurance reasoning"""
    if risk_score > 70:
        return f"High risk level ({risk_score:.1f}/100) with cargo value ${cargo_value:,.0f} requires comprehensive coverage to protect against significant potential losses."
    elif risk_score >= 40:
        return f"Moderate risk level ({risk_score:.1f}/100) suggests standard insurance coverage is prudent given cargo value ${cargo_value:,.0f}."
    else:
        return f"Low risk level ({risk_score:.1f}/100) indicates basic or optional coverage may be sufficient for cargo value ${cargo_value:,.0f}."


def _get_top_recommendations(risk_result: Dict) -> str:
    """Extract top recommendations from risk result"""
    recommendations = risk_result.get('recommendations', [])
    if recommendations:
        return recommendations[0] if isinstance(recommendations, list) else str(recommendations)
    return "Review route optimization and carrier selection"


