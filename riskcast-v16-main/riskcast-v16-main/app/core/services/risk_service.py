from typing import Dict, Any, Optional

# Import risk engine using absolute import
from app.core.engine.risk_engine_v16 import calculate_enterprise_risk

def _map_shipment_to_engine(shipment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Option A Shipment schema to engine input format
    
    Option A fields -> Engine fields:
    - transport_mode -> transport_mode (map values)
    - cargo_type -> cargo_type (map values)
    - route -> route_type + distance (derive from route)
    - container -> container_match (map to 1-10 scale)
    - packaging -> packaging_quality (map to 1-10 scale)
    - priority -> priority (map to 1-10 scale)
    - transit_time -> (used for calculation)
    - cargo_value -> cargo_value + shipment_value
    """
    engine_data = {}
    
    # Direct mappings with value transformations
    transport_mode_map = {
        'ocean_fcl': 'sea', 'ocean_lcl': 'sea',
        'air_freight': 'air',
        'rail_freight': 'rail',
        'road_truck': 'road',
        'multimodal': 'multimodal'
    }
    engine_data['transport_mode'] = transport_mode_map.get(
        shipment.get('transport_mode', 'ocean_fcl'), 'sea'
    )
    
    # Cargo type mapping (keep similar values)
    cargo_type_map = {
        'electronics': 'fragile',
        'textiles': 'standard',
        'food': 'perishable',
        'chemicals': 'hazardous',
        'machinery': 'high_value'
    }
    engine_data['cargo_type'] = cargo_type_map.get(
        shipment.get('cargo_type', 'electronics'), 'standard'
    )
    
    # Route mapping (derive route_type and distance)
    route_map = {
        'vn_us': {'route_type': 'complex', 'distance': 12000},
        'vn_cn': {'route_type': 'standard', 'distance': 2000},
        'vn_sg': {'route_type': 'direct', 'distance': 1500},
    }
    route_info = route_map.get(shipment.get('route', 'vn_us'), {'route_type': 'standard', 'distance': 5000})
    engine_data['route_type'] = route_info['route_type']
    engine_data['distance'] = route_info['distance']
    
    # Container mapping (container -> container_match, 1-10 scale)
    container_map = {
        '20ft': 7.0, '40ft': 8.0, '40ft_highcube': 8.5,
        '45ft': 9.0, 'reefer': 9.5
    }
    engine_data['container_match'] = container_map.get(
        shipment.get('container', '40ft_highcube'), 8.0
    )
    
    # Packaging mapping (packaging -> packaging_quality, 1-10 scale)
    packaging_map = {
        'poor': 3.0, 'fair': 5.0, 'good': 7.0,
        'excellent': 9.0
    }
    engine_data['packaging_quality'] = packaging_map.get(
        shipment.get('packaging', 'good'), 7.0
    )
    
    # Priority mapping (priority -> priority, 1-10 scale)
    priority_map = {
        'low': 3.0, 'standard': 5.0, 'high': 7.0,
        'express': 9.0
    }
    engine_data['priority'] = priority_map.get(
        shipment.get('priority', 'standard'), 5.0
    )
    
    # Direct value mappings
    engine_data['cargo_value'] = float(shipment.get('cargo_value', 50000))
    engine_data['shipment_value'] = engine_data['cargo_value']  # Use cargo_value as shipment_value
    engine_data['transit_time'] = float(shipment.get('transit_time', 20))
    
    # Default values for missing engine fields
    engine_data['weather_risk'] = 5.0  # Default moderate weather risk
    engine_data['port_risk'] = 5.0  # Default moderate port risk
    engine_data['carrier_rating'] = 4.0  # Default good carrier rating
    engine_data['climate_index'] = 5.0  # Default neutral climate index
    
    # Extract climate variables from Option A shipment data
    # These will be used by the engine for climate adjustments
    climate_fields = [
        'ENSO_index', 'typhoon_frequency', 'sst_anomaly', 
        'port_climate_stress', 'climate_volatility_index',
        'climate_tail_event_probability', 'ESG_score',
        'climate_resilience', 'green_packaging'
    ]
    for field in climate_fields:
        if field in shipment:
            engine_data[field] = shipment[field]
        elif field == 'ENSO_index':
            engine_data[field] = 0.0
        elif field == 'typhoon_frequency':
            engine_data[field] = 0.5
        elif field == 'sst_anomaly':
            engine_data[field] = 0.0
        elif field == 'port_climate_stress':
            engine_data[field] = 5.0
        elif field == 'climate_volatility_index':
            engine_data[field] = 5.0
        elif field == 'climate_tail_event_probability':
            engine_data[field] = 0.05
        elif field == 'ESG_score':
            engine_data[field] = 50.0
        elif field == 'climate_resilience':
            engine_data[field] = 5.0
        elif field == 'green_packaging':
            engine_data[field] = 5.0
    
    return engine_data


def _transform_engine_output(engine_result: Dict[str, Any], original_payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Transform engine output to Option A JSON format with ALL required fields for charts
    
    Engine output -> Frontend format:
    {
        "risk_score": 0.0-1.0,
        "risk_level": string,
        "expected_loss": int (USD),
        "reliability": 0.0-1.0,
        "esg": 0.0-1.0,
        "layers": [{name, score}],
        "radar": {labels: [], values: []},
        "mc_samples": [numbers],
        "var": int (USD),
        "cvar": int (USD),
        "scenario_analysis": {...},
        "forecast": {...},
        "climate_hazard_index": float,
        "climate_var_metrics": {...}
    }
    """
    def _payload_float(key: str, default: Optional[float] = None) -> Optional[float]:
        if not original_payload:
            return default
        value = original_payload.get(key, default)
        if value in (None, ""):
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    # Extract layers from risk_factors
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
    
    risk_factors = engine_result.get('risk_factors', [])
    transport_reliability_score = None
    
    for factor in risk_factors:
        layer_name = layer_names_map.get(factor['name'], factor['name'])
        score_0_1 = round(factor['score'] / 10.0, 2)  # Convert 0-10 to 0-1
        
        layers.append({
            'name': layer_name,
            'score': score_0_1
        })
        
        # Extract transport reliability for reliability metric
        if factor['name'] == 'Transport Reliability':
            transport_reliability_score = score_0_1
    
    # Ensure we have 8 layers (add missing ones with default values)
    expected_layers = ['Transport', 'Cargo', 'Route', 'Incoterm', 'Container', 'Packaging', 'Priority', 'Climate']
    existing_names = {l['name'] for l in layers}
    for layer_name in expected_layers:
        if layer_name not in existing_names:
            layers.append({'name': layer_name, 'score': 0.5})
    
    # Build radar data - try to use engine's radar_data first, fallback to layers
    radar_data = engine_result.get('radar_data', {})
    if radar_data and 'labels' in radar_data and 'scores' in radar_data:
        # Use engine's radar_data, convert scores (0-10) to values (0-1)
        radar_labels = radar_data.get('labels', [])
        radar_scores = radar_data.get('scores', [])
        radar_values = [round(score / 10.0, 2) if isinstance(score, (int, float)) else 0.5 for score in radar_scores]
    else:
        # Fallback: build from layers
        radar_labels = [l['name'] for l in layers]
        radar_values = [l['score'] for l in layers]
    
    # Get MC samples from financial distribution (USD losses)
    fin_dist = engine_result.get('financial_distribution', {})
    mc_samples = fin_dist.get('distribution', [])
    
    # Ensure mc_samples is a list and limit size for frontend
    if not isinstance(mc_samples, list):
        mc_samples = []
    if len(mc_samples) > 1000:
        mc_samples = mc_samples[:1000]
    
    # Extract VaR/CVaR from financial distribution (USD)
    var_95_usd = fin_dist.get('var_95_usd', 0)
    cvar_95_usd = fin_dist.get('cvar_95_usd', 0)
    
    # Transform risk_score (0-10) to 0-1
    overall_risk = engine_result.get('overall_risk', 5.0)
    risk_score = round(overall_risk / 10.0, 2)
    
    # Calculate reliability score (0-1 scale)
    # Use transport reliability if available, otherwise derive from overall risk (inverse)
    if transport_reliability_score is not None:
        reliability = round(1.0 - transport_reliability_score, 2)  # Inverse: low risk = high reliability
    else:
        reliability = round(1.0 - risk_score, 2)  # Fallback: inverse of overall risk
    
    # Extract ESG score from advanced_metrics or calculate from climate vars
    advanced_metrics = engine_result.get('advanced_metrics', {})
    climate_var_metrics = advanced_metrics.get('climate_var_metrics', {})
    
    # Extract ESG score from original payload or use default
    # ESG is typically 0-100, convert to 0-1
    esg_raw = 50.0  # Default
    if original_payload and 'ESG_score' in original_payload:
        esg_raw = float(original_payload.get('ESG_score', 50.0))
    elif 'ESG_score' in engine_result:
        esg_raw = float(engine_result.get('ESG_score', 50.0))
    esg = round(esg_raw / 100.0, 2)  # Convert 0-100 to 0-1
    green_pack_raw = original_payload.get('green_packaging', 50.0) if original_payload else 50.0
    climate_resilience_raw = original_payload.get('climate_resilience', 5.0) if original_payload else 5.0
    
    # Ensure advanced metrics include ESG & sustainability inputs for frontend use
    if 'esg_score' not in advanced_metrics:
        advanced_metrics['esg_score'] = esg_raw
    if 'green_packaging' not in advanced_metrics:
        advanced_metrics['green_packaging'] = green_pack_raw
    if 'climate_resilience' not in advanced_metrics:
        advanced_metrics['climate_resilience'] = climate_resilience_raw
    
    # Extract climate metrics
    climate_hazard_index = advanced_metrics.get('climate_hazard_index', 5.0)
    
    # Extract scenario analysis (required by frontend)
    scenario_analysis = engine_result.get('scenario_analysis', {})
    
    # Extract forecast (required by frontend)
    forecast = engine_result.get('forecast', {})
    
    # Advanced parameters derived from original payload
    advanced_parameters: Dict[str, Any] = {}
    if original_payload:
        distance_val = _payload_float('distance')
        if distance_val is not None:
            advanced_parameters['distance'] = distance_val
        route_type_val = original_payload.get('route_type')
        if route_type_val:
            advanced_parameters['route_type'] = route_type_val
        carrier_rating_val = _payload_float('carrier_rating')
        if carrier_rating_val is not None:
            advanced_parameters['carrier_rating'] = carrier_rating_val
        weather_risk_val = _payload_float('weather_risk')
        if weather_risk_val is not None:
            advanced_parameters['weather_risk'] = weather_risk_val
        port_risk_val = _payload_float('port_risk')
        if port_risk_val is not None:
            advanced_parameters['port_risk'] = port_risk_val
        container_match_val = _payload_float('container_match')
        if container_match_val is not None:
            advanced_parameters['container_match'] = container_match_val
        shipment_value_val = _payload_float('shipment_value')
        if shipment_value_val is not None:
            advanced_parameters['shipment_value'] = shipment_value_val
    
    # Climate input snapshot for frontend visualizations
    climate_inputs: Dict[str, Any] = {
        "climate_hazard_index": float(climate_hazard_index)
    }
    enso_val = _payload_float('ENSO_index')
    if enso_val is not None:
        climate_inputs['ENSO_index'] = enso_val
    typhoon_val = _payload_float('typhoon_frequency')
    if typhoon_val is not None:
        climate_inputs['typhoon_frequency'] = typhoon_val
    sst_val = _payload_float('sst_anomaly')
    if sst_val is not None:
        climate_inputs['sst_anomaly'] = sst_val
    port_climate_val = _payload_float('port_climate_stress')
    if port_climate_val is not None:
        climate_inputs['port_climate_stress'] = port_climate_val
    climate_vol_val = _payload_float('climate_volatility_index')
    if climate_vol_val is not None:
        climate_inputs['climate_volatility_index'] = climate_vol_val
    tail_prob_val = _payload_float('climate_tail_event_probability')
    if tail_prob_val is not None:
        climate_inputs['climate_tail_event_probability'] = tail_prob_val
    esg_input_val = _payload_float('ESG_score')
    if esg_input_val is not None:
        climate_inputs['ESG_score'] = esg_input_val
    climate_resilience_val = _payload_float('climate_resilience')
    if climate_resilience_val is not None:
        climate_inputs['climate_resilience'] = climate_resilience_val
    green_pack_val = _payload_float('green_packaging')
    if green_pack_val is not None:
        climate_inputs['green_packaging'] = green_pack_val
    
    # Extract priority_profile and priority_weights from original payload
    priority_profile = original_payload.get('priority_profile', 'standard') if original_payload else 'standard'
    priority_weights = original_payload.get('priority_weights', {'speed': 40, 'cost': 40, 'risk': 20}) if original_payload else {'speed': 40, 'cost': 40, 'risk': 20}
    
    # Ensure all required fields exist, even if empty
    result = {
        "risk_score": risk_score,
        "risk_level": engine_result.get('risk_level', 'MODERATE'),
        "expected_loss": int(round(engine_result.get('expected_loss', 0))),
        "reliability": reliability,
        "esg": esg,
        "layers": layers if layers else [],
        "risk_factors": risk_factors if risk_factors else [],
        "radar": {
            "labels": radar_labels if radar_labels else [],
            "values": radar_values if radar_values else []
        },
        "mc_samples": mc_samples if mc_samples else [],
        "var": int(round(var_95_usd)),
        "cvar": int(round(cvar_95_usd)),
        "financial_distribution": fin_dist if fin_dist else {},
        "climate_hazard_index": float(climate_hazard_index),
        "climate_var_metrics": climate_var_metrics if climate_var_metrics else {},
        "advanced_metrics": advanced_metrics if advanced_metrics else {},
        "climate_v14": climate_inputs,
        "climate_tail_event_probability": climate_inputs.get('climate_tail_event_probability', 0.05),
        # === SCENARIO & FORECAST (required by frontend) ===============
        "scenario_analysis": scenario_analysis if scenario_analysis else {},
        "forecast": forecast if forecast else {},
        # === PRIORITY PROFILE & WEIGHTS (for gauge charts) ============
        "priority_profile": priority_profile,
        "priority_weights": priority_weights,
        "advanced_parameters": advanced_parameters if advanced_parameters else {}
    }

    # Mirror frequently used advanced parameters at the root level for backward compatibility
    for key in ['distance', 'route_type', 'carrier_rating', 'weather_risk', 'port_risk', 'container_match', 'shipment_value']:
        value = advanced_parameters.get(key)
        if value is not None:
            result[key] = value

    # Expose climate inputs on root object as well
    for climate_key in ['ENSO_index', 'typhoon_frequency', 'sst_anomaly', 'port_climate_stress',
                        'climate_volatility_index', 'ESG_score', 'climate_resilience', 'green_packaging']:
        if climate_key in climate_inputs:
            result[climate_key] = climate_inputs[climate_key]

    return result


def run_risk_engine_v14(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main service function: Map Shipment -> Engine input -> Engine output -> Option A format
    """
    try:
        # Step 1: Map Option A Shipment to engine input format
        engine_input = _map_shipment_to_engine(payload)
        
        # Step 2: Extract buyer/seller data if present
        buyer = payload.get("buyer")
        seller = payload.get("seller")
        
        # Step 3: Call actual risk engine with buyer/seller
        engine_result = calculate_enterprise_risk(engine_input, buyer=buyer, seller=seller)
        
        # Step 4: Transform engine output to Option A format
        # Pass original payload to extract ESG_score and other input fields
        result = _transform_engine_output(engine_result, original_payload=payload)
        
        # Step 5: Add buyer_seller_analysis if present
        if "buyer_seller_analysis" in engine_result:
            result["buyer_seller_analysis"] = engine_result["buyer_seller_analysis"]
        
        return result
        
    except Exception as e:
        print(f"[RISKCAST v14] ENGINE ERROR: {e}")
        import traceback
        traceback.print_exc()
        # Return default structure on error with all required fields
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
            "layer_interactions": {},
            "buyer_seller_analysis": {},
            "financial_distribution": {}
        }
