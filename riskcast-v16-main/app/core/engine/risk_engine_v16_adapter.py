"""
Adapter for RiskEngineV16 to accept model parameters from ModelPayload.

This adapter bridges the gap between the versioned model system and
the existing V16 engine implementation.
"""

from typing import Dict, Any
import numpy as np

from app.core.model_versioning.loader import ModelPayload
from app.core.engine.risk_engine_v16 import (
    EnterpriseRiskEngineV16,
    run_monte_carlo,
    MonteCarloResult
)


class RiskEngineV16Adapter:
    """
    Adapter that converts ModelPayload to V16 engine parameters.
    
    This allows the V16 engine to work with versioned models while
    maintaining backward compatibility.
    """
    
    def __init__(self):
        """Initialize the adapter."""
        self.v16_engine = EnterpriseRiskEngineV16()
    
    def run_monte_carlo(
        self,
        input_data: dict,
        model_payload: ModelPayload,
        iterations: int,
        rng: np.random.Generator
    ) -> dict:
        """
        Run Monte Carlo simulation with provided model parameters.
        
        Args:
            input_data: Canonical input data (must contain 'layers', 'weights', 'context')
            model_payload: Model parameters from versioned model
            iterations: Number of Monte Carlo iterations
            rng: Seeded numpy random generator
            
        Returns:
            Dict with risk scores, VaR, CVaR, etc.
        """
        # Validate weights sum to 1.0
        weight_sum = sum(model_payload.base_weights.values())
        if abs(weight_sum - 1.0) > 0.001:
            raise ValueError(
                f"Model weights must sum to 1.0, got {weight_sum} "
                f"(model_version_id: {model_payload.model_version_id})"
            )
        
        # Extract tail parameters with defaults
        tail_params = model_payload.tail_parameters
        degrees_of_freedom = tail_params.get('degrees_of_freedom', 4)
        tail_shock_prob = tail_params.get('tail_shock_probability', 0.05)
        extreme_multiplier = tail_params.get('extreme_loss_multiplier', 2.5)
        
        # Extract loss transform parameters
        loss_params = model_payload.loss_transform_params
        base_loss_rate = loss_params.get('base_loss_rate', 0.02)
        risk_score_exponent = loss_params.get('risk_score_exponent', 1.5)
        min_loss_pct = loss_params.get('min_loss_pct', 0.001)
        max_loss_pct = loss_params.get('max_loss_pct', 0.15)
        
        # Get Monte Carlo defaults
        mc_defaults = model_payload.monte_carlo_defaults
        confidence_levels = mc_defaults.get('confidence_levels', [0.95, 0.99])
        
        # Convert model weights to numpy array format expected by V16
        # V16 expects weights as numpy array matching layer order
        # We need to map model payload weights to V16 layer structure
        layers = input_data.get('layers', {})
        if not layers:
            raise ValueError("Input data must contain 'layers' key")
        
        # Map model payload weights to V16 layer weights
        # Model payload has: route_risk, cargo_risk, carrier_risk, timing_risk, weather_risk, geopolitical_risk
        # V16 expects layer-specific weights
        v16_weights = self._map_weights_to_v16_layers(
            model_payload.base_weights,
            list(layers.keys())
        )
        
        # Build correlation matrix for V16
        v16_correlation = self._build_v16_correlation_matrix(
            model_payload.correlation_matrix,
            list(layers.keys())
        )
        
        # Prepare input for V16 engine
        v16_input = {
            'layers': layers,
            'weights': v16_weights,
            'context': input_data.get('context', {}),
            'climate_vars': input_data.get('climate_vars')
        }
        
        # Run V16 Monte Carlo
        mc_result: MonteCarloResult = run_monte_carlo(
            input_data=v16_input,
            iterations=iterations,
            seed=rng.integers(0, 2**32),  # Extract seed from generator
            rng=rng
        )
        
        # Extract metrics
        metrics = mc_result.metrics
        
        # Calculate VaR and CVaR at confidence levels
        distribution = mc_result.risk_distribution
        var_95 = np.percentile(distribution, (1 - 0.95) * 100) if 0.95 in confidence_levels else metrics.get('var_95', 0.0)
        var_99 = np.percentile(distribution, (1 - 0.99) * 100) if 0.99 in confidence_levels else metrics.get('var_99', 0.0)
        
        # Calculate CVaR (Conditional VaR)
        cvar_95 = np.mean(distribution[distribution <= var_95]) if 0.95 in confidence_levels else metrics.get('cvar_95', 0.0)
        cvar_99 = np.mean(distribution[distribution <= var_99]) if 0.99 in confidence_levels else metrics.get('cvar_99', 0.0)
        
        # Calculate expected loss using loss transform parameters
        overall_risk = metrics.get('mean', 0.0)
        expected_loss = self._calculate_expected_loss(
            overall_risk,
            base_loss_rate,
            risk_score_exponent,
            min_loss_pct,
            max_loss_pct
        )
        
        # Build risk factors from layer scores
        risk_factors = {}
        for layer_name, layer_data in layers.items():
            if isinstance(layer_data, dict):
                risk_factors[layer_name] = layer_data.get('score', 0.0)
            else:
                risk_factors[layer_name] = float(layer_data) if isinstance(layer_data, (int, float)) else 0.0
        
        return {
            'overall_risk_score': overall_risk,
            'risk_factors': risk_factors,
            'var_95': float(var_95),
            'var_99': float(var_99),
            'cvar_95': float(cvar_95),
            'cvar_99': float(cvar_99),
            'expected_loss': expected_loss,
            'risk_drivers': self._extract_risk_drivers(layers, v16_weights),
            'recommendations': [],
            'loss_distribution': distribution.tolist() if len(distribution) < 10000 else None  # Only include if reasonable size
        }
    
    def _map_weights_to_v16_layers(
        self,
        model_weights: Dict[str, float],
        layer_names: list
    ) -> np.ndarray:
        """
        Map model payload weights to V16 layer structure.
        
        Model payload has simplified weights (route_risk, cargo_risk, etc.)
        V16 expects weights for specific layers (route_complexity, cargo_sensitivity, etc.)
        
        Args:
            model_weights: Weights from model payload
            layer_names: List of V16 layer names
            
        Returns:
            Numpy array of weights matching layer order
        """
        # Default mapping from model weights to V16 layers
        weight_mapping = {
            'route_risk': ['route_complexity'],
            'cargo_risk': ['cargo_sensitivity', 'packaging_quality'],
            'carrier_risk': ['carrier_reliability'],
            'timing_risk': ['transit_time_variance', 'priority_level'],
            'weather_risk': ['weather_exposure', 'climate_tail_risk'],
            'geopolitical_risk': ['pol_congestion_risk', 'pod_customs_risk']
        }
        
        # Initialize weights array
        weights = np.zeros(len(layer_names))
        
        # Distribute model weights to V16 layers
        for model_key, model_weight in model_weights.items():
            v16_layers = weight_mapping.get(model_key, [])
            if v16_layers:
                # Distribute weight evenly among mapped layers
                weight_per_layer = model_weight / len(v16_layers)
                for v16_layer in v16_layers:
                    if v16_layer in layer_names:
                        idx = layer_names.index(v16_layer)
                        weights[idx] = weight_per_layer
        
        # Normalize to ensure sum is 1.0
        if weights.sum() > 0:
            weights = weights / weights.sum()
        
        return weights
    
    def _build_v16_correlation_matrix(
        self,
        model_correlations: Dict[str, float],
        layer_names: list
    ) -> np.ndarray:
        """
        Build V16 correlation matrix from model payload correlations.
        
        Args:
            model_correlations: Correlation dict from model payload
            layer_names: List of V16 layer names
            
        Returns:
            Numpy correlation matrix
        """
        n = len(layer_names)
        corr_matrix = np.eye(n)  # Identity matrix (no correlation by default)
        
        # Map model correlations to V16 layer pairs
        # This is a simplified mapping - in production, you'd want a more sophisticated mapping
        for corr_key, corr_value in model_correlations.items():
            # Parse correlation key (e.g., "route_cargo" -> route and cargo)
            parts = corr_key.split('_')
            if len(parts) >= 2:
                # Try to find matching layers
                # This is simplified - production would need better mapping logic
                pass  # TODO: Implement proper correlation mapping
        
        return corr_matrix
    
    def _calculate_expected_loss(
        self,
        risk_score: float,
        base_loss_rate: float,
        exponent: float,
        min_loss: float,
        max_loss: float
    ) -> float:
        """
        Calculate expected loss from risk score using transform parameters.
        
        Args:
            risk_score: Overall risk score
            base_loss_rate: Base loss rate
            exponent: Risk score exponent
            min_loss: Minimum loss percentage
            max_loss: Maximum loss percentage
            
        Returns:
            Expected loss as percentage
        """
        # Transform risk score to loss rate
        # Formula: loss = base_loss_rate * (risk_score / max_risk) ^ exponent
        max_risk = 10.0  # V16 uses 0-10 scale
        normalized_risk = risk_score / max_risk
        loss_rate = base_loss_rate * (normalized_risk ** exponent)
        
        # Clamp to min/max bounds
        loss_rate = max(min_loss, min(max_loss, loss_rate))
        
        return loss_rate
    
    def _extract_risk_drivers(
        self,
        layers: Dict[str, Any],
        weights: np.ndarray
    ) -> Dict[str, Any]:
        """
        Extract top risk drivers from layers and weights.
        
        Args:
            layers: Layer data
            weights: Layer weights
            
        Returns:
            Dict with risk driver analysis
        """
        drivers = {}
        layer_names = list(layers.keys())
        
        # Find top contributing layers
        if len(weights) == len(layer_names):
            # Sort by weighted contribution
            contributions = [
                (name, weight * (layers[name].get('score', 0.0) if isinstance(layers[name], dict) else float(layers[name]) if isinstance(layers[name], (int, float)) else 0.0))
                for name, weight in zip(layer_names, weights)
            ]
            contributions.sort(key=lambda x: x[1], reverse=True)
            
            drivers['top_contributors'] = [
                {'layer': name, 'contribution': float(contrib)}
                for name, contrib in contributions[:5]
            ]
        
        return drivers
