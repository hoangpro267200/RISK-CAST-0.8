"""
RISKCAST Sensitivity Analysis Service
=====================================
Analyze how changes in input parameters affect risk scores.
Generates tornado diagrams and sensitivity reports.

Author: RISKCAST Team
Version: 2.0
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
import copy

logger = logging.getLogger(__name__)


@dataclass
class SensitivityResult:
    """Result for a single parameter sensitivity analysis."""
    parameter: str
    baseline_value: float
    low_value: float
    high_value: float
    low_score: float
    high_score: float
    baseline_score: float
    low_delta: float
    high_delta: float
    sensitivity: float  # Total range (high - low)
    elasticity: float  # % change in score / % change in parameter


@dataclass
class TornadoResult:
    """Complete tornado analysis result."""
    baseline_score: float
    sensitivities: List[SensitivityResult]
    most_sensitive: str
    least_sensitive: str
    total_parameters: int


class SensitivityAnalyzer:
    """
    Analyze how changes in input parameters affect risk score.
    
    Provides:
    1. Tornado diagrams showing parameter importance
    2. Elasticity analysis
    3. Threshold analysis (what parameter values trigger risk level changes)
    """
    
    # Parameters that can be varied and their expected types
    ANALYZABLE_PARAMETERS = {
        'cargo_value': {'type': 'numeric', 'min': 100, 'max': 10_000_000},
        'transit_time': {'type': 'numeric', 'min': 1, 'max': 365},
        'carrier_rating': {'type': 'numeric', 'min': 0, 'max': 10},
        'container_match': {'type': 'numeric', 'min': 0, 'max': 10},
        'packaging_quality': {'type': 'numeric', 'min': 0, 'max': 10},
        'weather_risk': {'type': 'numeric', 'min': 0, 'max': 100},
        'port_risk': {'type': 'numeric', 'min': 0, 'max': 100},
        'distance': {'type': 'numeric', 'min': 100, 'max': 30_000},
        'ENSO_index': {'type': 'numeric', 'min': -3, 'max': 3},
        'typhoon_frequency': {'type': 'numeric', 'min': 0, 'max': 1},
        'ESG_score': {'type': 'numeric', 'min': 0, 'max': 100},
        'climate_resilience': {'type': 'numeric', 'min': 0, 'max': 10},
    }
    
    def __init__(self, risk_calculator_func: Optional[callable] = None):
        """
        Initialize analyzer.
        
        Args:
            risk_calculator_func: Function that takes shipment dict and returns
                                 dict with 'risk_score' or 'overall_risk' key.
                                 If None, uses default engine.
        """
        if risk_calculator_func is None:
            from app.core.engine.risk_engine_v16 import calculate_enterprise_risk
            self.calculate_risk = calculate_enterprise_risk
        else:
            self.calculate_risk = risk_calculator_func
        
        self.baseline_shipment: Optional[Dict] = None
        self.baseline_score: Optional[float] = None
    
    def _get_risk_score(self, shipment: Dict) -> float:
        """Extract risk score from engine result."""
        result = self.calculate_risk(shipment)
        
        # Handle different result formats
        if 'risk_score' in result:
            return float(result['risk_score'])
        elif 'overall_risk' in result:
            # Convert 0-10 to 0-100 scale
            return float(result['overall_risk']) * 10
        else:
            raise ValueError("Engine result missing risk_score or overall_risk")
    
    def run_tornado_analysis(
        self, 
        baseline_shipment: Dict,
        parameters: Optional[List[str]] = None,
        variation_pct: float = 0.2
    ) -> TornadoResult:
        """
        Create tornado diagram showing parameter sensitivity.
        
        Args:
            baseline_shipment: Base shipment data to vary from
            parameters: List of parameters to vary (None = all analyzable)
            variation_pct: How much to vary each parameter (±20% default)
            
        Returns:
            TornadoResult with ordered sensitivities
        """
        self.baseline_shipment = copy.deepcopy(baseline_shipment)
        self.baseline_score = self._get_risk_score(self.baseline_shipment)
        
        if parameters is None:
            # Only analyze parameters that exist in the shipment
            parameters = [
                p for p in self.ANALYZABLE_PARAMETERS.keys()
                if p in baseline_shipment and baseline_shipment[p] is not None
            ]
        
        logger.info(f"Running tornado analysis on {len(parameters)} parameters")
        
        sensitivities: List[SensitivityResult] = []
        
        for param in parameters:
            try:
                result = self._analyze_single_parameter(
                    param, variation_pct
                )
                sensitivities.append(result)
            except Exception as e:
                logger.warning(f"Could not analyze {param}: {e}")
        
        # Sort by sensitivity (descending)
        sensitivities.sort(key=lambda x: x.sensitivity, reverse=True)
        
        return TornadoResult(
            baseline_score=self.baseline_score,
            sensitivities=sensitivities,
            most_sensitive=sensitivities[0].parameter if sensitivities else None,
            least_sensitive=sensitivities[-1].parameter if sensitivities else None,
            total_parameters=len(sensitivities)
        )
    
    def _analyze_single_parameter(
        self, 
        param: str, 
        variation_pct: float
    ) -> SensitivityResult:
        """Analyze sensitivity to a single parameter."""
        original_value = self.baseline_shipment.get(param)
        
        if original_value is None or original_value == 0:
            # Handle zero or missing values
            param_config = self.ANALYZABLE_PARAMETERS.get(param, {})
            original_value = (param_config.get('max', 100) + param_config.get('min', 0)) / 2
        
        original_value = float(original_value)
        
        # Calculate low and high values
        low_value = original_value * (1 - variation_pct)
        high_value = original_value * (1 + variation_pct)
        
        # Clamp to parameter bounds
        param_config = self.ANALYZABLE_PARAMETERS.get(param, {})
        low_value = max(low_value, param_config.get('min', 0))
        high_value = min(high_value, param_config.get('max', float('inf')))
        
        # Test low value
        test_shipment = copy.deepcopy(self.baseline_shipment)
        test_shipment[param] = low_value
        low_score = self._get_risk_score(test_shipment)
        
        # Test high value
        test_shipment[param] = high_value
        high_score = self._get_risk_score(test_shipment)
        
        # Calculate metrics
        sensitivity = abs(high_score - low_score)
        
        # Elasticity: (% change in score) / (% change in parameter)
        score_pct_change = (high_score - low_score) / max(self.baseline_score, 1)
        param_pct_change = (high_value - low_value) / max(original_value, 1)
        elasticity = score_pct_change / max(param_pct_change, 0.001)
        
        return SensitivityResult(
            parameter=param,
            baseline_value=original_value,
            low_value=low_value,
            high_value=high_value,
            low_score=low_score,
            high_score=high_score,
            baseline_score=self.baseline_score,
            low_delta=low_score - self.baseline_score,
            high_delta=high_score - self.baseline_score,
            sensitivity=sensitivity,
            elasticity=elasticity
        )
    
    def find_threshold_values(
        self,
        baseline_shipment: Dict,
        param: str,
        target_risk_levels: List[int] = [25, 50, 75]
    ) -> Dict[int, Optional[float]]:
        """
        Find parameter values that trigger specific risk levels.
        
        Args:
            baseline_shipment: Base shipment data
            param: Parameter to analyze
            target_risk_levels: Risk score thresholds to find
            
        Returns:
            Dict mapping target level to parameter value (or None if not reachable)
        """
        self.baseline_shipment = copy.deepcopy(baseline_shipment)
        param_config = self.ANALYZABLE_PARAMETERS.get(param, {'min': 0, 'max': 100})
        
        results = {}
        
        for target in target_risk_levels:
            # Binary search for parameter value
            low = param_config.get('min', 0)
            high = param_config.get('max', 100)
            
            found_value = None
            
            for _ in range(20):  # Max iterations
                mid = (low + high) / 2
                
                test_shipment = copy.deepcopy(self.baseline_shipment)
                test_shipment[param] = mid
                score = self._get_risk_score(test_shipment)
                
                if abs(score - target) < 1:  # Within 1 point
                    found_value = mid
                    break
                
                if score < target:
                    low = mid
                else:
                    high = mid
            
            results[target] = found_value
        
        return results
    
    def generate_report(self, tornado_result: TornadoResult) -> Dict:
        """Generate sensitivity analysis report as dictionary."""
        return {
            'baseline_score': tornado_result.baseline_score,
            'most_sensitive_parameter': tornado_result.most_sensitive,
            'least_sensitive_parameter': tornado_result.least_sensitive,
            'total_parameters_analyzed': tornado_result.total_parameters,
            'sensitivities': [asdict(s) for s in tornado_result.sensitivities],
            'interpretation': self._generate_interpretation(tornado_result)
        }
    
    def _generate_interpretation(self, result: TornadoResult) -> str:
        """Generate human-readable interpretation."""
        if not result.sensitivities:
            return "No parameters analyzed."
        
        top_3 = result.sensitivities[:3]
        
        interpretation = f"""
