"""
RISKCAST Legacy Adapter

This module provides adapters for converting between legacy formats (v14, v15)
and the canonical engine interface. This enables backward compatibility while
migrating to the canonical engine.

ARCHITECTURE: ENGINE-FIRST
- Legacy endpoints use adapters to call canonical engine (v16)
- Adapters handle format conversion (input and output)
- Deprecation warnings are logged when legacy formats are used
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from app.core.engine.interface import (
    RiskRequest,
    RiskResult,
    RiskLevel,
    LayerResult,
    ConfidenceResult,
    FinancialMetrics,
    EvidenceItem,
)
from app.core.engine.risk_engine_v16 import calculate_enterprise_risk

logger = logging.getLogger(__name__)


def adapt_v14_to_canonical(v14_payload: Dict[str, Any]) -> RiskRequest:
    """
    Convert v14 format payload to canonical RiskRequest
    
    This adapter handles the mapping from the legacy v14 API format
    to the canonical engine interface format.
    
    Args:
        v14_payload: Legacy v14 format shipment data
        
    Returns:
        Canonical RiskRequest object
    """
    # Log deprecation warning
    logger.warning(
        "[DEPRECATED] Using v14 format. Please migrate to canonical format. "
        "See docs/DEPRECATION.md for migration guide."
    )
    
    # Map transport_mode
    transport_mode_map = {
        'ocean_fcl': 'sea',
        'ocean_lcl': 'sea',
        'air_freight': 'air',
        'rail_freight': 'rail',
        'road_truck': 'road',
        'multimodal': 'multimodal'
    }
    transport_mode = transport_mode_map.get(
        v14_payload.get('transport_mode', 'ocean_fcl'), 'sea'
    )
    
    # Map cargo_type
    cargo_type_map = {
        'electronics': 'fragile',
        'textiles': 'standard',
        'food': 'perishable',
        'chemicals': 'hazardous',
        'machinery': 'high_value',
        'general': 'standard'
    }
    cargo_type = cargo_type_map.get(
        v14_payload.get('cargo_type', 'general'), 'standard'
    )
    
    # Extract container_match from container field
    container_map = {
        '20ft': 7.0,
        '40ft': 8.0,
        '40HC': 8.5,
        '40ft_highcube': 8.5,
        '45ft': 9.0,
        'reefer': 9.5
    }
    container = v14_payload.get('container', '40HC')
    container_match = container_map.get(container, 8.0)
    
    # Extract packaging_quality from packaging field
    packaging_map = {
        'poor': 3.0,
        'fair': 5.0,
        'good': 7.0,
        'excellent': 9.0,
        'palletized': 7.0,
        'loose': 4.0
    }
    packaging = v14_payload.get('packaging', 'good')
    packaging_quality = packaging_map.get(packaging, 7.0)
    
    # Extract priority
    priority_map = {
        'low': 3.0,
        'standard': 5.0,
        'high': 7.0,
        'express': 9.0,
        'speed': 8.0,
        'cost': 4.0
    }
    priority = v14_payload.get('priority', 'standard')
    priority_value = priority_map.get(priority, 5.0)
    
    # Build canonical request
    request = RiskRequest(
        transport_mode=transport_mode,
        cargo_type=cargo_type,
        route=v14_payload.get('route', ''),
        incoterm=v14_payload.get('incoterm', 'FOB'),
        container=container,
        container_match=container_match,
        packaging=packaging,
        packaging_quality=packaging_quality,
        priority=priority,
        priority_profile=v14_payload.get('priority_profile', 'standard'),
        priority_weights=v14_payload.get('priority_weights'),
        transit_time=float(v14_payload.get('transit_time', 0.0)),
        etd=v14_payload.get('etd'),
        eta=v14_payload.get('eta'),
        cargo_value=float(v14_payload.get('cargo_value', 0.0)),
        shipment_value=float(v14_payload.get('shipment_value', 0.0)) or float(v14_payload.get('cargo_value', 0.0)),
        route_type=v14_payload.get('route_type'),
        distance=float(v14_payload.get('distance', 0.0)) if v14_payload.get('distance') else None,
        weather_risk=float(v14_payload.get('weather_risk', 5.0)) if v14_payload.get('weather_risk') is not None else None,
        port_risk=float(v14_payload.get('port_risk', 5.0)) if v14_payload.get('port_risk') is not None else None,
        carrier_rating=float(v14_payload.get('carrier_rating', 4.0)) if v14_payload.get('carrier_rating') is not None else None,
        # Climate variables
        ENSO_index=float(v14_payload.get('ENSO_index', 0.0)) if v14_payload.get('ENSO_index') is not None else None,
        typhoon_frequency=float(v14_payload.get('typhoon_frequency', 0.5)) if v14_payload.get('typhoon_frequency') is not None else None,
        sst_anomaly=float(v14_payload.get('sst_anomaly', 0.0)) if v14_payload.get('sst_anomaly') is not None else None,
        port_climate_stress=float(v14_payload.get('port_climate_stress', 5.0)) if v14_payload.get('port_climate_stress') is not None else None,
        climate_volatility_index=float(v14_payload.get('climate_volatility_index', 5.0)) if v14_payload.get('climate_volatility_index') is not None else None,
        climate_tail_event_probability=float(v14_payload.get('climate_tail_event_probability', 0.05)) if v14_payload.get('climate_tail_event_probability') is not None else None,
        ESG_score=float(v14_payload.get('ESG_score', 50.0)) if v14_payload.get('ESG_score') is not None else None,
        climate_resilience=float(v14_payload.get('climate_resilience', 5.0)) if v14_payload.get('climate_resilience') is not None else None,
        green_packaging=float(v14_payload.get('green_packaging', 5.0)) if v14_payload.get('green_packaging') is not None else None,
        # Parties
        buyer=v14_payload.get('buyer'),
        seller=v14_payload.get('seller'),
        # Engine configuration
        use_fuzzy=v14_payload.get('use_fuzzy', False),
        use_forecast=v14_payload.get('use_forecast', False),
        use_mc=v14_payload.get('use_mc', True),
        use_var=v14_payload.get('use_var', True),
        mc_iterations=v14_payload.get('mc_iterations'),
        # Language
        language=v14_payload.get('language', 'en'),
        # Metadata
        metadata={'source': 'v14_adapter', 'original_payload': v14_payload}
    )
    
    return request


def adapt_canonical_to_v14(canonical_result: RiskResult) -> Dict[str, Any]:
    """
    Convert canonical RiskResult to v14 format
    
    This adapter handles the mapping from the canonical engine result
    back to the legacy v14 API format for backward compatibility.
    
    Args:
        canonical_result: Canonical RiskResult object
        
    Returns:
        Legacy v14 format result dictionary
    """
    # Convert layers to v14 format
    layers = []
    layer_names_map = {
        'Route Complexity': 'Route',
        'Cargo Sensitivity': 'Cargo',
        'Packaging Quality': 'Packaging',
        'Transport Reliability': 'Transport',
        'Weather Exposure': 'Climate',
        'Priority Level': 'Priority',
        'Container Match': 'Container',
        'Port Risk': 'Incoterm'
    }
    
    for layer in canonical_result.layers:
        layer_name = layer_names_map.get(layer.layer_name, layer.layer_name)
        score_0_1 = round(layer.score / 10.0, 2)  # Convert 0-10 to 0-1
        layers.append({
            'name': layer_name,
            'score': score_0_1
        })
    
    # Ensure we have at least 8 layers (v14 expected format)
    expected_layers = ['Transport', 'Cargo', 'Route', 'Incoterm', 'Container', 'Packaging', 'Priority', 'Climate']
    existing_names = {l['name'] for l in layers}
    for layer_name in expected_layers:
        if layer_name not in existing_names:
            layers.append({'name': layer_name, 'score': 0.5})
    
    # Build radar data
    radar_labels = [l['name'] for l in layers]
    radar_values = [l['score'] for l in layers]
    
    # Extract financial metrics
    financial = canonical_result.financial
    mc_samples = financial.distribution[:1000] if financial.distribution else []  # Limit for frontend
    
    # Calculate reliability (inverse of risk)
    reliability = round(1.0 - (canonical_result.overall_score / 10.0), 2) if canonical_result.reliability is None else canonical_result.reliability
    
    # Convert ESG score
    esg = round((canonical_result.esg_score / 100.0) if canonical_result.esg_score else 0.5, 2)
    
    # Build v14 format result
    result = {
        "risk_score": round(canonical_result.overall_score / 10.0, 2),  # Convert 0-10 to 0-1
        "risk_level": canonical_result.risk_level.value,
        "expected_loss": int(round(financial.expected_loss)),
        "reliability": reliability,
        "esg": esg,
        "layers": layers,
        "radar": {
            "labels": radar_labels,
            "values": radar_values
        },
        "mc_samples": mc_samples,
        "var": int(round(financial.var_95)),
        "cvar": int(round(financial.cvar_95)),
        "financial_distribution": {
            "distribution": mc_samples,
            "var_95_usd": financial.var_95,
            "cvar_95_usd": financial.cvar_95
        },
        "climate_hazard_index": float(canonical_result.climate_hazard_index) if canonical_result.climate_hazard_index else 5.0,
        "climate_var_metrics": canonical_result.climate_var_metrics or {},
        "advanced_metrics": {
            "esg_score": canonical_result.esg_score or 50.0,
            "climate_hazard_index": canonical_result.climate_hazard_index or 5.0
        },
        "scenario_analysis": canonical_result.scenario_analysis or {},
        "forecast": canonical_result.forecast or {},
        "priority_profile": canonical_result.metadata.get('priority_profile', 'standard'),
        "priority_weights": canonical_result.metadata.get('priority_weights', {'speed': 40, 'cost': 40, 'risk': 20}),
        "buyer_seller_analysis": canonical_result.buyer_seller_analysis or {},
    }
    
    return result


def run_risk_engine_v14_adapted(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapter function that replaces the original run_risk_engine_v14
    
    This function:
    1. Converts v14 format to canonical
    2. Calls the canonical engine (v16)
    3. Converts result back to v14 format
    4. Logs deprecation warning
    
    Args:
        payload: Legacy v14 format shipment data
        
    Returns:
        Legacy v14 format result dictionary
    """
    try:
        # Step 1: Convert v14 format to canonical
        canonical_request = adapt_v14_to_canonical(payload)
        
        # Step 2: Call canonical engine (v16)
        # Note: calculate_enterprise_risk expects a dict, not RiskRequest
        # So we convert the RiskRequest back to dict for now
        # TODO: Update engine to accept RiskRequest directly
        engine_input = {
            'transport_mode': canonical_request.transport_mode,
            'cargo_type': canonical_request.cargo_type,
            'route': canonical_request.route,
            'incoterm': canonical_request.incoterm,
            'container_match': canonical_request.container_match,
            'packaging_quality': canonical_request.packaging_quality,
            'priority': canonical_request.priority,
            'transit_time': canonical_request.transit_time,
            'cargo_value': canonical_request.cargo_value,
            'shipment_value': canonical_request.shipment_value,
            'route_type': canonical_request.route_type,
            'distance': canonical_request.distance,
            'weather_risk': canonical_request.weather_risk,
            'port_risk': canonical_request.port_risk,
            'carrier_rating': canonical_request.carrier_rating,
            'ENSO_index': canonical_request.ENSO_index,
            'typhoon_frequency': canonical_request.typhoon_frequency,
            'sst_anomaly': canonical_request.sst_anomaly,
            'port_climate_stress': canonical_request.port_climate_stress,
            'climate_volatility_index': canonical_request.climate_volatility_index,
            'climate_tail_event_probability': canonical_request.climate_tail_event_probability,
            'ESG_score': canonical_request.ESG_score,
            'climate_resilience': canonical_request.climate_resilience,
            'green_packaging': canonical_request.green_packaging,
        }
        
        engine_result = calculate_enterprise_risk(
            engine_input,
            buyer=canonical_request.buyer,
            seller=canonical_request.seller
        )
        
        # Step 3: Convert engine result to canonical format
        # Note: The engine returns a dict, not RiskResult
        # For now, we'll use the existing transformation logic
        # TODO: Update engine to return RiskResult
        
        # Step 4: Use existing transformation (from risk_service.py)
        # We'll call the existing _transform_engine_output function
        from app.core.services.risk_service import _transform_engine_output
        v14_result = _transform_engine_output(engine_result, original_payload=payload)
        
        return v14_result
        
    except Exception as e:
        logger.error(f"[RISKCAST v14 Adapter] Error: {e}", exc_info=True)
        # Return default structure on error (same as original)
        return {
            "risk_score": 0.5,
            "risk_level": "MODERATE",
            "expected_loss": 0,
            "reliability": 0.5,
            "esg": 0.5,
            "layers": [
                {"name": "Transport", "score": 0.5},
                {"name": "Cargo", "score": 0.5},
                {"name": "Route", "score": 0.5},
                {"name": "Incoterm", "score": 0.5},
                {"name": "Container", "score": 0.5},
                {"name": "Packaging", "score": 0.5},
                {"name": "Priority", "score": 0.5},
                {"name": "Climate", "score": 0.5}
            ],
            "radar": {
                "labels": ["Transport", "Cargo", "Route", "Incoterm", "Container", "Packaging", "Priority", "Climate"],
                "values": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
            },
            "mc_samples": [],
            "var": 0,
            "cvar": 0,
            "scenario_analysis": {},
            "forecast": {},
            "climate_hazard_index": 5.0,
            "climate_var_metrics": {},
            "advanced_metrics": {},
            "priority_profile": "standard",
            "priority_weights": {"speed": 40, "cost": 40, "risk": 20},
            "buyer_seller_analysis": {},
            "financial_distribution": {}
        }

