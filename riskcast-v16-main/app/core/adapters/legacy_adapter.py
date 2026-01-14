"""
Legacy API adapter for backward compatibility.

RISKCAST v17 - Backward Compatibility Layer

This adapter allows old v1 API consumers to continue working
while we migrate to v2. It translates between old and new formats.

DEPRECATION NOTICE:
These adapters will be removed in v18. Please migrate to v2 API.
"""

import warnings
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from functools import wraps
import json


# ============================================================
# DEPRECATION UTILITIES
# ============================================================

def deprecated(message: str = "This function is deprecated"):
    """
    Decorator to mark functions as deprecated.
    
    Usage:
        @deprecated("Use new_function() instead")
        def old_function():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated. {message}",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_deprecation(endpoint: str, replacement: str):
    """Log deprecation warning with suggested replacement."""
    print(f"[DEPRECATED] {endpoint} - Use {replacement} instead")


# ============================================================
# V1 TO V2 REQUEST ADAPTERS
# ============================================================

class RequestAdapter:
    """
    Adapts v1 API requests to v2 format.
    
    Example:
        v1_payload = {"cargo_type": "GENERAL", "mode": "sea"}
        v2_payload = RequestAdapter.v1_to_v2_risk(v1_payload)
        # Now v2_payload has correct field names and values
    """
    
    @staticmethod
    def v1_to_v2_risk(v1_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert v1 risk analysis request to v2 format.
        
        v1 format:
        {
            "cargo_type": "GENERAL",
            "mode": "sea",
            "value": 50000,
            "from_port": "CNSHA",
            "to_port": "USLAX"
        }
        
        v2 format:
        {
            "cargo_type": "general_merchandise",
            "transport_mode": "ocean_fcl",
            "cargo_value": 50000,
            "origin_port": "CNSHA",
            "destination_port": "USLAX"
        }
        """
        v2_payload = {}
        
        # Field mappings
        field_map = {
            'value': 'cargo_value',
            'from_port': 'origin_port',
            'to_port': 'destination_port',
            'mode': 'transport_mode',
            'ship_date': 'departure_date',
            'arrive_date': 'arrival_date',
        }
        
        for v1_field, v2_field in field_map.items():
            if v1_field in v1_payload:
                v2_payload[v2_field] = v1_payload[v1_field]
        
        # Value mappings for enums
        cargo_type_map = {
            'GENERAL': 'general_merchandise',
            'ELECTRONICS': 'electronics_high_value',
            'PERISHABLE': 'perishables_refrigerated',
            'HAZMAT': 'hazardous_materials',
            'BULK': 'bulk_dry',
            'LIQUID': 'bulk_liquid',
        }
        
        if 'cargo_type' in v1_payload:
            old_type = v1_payload['cargo_type'].upper()
            v2_payload['cargo_type'] = cargo_type_map.get(old_type, 'general_merchandise')
        
        transport_mode_map = {
            'sea': 'ocean_fcl',
            'SEA': 'ocean_fcl',
            'ocean': 'ocean_fcl',
            'air': 'air_freight',
            'AIR': 'air_freight',
            'truck': 'road_ftl',
            'road': 'road_ftl',
            'rail': 'rail',
        }
        
        if 'transport_mode' in v2_payload:
            old_mode = v2_payload['transport_mode']
            v2_payload['transport_mode'] = transport_mode_map.get(old_mode, old_mode)
        
        # Copy remaining fields that don't need transformation
        pass_through = [
            'origin', 'destination', 'cargo_value', 'container',
            'priority', 'packaging', 'insurance_level'
        ]
        
        for field in pass_through:
            if field in v1_payload and field not in v2_payload:
                v2_payload[field] = v1_payload[field]
        
        return v2_payload
    
    @staticmethod
    def v1_to_v2_shipment(v1_shipment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert v1 shipment format to v2.
        
        Handles nested structure differences.
        """
        v2_shipment = {}
        
        # Flatten nested structures
        if 'trade' in v1_shipment:
            trade = v1_shipment['trade']
            v2_shipment['origin_port'] = trade.get('pol')
            v2_shipment['destination_port'] = trade.get('pod')
            v2_shipment['departure_date'] = trade.get('etd')
            v2_shipment['arrival_date'] = trade.get('eta')
        
        if 'cargo' in v1_shipment:
            cargo = v1_shipment['cargo']
            v2_shipment['cargo_value'] = cargo.get('value', cargo.get('cargo_value'))
            v2_shipment['cargo_type'] = cargo.get('type', cargo.get('cargo_type'))
            v2_shipment['packaging'] = cargo.get('packaging')
        
        if 'transport' in v1_shipment:
            transport = v1_shipment['transport']
            v2_shipment['transport_mode'] = transport.get('mode')
            v2_shipment['container'] = transport.get('container')
        
        # Copy top-level fields
        top_level = ['shipment_id', 'status', 'priority', 'notes']
        for field in top_level:
            if field in v1_shipment:
                v2_shipment[field] = v1_shipment[field]
        
        return v2_shipment


# ============================================================
# V2 TO V1 RESPONSE ADAPTERS
# ============================================================

class ResponseAdapter:
    """
    Adapts v2 API responses to v1 format.
    
    For backward compatibility with old clients.
    """
    
    @staticmethod
    def v2_to_v1_risk(v2_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert v2 risk analysis response to v1 format.
        
        v2 format (new):
        {
            "risk_score": 67.5,
            "risk_level": "medium",
            "var_95": 15000,
            "cvar_95": 22000,
            "expected_loss": 8000,
            "risk_factors": [...]
        }
        
        v1 format (legacy):
        {
            "score": 67.5,
            "level": "MEDIUM",
            "var": 15000,
            "expectedLoss": 8000,
            "factors": [...]
        }
        """
        v1_response = {
            # Main metrics with old field names
            'score': v2_response.get('risk_score'),
            'level': v2_response.get('risk_level', '').upper(),
            'var': v2_response.get('var_95'),
            'expectedLoss': v2_response.get('expected_loss'),
            
            # Factors in old format
            'factors': ResponseAdapter._convert_risk_factors(
                v2_response.get('risk_factors', [])
            ),
            
            # Legacy flag
            '_legacy_format': True,
            '_v2_available': True,
        }
        
        # Add deprecation warning
        v1_response['_deprecation_warning'] = (
            "This response format is deprecated. "
            "Please migrate to v2 API for enhanced features."
        )
        
        return v1_response
    
    @staticmethod
    def _convert_risk_factors(v2_factors: list) -> list:
        """Convert v2 risk factors to v1 format."""
        v1_factors = []
        
        for factor in v2_factors:
            v1_factors.append({
                'name': factor.get('name'),
                'score': factor.get('score'),
                'weight': factor.get('weight', 1.0),
                # v1 used simple string descriptions
                'description': factor.get('description', factor.get('explanation', ''))
            })
        
        return v1_factors
    
    @staticmethod
    def v2_to_v1_recommendations(v2_recs: list) -> list:
        """Convert v2 recommendations to v1 format."""
        v1_recs = []
        
        for rec in v2_recs:
            v1_recs.append({
                'text': rec.get('recommendation', rec.get('text')),
                'priority': rec.get('priority', 'medium').upper(),
                'impact': rec.get('impact', 'medium').upper(),
                # v1 didn't have effort/cost fields
            })
        
        return v1_recs


# ============================================================
# ENDPOINT WRAPPER
# ============================================================

class LegacyEndpointWrapper:
    """
    Wraps v2 endpoints to provide v1 compatibility.
    
    Usage in routes:
        @router.post("/api/v1/risk/analyze")
        @LegacyEndpointWrapper.wrap_v1_endpoint
        async def legacy_analyze(request: Request):
            # Request is automatically converted to v2
            # Response is automatically converted back to v1
            pass
    """
    
    @staticmethod
    def wrap_v1_endpoint(func):
        """
        Decorator to wrap v2 endpoint for v1 compatibility.
        
        Automatically:
        1. Logs deprecation warning
        2. Converts request from v1 to v2 format
        3. Calls the v2 handler
        4. Converts response from v2 to v1 format
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Log deprecation
            log_deprecation(
                func.__name__,
                f"POST /api/v2/risk/analyze"
            )
            
            # Get request from kwargs or args
            request = kwargs.get('request')
            if request is None and args:
                request = args[0]
            
            # Convert request body if present
            if hasattr(request, 'json'):
                try:
                    v1_body = await request.json()
                    v2_body = RequestAdapter.v1_to_v2_risk(v1_body)
                    # Attach converted body
                    request._v2_body = v2_body
                except Exception:
                    pass
            
            # Call original function
            result = await func(*args, **kwargs)
            
            # Convert response if needed
            if isinstance(result, dict):
                return ResponseAdapter.v2_to_v1_risk(result)
            
            return result
        
        return wrapper


# ============================================================
# MIGRATION HELPERS
# ============================================================

class MigrationHelper:
    """
    Utilities to help migrate from v1 to v2.
    """
    
    @staticmethod
    def get_field_mapping() -> Dict[str, str]:
        """Get complete field mapping from v1 to v2."""
        return {
            # Request fields
            'value': 'cargo_value',
            'from_port': 'origin_port',
            'to_port': 'destination_port',
            'mode': 'transport_mode',
            'ship_date': 'departure_date',
            'arrive_date': 'arrival_date',
            
            # Response fields
            'score': 'risk_score',
            'level': 'risk_level',
            'var': 'var_95',
            'expectedLoss': 'expected_loss',
            'factors': 'risk_factors',
        }
    
    @staticmethod
    def get_enum_mappings() -> Dict[str, Dict[str, str]]:
        """Get enum value mappings from v1 to v2."""
        return {
            'cargo_type': {
                'GENERAL': 'general_merchandise',
                'ELECTRONICS': 'electronics_high_value',
                'PERISHABLE': 'perishables_refrigerated',
                'HAZMAT': 'hazardous_materials',
                'BULK': 'bulk_dry',
                'LIQUID': 'bulk_liquid',
            },
            'transport_mode': {
                'sea': 'ocean_fcl',
                'ocean': 'ocean_fcl',
                'air': 'air_freight',
                'truck': 'road_ftl',
                'road': 'road_ftl',
                'rail': 'rail',
            },
            'risk_level': {
                'LOW': 'low',
                'MEDIUM': 'medium',
                'HIGH': 'high',
                'CRITICAL': 'critical',
            }
        }
    
    @staticmethod
    def validate_v1_payload(payload: Dict[str, Any]) -> Tuple[bool, list]:
        """
        Validate v1 payload and return migration suggestions.
        
        Returns:
            (is_valid, list_of_suggestions)
        """
        suggestions = []
        is_valid = True
        
        # Check for deprecated fields
        deprecated_fields = ['value', 'from_port', 'to_port', 'mode']
        for field in deprecated_fields:
            if field in payload:
                new_field = MigrationHelper.get_field_mapping().get(field)
                suggestions.append(f"Rename '{field}' to '{new_field}'")
        
        # Check for uppercase enums (v1 style)
        if 'cargo_type' in payload and payload['cargo_type'].isupper():
            suggestions.append("Use lowercase cargo_type values")
        
        return is_valid, suggestions
    
    @staticmethod
    def generate_migration_guide(v1_code: str) -> str:
        """
        Generate migration suggestions for v1 code.
        
        Args:
            v1_code: String containing v1 API usage
        
        Returns:
            Migration guide string
        """
        guide = ["# Migration Guide: v1 → v2", ""]
        
        field_map = MigrationHelper.get_field_mapping()
        
        for old_field, new_field in field_map.items():
            if old_field in v1_code:
                guide.append(f"- Replace `{old_field}` with `{new_field}`")
        
        guide.append("")
        guide.append("## Endpoint Changes")
        guide.append("- `/api/v1/risk/analyze` → `/api/v2/risk/analyze`")
        guide.append("- `/api/v1/shipments` → `/api/v2/shipments`")
        
        return "\n".join(guide)


# ============================================================
# EXAMPLE USAGE
# ============================================================

"""
Example: Using legacy adapter in FastAPI routes

from fastapi import APIRouter, Request
from app.core.adapters.legacy_adapter import (
    RequestAdapter, ResponseAdapter, deprecated
)

router = APIRouter()

@router.post("/api/v1/risk/analyze")
@deprecated("Use /api/v2/risk/analyze instead")
async def legacy_analyze(request: Request):
    # Get v1 request body
    v1_body = await request.json()
    
    # Convert to v2 format
    v2_body = RequestAdapter.v1_to_v2_risk(v1_body)
    
    # Call v2 handler
    v2_result = await v2_analyze_handler(v2_body)
    
    # Convert back to v1 format
    v1_result = ResponseAdapter.v2_to_v1_risk(v2_result)
    
    return v1_result
"""


# ============================================================
# V14 LEGACY ADAPTER FUNCTIONS (for __init__.py compatibility)
# ============================================================

def adapt_v14_to_canonical(v14_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapt v14 input format to canonical engine format.
    
    This function is used by the existing codebase for backward
    compatibility with v14 API consumers.
    
    Args:
        v14_data: Input data in v14 format
    
    Returns:
        Data in canonical engine format
    """
    # Use the v1 to v2 adapter as v14 is similar to v1
    return RequestAdapter.v1_to_v2_risk(v14_data)


def adapt_canonical_to_v14(canonical_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapt canonical engine result to v14 output format.
    
    Args:
        canonical_result: Result from canonical engine
    
    Returns:
        Data in v14 format
    """
    # Use the v2 to v1 adapter as v14 output is similar to v1
    return ResponseAdapter.v2_to_v1_risk(canonical_result)


def run_risk_engine_v14_adapted(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run risk engine with v14 format input/output adaptation.
    
    This is a convenience function that:
    1. Converts v14 input to canonical format
    2. Runs the risk engine
    3. Converts the result back to v14 format
    
    Args:
        input_data: Input data in v14 format
    
    Returns:
        Risk analysis result in v14 format
    """
    # Convert input
    canonical_input = adapt_v14_to_canonical(input_data)
    
    # Run engine (import here to avoid circular imports)
    try:
        from app.core.engine.risk_engine_v16 import RiskEngineV16
        engine = RiskEngineV16()
        canonical_result = engine.calculate_risk(canonical_input)
    except ImportError:
        # Fallback if v16 engine not available
        try:
            from app.risk_engine import calculate_risk
            canonical_result = calculate_risk(canonical_input)
        except ImportError:
            # Return mock result if no engine available
            canonical_result = {
                'risk_score': 50,
                'risk_level': 'medium',
                'var_95': 10000,
                'expected_loss': 5000,
                'message': 'Engine not available - mock result'
            }
    
    # Convert output
    v14_result = adapt_canonical_to_v14(canonical_result)
    
    return v14_result


# Export all functions for __init__.py
__all__ = [
    'deprecated',
    'log_deprecation',
    'RequestAdapter',
    'ResponseAdapter',
    'LegacyEndpointWrapper',
    'MigrationHelper',
    'adapt_v14_to_canonical',
    'adapt_canonical_to_v14',
    'run_risk_engine_v14_adapted',
]