Risk Score Sensitivity Analysis Summary:
- Baseline risk score: {result.baseline_score:.1f}/100
- Most sensitive to: {result.most_sensitive} (±{top_3[0].sensitivity:.1f} points)

Top 3 influential parameters:
"""
        for i, s in enumerate(top_3, 1):
            interpretation += f"""
{i}. {s.parameter}:
   - Varying ±20% changes score by {s.sensitivity:.1f} points
   - Elasticity: {s.elasticity:.2f} (1% param change → {s.elasticity:.2f}% score change)
"""
        
        return interpretation
    
    def plot_tornado(
        self, 
        tornado_result: TornadoResult,
        save_path: str = 'tornado_diagram.png',
        top_n: int = 10
    ):
        """Generate tornado diagram visualization."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning("matplotlib not available for plotting")
            return
        
        # Take top N sensitivities
        sensitivities = tornado_result.sensitivities[:top_n]
        
        fig, ax = plt.subplots(figsize=(12, len(sensitivities) * 0.6 + 2))
        
        params = [s.parameter for s in sensitivities]
        low_deltas = [s.low_delta for s in sensitivities]
        high_deltas = [s.high_delta for s in sensitivities]
        
        y_pos = np.arange(len(params))
        
        # Plot bars
        bars_low = ax.barh(y_pos, low_deltas, color='#d62728', alpha=0.7, 
                          label='Low Value (-20%)')
        bars_high = ax.barh(y_pos, high_deltas, color='#2ca02c', alpha=0.7, 
                           label='High Value (+20%)')
        
        # Baseline line
        ax.axvline(x=0, color='black', linewidth=2, linestyle='-')
        
        # Formatting
        ax.set_yticks(y_pos)
        ax.set_yticklabels(params, fontsize=10)
        ax.set_xlabel('Change in Risk Score (points)', fontsize=12)
        ax.set_title(
            f'Tornado Diagram: Parameter Sensitivity\n'
            f'Baseline Score: {tornado_result.baseline_score:.1f}',
            fontsize=14, fontweight='bold'
        )
        ax.legend(loc='lower right', fontsize=10)
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, (s, low_bar, high_bar) in enumerate(zip(sensitivities, bars_low, bars_high)):
            if s.low_delta < 0:
                ax.text(s.low_delta - 0.5, i, f'{s.low_delta:.1f}', 
                       va='center', ha='right', fontsize=8)
            if s.high_delta > 0:
                ax.text(s.high_delta + 0.5, i, f'+{s.high_delta:.1f}', 
                       va='center', ha='left', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Tornado diagram saved to {save_path}")
        plt.close()


# Convenience function for API integration
def analyze_shipment_sensitivity(
    shipment_data: Dict,
    parameters: Optional[List[str]] = None,
    variation_pct: float = 0.2
) -> Dict:
    """
    Analyze sensitivity of a shipment to parameter variations.
    
    Args:
        shipment_data: Shipment data dictionary
        parameters: Parameters to analyze (None = auto-detect)
        variation_pct: Variation percentage (default 20%)
        
    Returns:
        Sensitivity analysis report
    """
    analyzer = SensitivityAnalyzer()
    result = analyzer.run_tornado_analysis(
        baseline_shipment=shipment_data,
        parameters=parameters,
        variation_pct=variation_pct
    )
    return analyzer.generate_report(result)
