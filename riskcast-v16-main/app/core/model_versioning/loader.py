"""
Model payload loader - converts stored model to engine-ready format.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.modules.model_versioning.models import RiskModelVersion
from app.core.model_versioning.selector import ModelNotFoundError

__all__ = ['ModelLoader', 'ModelPayload']


@dataclass
class ModelPayload:
    """
    Engine-ready model payload.
    
    This is what the risk engine receives to perform calculations.
    """
    model_version_id: str  # ULID
    immutable_hash: Optional[str]
    
    # Weights
    base_weights: Dict[str, float]
    
    # Correlations
    correlation_matrix: Dict[str, float]
    
    # Tail risk parameters
    tail_parameters: Dict[str, float]
    
    # Interaction effects
    interaction_multipliers: Dict[str, float]
    
    # Loss transformation
    loss_transform_params: Dict[str, float]
    
    # Monte Carlo settings
    monte_carlo_defaults: Dict[str, Any]
    
    def get_weight(self, factor: str) -> float:
        """
        Get weight for a risk factor.
        
        Args:
            factor: Risk factor name (e.g., 'route_risk', 'cargo_risk')
            
        Returns:
            Weight value or 0.0 if not found
        """
        return self.base_weights.get(factor, 0.0)
    
    def get_correlation(self, factor1: str, factor2: str) -> float:
        """
        Get correlation between two factors.
        
        Args:
            factor1: First risk factor name
            factor2: Second risk factor name
            
        Returns:
            Correlation value or 0.0 if not found
        """
        # Try both orderings: "factor1_factor2" and "factor2_factor1"
        key = f"{factor1}_{factor2}"
        alt_key = f"{factor2}_{factor1}"
        return self.correlation_matrix.get(key) or self.correlation_matrix.get(alt_key, 0.0)
    
    def get_tail_param(self, param: str) -> float:
        """
        Get tail risk parameter.
        
        Args:
            param: Parameter name (e.g., 'degrees_of_freedom', 'tail_shock_probability')
            
        Returns:
            Parameter value or None if not found
        """
        return self.tail_parameters.get(param)
    
    def get_interaction_multiplier(self, interaction: str) -> float:
        """
        Get interaction multiplier.
        
        Args:
            interaction: Interaction name (e.g., 'high_value_perishable', 'hazmat_congested_port')
            
        Returns:
            Multiplier value or 1.0 (no effect) if not found
        """
        return self.interaction_multipliers.get(interaction, 1.0)
    
    def get_loss_transform_param(self, param: str) -> float:
        """
        Get loss transformation parameter.
        
        Args:
            param: Parameter name (e.g., 'base_loss_rate', 'risk_score_exponent')
            
        Returns:
            Parameter value or None if not found
        """
        return self.loss_transform_params.get(param)
    
    def get_mc_default(self, key: str, default: Any = None) -> Any:
        """
        Get Monte Carlo default value.
        
        Args:
            key: Setting key (e.g., 'default_iterations', 'confidence_levels')
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        return self.monte_carlo_defaults.get(key, default)


class ModelLoader:
    """Loads model version into engine-ready payload."""
    
    def load(self, model: RiskModelVersion) -> ModelPayload:
        """
        Convert database model to engine payload.
        
        Uses calibrated parameters if available, with fallbacks to defaults.
        
        Args:
            model: RiskModelVersion from database
            
        Returns:
            ModelPayload ready for engine consumption
            
        Raises:
            ValueError: If required fields are missing
        """
        # Build base weights - use calibrated if available, otherwise defaults
        if model.base_weights_json:
            base_weights = model.base_weights_json
        elif model.weights_json:
            # Fallback to legacy weights_json
            base_weights = model.weights_json
        else:
            # Use defaults for all known layers
            base_weights = {}
            for layer in ["route_risk", "cargo_risk", "transport_risk", "commercial_risk",
                         "infrastructure_risk", "weather_risk", "geopolitical_risk",
                         "seasonal_risk", "documentation_risk", "handling_risk",
                         "security_risk", "regulatory_risk", "financial_risk"]:
                base_weights[layer] = model.get_layer_weight(layer)
        
        # Build correlation matrix - use calibrated if available
        correlation_matrix = {}
        if model.correlation_matrix_json:
            # Convert from stored format to engine format
            for key, value in model.correlation_matrix_json.items():
                if ":" in key:
                    # Format: "layer1:layer2"
                    correlation_matrix[key.replace(":", "_")] = value
                else:
                    correlation_matrix[key] = value
        
        # Use defaults for optional fields
        tail_parameters = model.tail_parameters_json or {}
        interaction_multipliers = model.interaction_multipliers_json or {}
        
        # Get loss function parameters - use calibrated if available
        loss_transform_params = model.get_loss_function_params()
        
        monte_carlo_defaults = model.monte_carlo_defaults_json or {
            'default_iterations': 10000,
            'confidence_levels': [0.95, 0.99]
        }
        
        return ModelPayload(
            model_version_id=model.id,
            immutable_hash=model.immutable_hash,
            base_weights=base_weights,
            correlation_matrix=correlation_matrix,
            tail_parameters=tail_parameters,
            interaction_multipliers=interaction_multipliers,
            loss_transform_params=loss_transform_params,
            monte_carlo_defaults=monte_carlo_defaults
        )
    
    def load_by_id(self, db: Session, model_id: str) -> ModelPayload:
        """
        Load model payload by ID.
        
        Args:
            db: Database session
            model_id: Model version ID (ULID)
            
        Returns:
            ModelPayload ready for engine consumption
            
        Raises:
            ModelNotFoundError: If model is not found
            ValueError: If required fields are missing
        """
        model = db.query(RiskModelVersion).filter(
            RiskModelVersion.id == model_id
        ).first()
        
        if not model:
            raise ModelNotFoundError(f"Model {model_id} not found")
        
        return self.load(model)
