"""
RISKCAST Uncertainty Quantification
====================================
Provide confidence intervals for risk predictions.
Replaces point estimates with proper uncertainty bounds.

Methods:
1. Bootstrap confidence intervals
2. Bayesian credible intervals
3. Monte Carlo variance decomposition

Author: RISKCAST Team
Version: 2.0
"""

import numpy as np
from scipy import stats
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class UncertaintyInterval:
    """Uncertainty interval for a risk score."""
    point_estimate: float
    lower_bound: float
    upper_bound: float
    interval_width: float
    confidence_level: float
    method: str
    
    def contains(self, value: float) -> bool:
        """Check if a value falls within the interval."""
        return self.lower_bound <= value <= self.upper_bound


@dataclass
class UncertaintyReport:
    """Complete uncertainty analysis report."""
    risk_score: float
    interval: UncertaintyInterval
    variance_decomposition: Optional[Dict[str, float]]
    reliability_grade: str  # A, B, C, D, F
    interpretation: str


class UncertaintyQuantifier:
    """
    Provide confidence intervals for risk predictions.
    
    CRITICAL for insurance/enterprise use:
    - Point estimates are insufficient
    - Decision makers need uncertainty bounds
    - Required for regulatory compliance (Basel/Solvency)
    """
    
    # Reliability grading based on interval width
    GRADE_THRESHOLDS = {
        'A': 10,   # Very narrow interval (< 10 points)
        'B': 20,   # Narrow interval (< 20 points)
        'C': 30,   # Moderate interval (< 30 points)
        'D': 50,   # Wide interval (< 50 points)
        'F': 100,  # Very wide (>= 50 points)
    }
    
    @staticmethod
    def bootstrap_confidence_interval(
        risk_score: float,
        monte_carlo_results: np.ndarray,
        confidence_level: float = 0.95,
        n_bootstrap: int = 1000
    ) -> UncertaintyInterval:
        """
        Compute bootstrap confidence interval for risk score.
        
        Args:
            risk_score: Point estimate of risk score
            monte_carlo_results: Array of MC simulation results
            confidence_level: Confidence level (default 95%)
            n_bootstrap: Number of bootstrap samples
            
        Returns:
            UncertaintyInterval object
        """
        if len(monte_carlo_results) < 10:
            logger.warning("Too few MC samples for reliable bootstrap CI")
            # Return wide interval indicating high uncertainty
            return UncertaintyInterval(
                point_estimate=risk_score,
                lower_bound=max(0, risk_score - 30),
                upper_bound=min(100, risk_score + 30),
                interval_width=60,
                confidence_level=confidence_level,
                method='bootstrap_insufficient_data'
            )
        
        monte_carlo_results = np.asarray(monte_carlo_results).flatten()
        
        # Bootstrap resampling
        bootstrap_means = []
        for _ in range(n_bootstrap):
            sample = np.random.choice(
                monte_carlo_results, 
                size=len(monte_carlo_results), 
                replace=True
            )
            bootstrap_means.append(np.mean(sample))
        
        bootstrap_means = np.array(bootstrap_means)
        
        # Compute percentile interval
        alpha = 1 - confidence_level
        lower = np.percentile(bootstrap_means, alpha/2 * 100)
        upper = np.percentile(bootstrap_means, (1 - alpha/2) * 100)
        
        return UncertaintyInterval(
            point_estimate=risk_score,
            lower_bound=max(0, float(lower)),
            upper_bound=min(100, float(upper)),
            interval_width=float(upper - lower),
            confidence_level=confidence_level,
            method='bootstrap'
        )
    
    @staticmethod
    def bayesian_credible_interval(
        risk_score: float,
        prior_mean: float = 50.0,
        prior_std: float = 20.0,
        observation_std: float = 10.0,
        confidence_level: float = 0.95
    ) -> UncertaintyInterval:
        """
        Compute Bayesian credible interval.
        
        Uses Normal-Normal conjugate prior:
        - Prior: N(prior_mean, prior_std^2)
        - Likelihood: N(risk_score, observation_std^2)
        - Posterior: N(posterior_mean, posterior_std^2)
        
        Args:
            risk_score: Observed risk score
            prior_mean: Prior mean (domain knowledge)
            prior_std: Prior standard deviation
            observation_std: Standard deviation of observations
            confidence_level: Credible interval level
            
        Returns:
            UncertaintyInterval object
        """
        # Posterior parameters (Normal-Normal conjugate)
        prior_precision = 1 / (prior_std ** 2)
        obs_precision = 1 / (observation_std ** 2)
        
        posterior_precision = prior_precision + obs_precision
        posterior_std = 1 / np.sqrt(posterior_precision)
        
        posterior_mean = (
            prior_mean * prior_precision + risk_score * obs_precision
        ) / posterior_precision
        
        # Credible interval
        alpha = 1 - confidence_level
        lower = stats.norm.ppf(alpha/2, loc=posterior_mean, scale=posterior_std)
        upper = stats.norm.ppf(1 - alpha/2, loc=posterior_mean, scale=posterior_std)
        
        return UncertaintyInterval(
            point_estimate=float(posterior_mean),
            lower_bound=max(0, float(lower)),
            upper_bound=min(100, float(upper)),
            interval_width=float(upper - lower),
            confidence_level=confidence_level,
            method='bayesian'
        )
    
    @staticmethod
    def mc_variance_decomposition(
        layer_contributions: Dict[str, float],
        layer_variances: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Decompose total variance by risk layer.
        
        Shows how much each layer contributes to overall uncertainty.
        
        Args:
            layer_contributions: Contribution of each layer to total score
            layer_variances: Variance/uncertainty of each layer
            
        Returns:
            Dict mapping layer name to variance contribution %
        """
        if not layer_contributions or not layer_variances:
            return {}
        
        # Compute variance contribution (assuming independence)
        total_variance = 0.0
        layer_var_contributions = {}
        
        for layer, contribution in layer_contributions.items():
            var = layer_variances.get(layer, 1.0)
            # Contribution^2 * Variance (for weighted sum)
            layer_var_contributions[layer] = (contribution ** 2) * var
            total_variance += layer_var_contributions[layer]
        
        # Normalize to percentages
        if total_variance > 0:
            variance_decomposition = {
                layer: (var_contrib / total_variance) * 100
                for layer, var_contrib in layer_var_contributions.items()
            }
        else:
            variance_decomposition = {layer: 0.0 for layer in layer_contributions}
        
        return variance_decomposition
    
    @classmethod
    def grade_reliability(cls, interval_width: float) -> str:
        """
        Assign reliability grade based on interval width.
        
        Args:
            interval_width: Width of confidence interval
            
        Returns:
            Letter grade (A, B, C, D, F)
        """
        for grade, threshold in sorted(cls.GRADE_THRESHOLDS.items()):
            if interval_width < threshold:
                return grade
        return 'F'
    
    @classmethod
    def generate_interpretation(
        cls, 
        interval: UncertaintyInterval,
        grade: str
    ) -> str:
        """Generate human-readable interpretation of uncertainty."""
        
        interpretations = {
            'A': "HIGH CONFIDENCE: Risk score is highly reliable. "
                 "The narrow confidence interval indicates strong data quality "
                 "and consistent risk factors.",
            
            'B': "GOOD CONFIDENCE: Risk score is reasonably reliable. "
                 "Minor variations in inputs would not significantly change "
                 "the risk assessment.",
            
            'C': "MODERATE CONFIDENCE: Risk score has moderate uncertainty. "
                 "Consider gathering additional data to narrow the interval. "
                 "Use the upper bound for conservative decision-making.",
            
            'D': "LOW CONFIDENCE: Risk score has significant uncertainty. "
                 "The wide interval suggests missing data or high variability "
                 "in risk factors. Use with caution.",
            
            'F': "VERY LOW CONFIDENCE: Risk score is highly uncertain. "
                 "Do not make critical decisions based on this estimate alone. "
                 "Gather additional data before proceeding."
        }
        
        base_interpretation = interpretations.get(grade, interpretations['F'])
        
        return (
            f"{base_interpretation}\n\n"
            f"Risk Score: {interval.point_estimate:.1f} "
            f"(95% CI: {interval.lower_bound:.1f} - {interval.upper_bound:.1f})\n"
            f"Interval Width: {interval.interval_width:.1f} points"
        )
    
    @classmethod
    def full_uncertainty_analysis(
        cls,
        risk_score: float,
        monte_carlo_results: Optional[np.ndarray] = None,
        layer_contributions: Optional[Dict[str, float]] = None,
        layer_variances: Optional[Dict[str, float]] = None,
        method: str = 'bootstrap',
        confidence_level: float = 0.95
    ) -> UncertaintyReport:
        """
        Run complete uncertainty analysis.
        
        Args:
            risk_score: Point estimate of risk
            monte_carlo_results: MC simulation results (for bootstrap)
            layer_contributions: Layer contributions (for variance decomposition)
            layer_variances: Layer variances (for variance decomposition)
            method: 'bootstrap' or 'bayesian'
            confidence_level: Confidence level
            
        Returns:
            UncertaintyReport object
        """
        # Compute interval
        if method == 'bootstrap' and monte_carlo_results is not None:
            interval = cls.bootstrap_confidence_interval(
                risk_score, monte_carlo_results, confidence_level
            )
        else:
            interval = cls.bayesian_credible_interval(
                risk_score, confidence_level=confidence_level
            )
        
        # Variance decomposition
        variance_decomp = None
        if layer_contributions and layer_variances:
            variance_decomp = cls.mc_variance_decomposition(
                layer_contributions, layer_variances
            )
        
        # Grade and interpretation
        grade = cls.grade_reliability(interval.interval_width)
        interpretation = cls.generate_interpretation(interval, grade)
        
        return UncertaintyReport(
            risk_score=risk_score,
            interval=interval,
            variance_decomposition=variance_decomp,
            reliability_grade=grade,
            interpretation=interpretation
        )
    
    @classmethod
    def to_api_format(cls, report: UncertaintyReport) -> Dict:
        """Convert UncertaintyReport to API response format."""
        return {
            'risk_score': report.risk_score,
            'uncertainty': {
                'point_estimate': report.interval.point_estimate,
                'confidence_level': report.interval.confidence_level,
                'lower_bound': report.interval.lower_bound,
                'upper_bound': report.interval.upper_bound,
                'interval_width': report.interval.interval_width,
                'method': report.interval.method
            },
            'reliability_grade': report.reliability_grade,
            'variance_decomposition': report.variance_decomposition,
            'interpretation': report.interpretation
        }


# Integration helper for risk engine
def add_uncertainty_to_result(
    engine_result: Dict,
    monte_carlo_results: Optional[np.ndarray] = None
) -> Dict:
    """
    Add uncertainty quantification to engine result.
    
    Args:
        engine_result: Result from risk engine
        monte_carlo_results: Optional MC results
        
    Returns:
        Engine result with 'uncertainty' field added
    """
    risk_score = engine_result.get('risk_score', engine_result.get('overall_risk', 0) * 10)
    
    # Extract layer info for variance decomposition
    layers = engine_result.get('layers', engine_result.get('risk_factors', []))
    layer_contributions = {}
    layer_variances = {}
    
    for layer in layers:
        if isinstance(layer, dict):
            name = layer.get('name', 'unknown')
            score = layer.get('score', 0)
            layer_contributions[name] = score
            # Estimate variance as 10% of score (simplified)
            layer_variances[name] = (score * 0.1) ** 2
    
    # Run analysis
    report = UncertaintyQuantifier.full_uncertainty_analysis(
        risk_score=risk_score,
        monte_carlo_results=monte_carlo_results,
        layer_contributions=layer_contributions,
        layer_variances=layer_variances,
        method='bootstrap' if monte_carlo_results is not None else 'bayesian'
    )
    
    # Add to result
    engine_result['uncertainty'] = UncertaintyQuantifier.to_api_format(report)
    
    return engine_result
