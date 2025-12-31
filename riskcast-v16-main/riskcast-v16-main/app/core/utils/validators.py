"""
RISKCAST Enterprise AI - Utility Functions
Helper functions for data processing and formatting
"""

from typing import Dict, List, Any, Optional
import re


def sanitize_input(data: Dict) -> Dict:
    """
    Sanitize and validate input data
    
    Args:
        data: Raw input dictionary
    
    Returns:
        Sanitized dictionary
    """
    sanitized = {}
    
    # Numeric fields
    numeric_fields = [
        'distance', 'cargo_value', 'shipment_value', 'packaging_quality',
        'weather_risk', 'priority', 'container_match', 'port_risk',
        'carrier_rating', 'climate_index', 'cargo_weight_ton'
    ]
    
    for field in numeric_fields:
        if field in data:
            try:
                value = float(data[field])
                # Clamp values to reasonable ranges
                if 'quality' in field or 'rating' in field:
                    value = max(1.0, min(10.0, value))
                elif 'risk' in field or 'priority' in field:
                    value = max(1.0, min(10.0, value))
                elif 'index' in field:
                    value = max(1.0, min(10.0, value))
                sanitized[field] = value
            except (ValueError, TypeError):
                sanitized[field] = 5.0  # Default
    
    # String fields
    string_fields = [
        'cargo_type', 'transport_mode', 'route_type', 'incoterm',
        'origin_country', 'destination_country'
    ]
    
    for field in string_fields:
        if field in data:
            sanitized[field] = str(data[field]).strip()
    
    # Set defaults for missing required fields
    defaults = {
        'distance': 1000.0,
        'cargo_value': 10000.0,
        'packaging_quality': 5.0,
        'weather_risk': 5.0,
        'priority': 5.0,
        'container_match': 5.0,
        'port_risk': 5.0,
        'transport_mode': 'sea',
        'cargo_type': 'standard',
        'route_type': 'standard',
        'climate_index': 5.0
    }
    
    for key, default_value in defaults.items():
        if key not in sanitized:
            sanitized[key] = default_value
    
    return sanitized


def format_risk_level(risk_score: float) -> str:
    """
    Format risk score to level string
    
    Args:
        risk_score: Risk score (0-100)
    
    Returns:
        Risk level string
    """
    if risk_score >= 67:
        return "High"
    elif risk_score >= 34:
        return "Medium"
    else:
        return "Low"


def format_currency(amount: float) -> str:
    """
    Format currency amount
    
    Args:
        amount: Amount in USD
    
    Returns:
        Formatted string
    """
    if amount >= 1000000:
        return f"${amount/1000000:.2f}M"
    elif amount >= 1000:
        return f"${amount/1000:.2f}K"
    else:
        return f"${amount:,.2f}"


def extract_key_points(text: str, max_points: int = 5) -> List[str]:
    """
    Extract key points from text
    
    Args:
        text: Input text
        max_points: Maximum number of points to extract
    
    Returns:
        List of key points
    """
    # Split by common separators
    points = re.split(r'[•\-\n]', text)
    
    # Clean and filter
    cleaned = []
    for point in points:
        point = point.strip()
        if len(point) > 10:  # Minimum length
            cleaned.append(point)
    
    return cleaned[:max_points]


def build_ai_prompt(context: str, task: str, data: Dict) -> str:
    """
    Build AI prompt from context and data
    
    Args:
        context: Context description
        task: Specific task
        data: Relevant data
    
    Returns:
        Formatted prompt string
    """
    prompt = f"""
You are RISKCAST Enterprise AI — a Logistics Risk Intelligence System.

Context: {context}

Task: {task}

Shipment Data:
- Route: {data.get('route', 'N/A')}
- Cargo Type: {data.get('cargo_type', 'N/A')}
- Transport Mode: {data.get('transport_mode', 'N/A')}
- Value: ${data.get('cargo_value', 0):,.2f}

Your tasks:
1. Identify main risk drivers
2. Quantify risk impact
3. Provide actionable recommendations
4. Explain reasoning in structured format
5. Write in expert tone (KPMG / Deloitte / BCG style)

Please provide your analysis:
"""
    return prompt.strip()


def validate_shipment_data(data: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate shipment data
    
    Args:
        data: Shipment data dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['cargo_value', 'transport_mode']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate numeric fields
    numeric_fields = ['cargo_value', 'distance']
    for field in numeric_fields:
        if field in data:
            try:
                value = float(data[field])
                if value <= 0:
                    return False, f"{field} must be positive"
            except (ValueError, TypeError):
                return False, f"{field} must be a number"
    
    return True, None


def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge multiple dictionaries
    
    Args:
        *dicts: Variable number of dictionaries
    
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def safe_get(data: Dict, key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary
    
    Args:
        data: Dictionary
        key: Key to retrieve
        default: Default value if key not found
    
    Returns:
        Value or default
    """
    return data.get(key, default)


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change
    
    Args:
        old_value: Old value
        new_value: New value
    
    Returns:
        Percentage change
    """
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100

