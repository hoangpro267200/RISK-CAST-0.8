"""
===============================================================
RISKCAST v14.5 — Climate Intelligence Upgrade Module
Enterprise-Grade Climate Risk Analytics

Provides:
- ClimateVariables: Core climate data structure
- ClimateRiskLayerExtensions: Climate adjustments for risk layers
- ClimateMonteCarloExtension: Climate tail shocks & VaR
- ESGClimateResilience: ESG-based climate resilience scoring
- ClimateAIAnalysis: AI-powered climate narrative generation

Author: Kai × Hoàng | v14.5 Climate Intelligence
===============================================================
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from scipy import stats


# ================================================================
# CLIMATE VARIABLES
# ================================================================

@dataclass
class ClimateVariables:
    """Core climate variables for risk assessment"""
    ENSO_index: float = 0.0  # El Niño Southern Oscillation index
    seasonal_typhoon_frequency: float = 0.5  # Typhoon frequency (0-1)
    sea_surface_temperature_anomaly: float = 0.0  # SST anomaly (°C)
    port_climate_stress_score: float = 5.0  # Port stress (0-10)
    long_term_climate_volatility_index: float = 5.0  # Volatility index (0-10)
    climate_tail_event_probability: float = 0.05  # Extreme event probability
    ESG_score: float = 50.0  # ESG score (0-100)
    climate_resilience_score: float = 5.0  # Resilience score (0-10)
    green_packaging_score: float = 5.0  # Green packaging (0-10)
    
    def calculate_CHI(self) -> float:
        """
        Calculate Climate Hazard Index (CHI) from all variables
        
        CHI = weighted combination of climate factors
        Returns: CHI value [0-10]
        """
        # Normalize ENSO index (typically -3 to +3)
        normalized_enso = np.clip((self.ENSO_index + 3) / 6, 0, 1) * 10
        
        # Combine factors with weights
        chi = (
            0.25 * normalized_enso +
            0.20 * self.seasonal_typhoon_frequency * 10 +
            0.15 * np.clip(abs(self.sea_surface_temperature_anomaly) * 2, 0, 10) +
            0.15 * self.port_climate_stress_score +
            0.10 * self.long_term_climate_volatility_index +
            0.10 * self.climate_tail_event_probability * 10 +
            0.05 * (1 - self.climate_resilience_score / 10) * 10
        )
        
        return np.clip(chi, 0.0, 10.0)


# ================================================================
# CLIMATE RISK LAYER EXTENSIONS
# ================================================================

class ClimateRiskLayerExtensions:
    """Extend risk layers with climate-adjusted scoring"""
    
    @staticmethod
    def adjust_weather_exposure(
        base_score: float,
        climate_vars: ClimateVariables,
        context: Dict[str, Any] = None
    ) -> float:
        """Adjust weather exposure layer based on climate variables"""
        context = context or {}
        
        # ENSO impact on weather patterns
        enso_factor = 1.0 + abs(climate_vars.ENSO_index) * 0.1
        
        # Typhoon frequency impact
        typhoon_factor = 1.0 + climate_vars.seasonal_typhoon_frequency * 0.3
        
        # SST anomaly impact
        sst_factor = 1.0 + abs(climate_vars.sea_surface_temperature_anomaly) * 0.15
        
        adjusted = base_score * enso_factor * typhoon_factor * sst_factor
        
        return np.clip(adjusted, 0.0, 10.0)
    
    @staticmethod
    def adjust_port_risk(
        base_score: float,
        climate_vars: ClimateVariables,
        context: Dict[str, Any] = None
    ) -> float:
        """Adjust port risk layer based on climate variables"""
        context = context or {}
        
        # Port climate stress impact
        port_stress_factor = 1.0 + (climate_vars.port_climate_stress_score - 5.0) / 10.0
        
        # Climate volatility impact
        volatility_factor = 1.0 + (climate_vars.long_term_climate_volatility_index - 5.0) / 15.0
        
        adjusted = base_score * port_stress_factor * volatility_factor
        
        return np.clip(adjusted, 0.0, 10.0)
    
    @staticmethod
    def adjust_transport_reliability(
        base_score: float,
        transport_mode: str,
        climate_vars: ClimateVariables,
        context: Dict[str, Any] = None
    ) -> float:
        """Adjust transport reliability based on climate variables"""
        context = context or {}
        
        # Mode-specific climate sensitivity
        mode_sensitivity = {
            'sea': 1.5,  # Ocean freight highly sensitive
            'air': 0.8,  # Air freight less sensitive
            'road': 1.2,  # Road sensitive to weather
            'rail': 1.1,  # Rail moderately sensitive
            'multimodal': 1.3
        }
        sensitivity = mode_sensitivity.get(transport_mode.lower(), 1.0)
        
        # Climate impact
        climate_factor = 1.0 + (
            climate_vars.seasonal_typhoon_frequency * sensitivity * 0.2 +
            abs(climate_vars.ENSO_index) * 0.1
        )
        
        adjusted = base_score * climate_factor
        
        return np.clip(adjusted, 0.0, 10.0)
    
    @staticmethod
    def adjust_route_complexity(
        base_score: float,
        climate_vars: ClimateVariables,
        route_segments: Optional[List[Dict]] = None,
        context: Dict[str, Any] = None
    ) -> float:
        """Adjust route complexity based on climate variables"""
        context = context or {}
        
        # Climate volatility increases route complexity
        volatility_impact = (climate_vars.long_term_climate_volatility_index - 5.0) / 10.0
        
        # Extreme event probability impact
        tail_impact = climate_vars.climate_tail_event_probability * 0.5
        
        adjusted = base_score * (1.0 + volatility_impact + tail_impact)
        
        return np.clip(adjusted, 0.0, 10.0)
    
    @staticmethod
    def calculate_climate_volatility_boost(
        base_volatility: float,
        climate_vars: ClimateVariables
    ) -> float:
        """Boost volatility based on climate variables"""
        # Climate volatility multiplier
        volatility_mult = 1.0 + (climate_vars.long_term_climate_volatility_index - 5.0) / 20.0
        
        # Tail event probability boost
        tail_boost = climate_vars.climate_tail_event_probability * 0.3
        
        boosted = base_volatility * volatility_mult * (1.0 + tail_boost)
        
        return np.clip(boosted, 0.0, 1.0)


# ================================================================
# ESG CLIMATE RESILIENCE
# ================================================================

class ESGClimateResilience:
    """ESG-based climate resilience adjustments"""
    
    @staticmethod
    def apply_esg_climate_adjustments(
        base_score: float,
        layer_name: str,
        climate_vars: ClimateVariables
    ) -> float:
        """Apply ESG-based climate adjustments to risk layers"""
        
        # ESG resilience factor (higher ESG = lower risk)
        esg_factor = 1.0 - (climate_vars.ESG_score - 50.0) / 200.0
        
        # Climate resilience factor
        resilience_factor = 1.0 - (climate_vars.climate_resilience_score - 5.0) / 20.0
        
        # Green packaging bonus
        green_bonus = (climate_vars.green_packaging_score - 5.0) / 30.0
        
        # Layer-specific ESG weight
        layer_weights = {
            'cargo_sensitivity': 0.8,
            'packaging_quality': 1.5,  # Packaging highly ESG-sensitive
            'transport_reliability': 0.6,
            'port_risk': 0.7,
            'weather_exposure': 1.2,  # Weather highly climate-sensitive
            'route_complexity': 0.5
        }
        weight = layer_weights.get(layer_name.lower(), 1.0)
        
        adjusted = base_score * esg_factor * resilience_factor - (green_bonus * weight)
        
        return np.clip(adjusted, 0.0, 10.0)


# ================================================================
# CLIMATE MONTE CARLO EXTENSION
# ================================================================

class ClimateMonteCarloExtension:
    """Climate-enhanced Monte Carlo simulations"""
    
    @staticmethod
    def generate_climate_tail_shocks(
        n_samples: int,
        climate_vars: ClimateVariables,
        base_tail_prob: float = 0.05
    ) -> np.ndarray:
        """Generate climate-driven tail shock distribution"""
        
        # Combined tail probability
        combined_prob = base_tail_prob + climate_vars.climate_tail_event_probability * 0.5
        combined_prob = np.clip(combined_prob, 0.0, 0.15)
        
        # Generate shocks
        shocks = np.zeros(n_samples)
        
        # Identify tail event samples
        tail_mask = np.random.random(n_samples) < combined_prob
        
        if np.any(tail_mask):
            # Calculate shock magnitude based on climate variables
            base_magnitude = 2.0
            enso_mult = 1.0 + abs(climate_vars.ENSO_index) * 0.3
            typhoon_mult = 1.0 + climate_vars.seasonal_typhoon_frequency * 0.5
            volatility_mult = climate_vars.long_term_climate_volatility_index / 5.0
            
            magnitude = base_magnitude * enso_mult * typhoon_mult * volatility_mult
            
            # Generate gamma-distributed shocks
            shocks[tail_mask] = np.random.gamma(2.0, magnitude, size=np.sum(tail_mask))
        
        return shocks
    
    @staticmethod
    def build_climate_correlation_matrix(
        layer_names: List[str],
        climate_vars: ClimateVariables
    ) -> np.ndarray:
        """Build correlation matrix with climate-driven adjustments"""
        n = len(layer_names)
        base_corr = np.eye(n)
        
        # Base correlations
        correlations = {
            ('weather_exposure', 'port_risk'): 0.4,
            ('weather_exposure', 'transport_reliability'): -0.3,
            ('route_complexity', 'weather_exposure'): 0.45,
            ('transport_reliability', 'port_risk'): 0.35,
        }
        
        # Apply base correlations
        for i, name1 in enumerate(layer_names):
            for j, name2 in enumerate(layer_names):
                if i < j:
                    key = (name1, name2)
                    rev_key = (name2, name1)
                    if key in correlations:
                        base_corr[i, j] = base_corr[j, i] = correlations[key]
                    elif rev_key in correlations:
                        base_corr[i, j] = base_corr[j, i] = correlations[rev_key]
        
        # Climate-driven correlation boost
        chi = climate_vars.calculate_CHI()
        climate_factor = 1.0 + (chi - 5.0) / 20.0
        
        # Increase correlations for climate-sensitive pairs
        climate_sensitive_pairs = [
            ('weather_exposure', 'port_risk'),
            ('weather_exposure', 'transport_reliability'),
            ('route_complexity', 'weather_exposure')
        ]
        
        for name1, name2 in climate_sensitive_pairs:
            if name1 in layer_names and name2 in layer_names:
                i = layer_names.index(name1)
                j = layer_names.index(name2)
                if base_corr[i, j] != 0:
                    base_corr[i, j] = base_corr[j, i] = np.clip(
                        base_corr[i, j] * climate_factor, -1.0, 1.0
                    )
        
        # Ensure positive definiteness
        base_corr = (base_corr + base_corr.T) / 2
        eigenvalues = np.linalg.eigvals(base_corr)
        if np.any(eigenvalues <= 0):
            # Adjust to make positive definite
            min_eigenvalue = np.min(eigenvalues)
            base_corr += np.eye(n) * (abs(min_eigenvalue) + 0.01)
            base_corr = (base_corr + base_corr.T) / 2
        
        return base_corr
    
    @staticmethod
    def calculate_climate_var(
        risk_distribution: np.ndarray
    ) -> Dict[str, float]:
        """Calculate Climate-adjusted Value at Risk metrics"""
        if len(risk_distribution) == 0:
            return {
                'climate_var_95': 0.0,
                'climate_var_99': 0.0,
                'climate_cvar_95': 0.0,
                'climate_cvar_99': 0.0,
                'climate_tail_risk': 0.0,
                'climate_extreme_probability': 0.0,
                'climate_volatility': 0.0
            }
        
        # Standard VaR calculations
        var_95 = np.percentile(risk_distribution, 95)
        var_99 = np.percentile(risk_distribution, 99)
        
        # CVaR (Expected Shortfall)
        tail_95 = risk_distribution[risk_distribution >= var_95]
        tail_99 = risk_distribution[risk_distribution >= var_99]
        
        cvar_95 = np.mean(tail_95) if len(tail_95) > 0 else var_95
        cvar_99 = np.mean(tail_99) if len(tail_99) > 0 else var_99
        
        # Climate-specific metrics
        climate_risk_tail = risk_distribution[risk_distribution >= np.percentile(risk_distribution, 90)]
        climate_extreme_prob = np.mean(risk_distribution >= np.percentile(risk_distribution, 98))
        
        return {
            'climate_var_95': float(var_95),
            'climate_var_99': float(var_99),
            'climate_cvar_95': float(cvar_95),
            'climate_cvar_99': float(cvar_99),
            'climate_tail_risk': float(np.mean(climate_risk_tail)) if len(climate_risk_tail) > 0 else 0.0,
            'climate_extreme_probability': float(climate_extreme_prob),
            'climate_volatility': float(np.std(risk_distribution))
        }


# ================================================================
# CLIMATE AI ANALYSIS
# ================================================================

class ClimateAIAnalysis:
    """AI-powered climate narrative generation"""
    
    @staticmethod
    def generate_climate_vulnerability_summary(
        climate_vars: ClimateVariables,
        c_var_metrics: Dict[str, float]
    ) -> str:
        """Generate climate vulnerability analysis summary"""
        chi = climate_vars.calculate_CHI()
        
        if chi < 3.0:
            level = "LOW"
            summary = f"Climate Hazard Index (CHI): {chi:.2f}/10 — {level} climate risk exposure."
        elif chi < 6.0:
            level = "MODERATE"
            summary = f"Climate Hazard Index (CHI): {chi:.2f}/10 — {level} climate risk exposure. Monitor ENSO patterns and typhoon forecasts."
        else:
            level = "HIGH"
            summary = f"Climate Hazard Index (CHI): {chi:.2f}/10 — {level} climate risk exposure. Active climate risk mitigation recommended."
        
        return summary
    
    @staticmethod
    def generate_climate_tail_analysis(
        c_var_metrics: Dict[str, float],
        climate_vars: ClimateVariables
    ) -> str:
        """Generate climate tail risk analysis"""
        extreme_prob = c_var_metrics.get('climate_extreme_probability', 0.0) * 100
        
        if extreme_prob < 2.0:
            analysis = f"Climate Extreme Event Probability: {extreme_prob:.1f}% — Normal tail risk distribution."
        elif extreme_prob < 5.0:
            analysis = f"Climate Extreme Event Probability: {extreme_prob:.1f}% — Elevated tail risk. Consider climate stress testing."
        else:
            analysis = f"Climate Extreme Event Probability: {extreme_prob:.1f}% — High tail risk. Implement climate contingency plans."
        
        return analysis
    
    @staticmethod
    def generate_enso_seasonal_outlook(
        climate_vars: ClimateVariables
    ) -> str:
        """Generate ENSO seasonal outlook"""
        enso = climate_vars.ENSO_index
        
        if enso < -1.0:
            phase = "La Niña"
            impact = "Enhanced trade winds, potentially higher typhoon activity in Western Pacific."
        elif enso > 1.0:
            phase = "El Niño"
            impact = "Weaker trade winds, altered precipitation patterns, warmer SSTs."
        else:
            phase = "Neutral"
            impact = "Normal climate patterns expected."
        
        return f"ENSO Phase: {phase} (Index: {enso:.2f}). {impact}"
    
    @staticmethod
    def generate_esg_resilience_recommendations(
        climate_vars: ClimateVariables
    ) -> str:
        """Generate ESG resilience recommendations"""
        esg = climate_vars.ESG_score
        resilience = climate_vars.climate_resilience_score
        
        if esg >= 70 and resilience >= 7.0:
            rec = "Strong ESG and climate resilience positioning. Maintain current practices."
        elif esg >= 50 or resilience >= 5.0:
            rec = "Moderate ESG performance. Consider enhancing green packaging and climate adaptation measures."
        else:
            rec = "ESG and climate resilience improvement opportunities. Prioritize green logistics and climate risk management."
        
        return f"ESG Score: {esg:.1f}/100, Resilience: {resilience:.1f}/10. {rec}"
    
    @staticmethod
    def generate_climate_var_explanation(
        c_var_metrics: Dict[str, float],
        financial_chi_impact: float
    ) -> str:
        """Generate Climate-VaR explanation"""
        var_95 = c_var_metrics.get('climate_var_95', 0.0)
        cvar_95 = c_var_metrics.get('climate_cvar_95', 0.0)
        
        impact_pct = financial_chi_impact * 100
        
        explanation = (
            f"Climate-Adjusted VaR (95%): {var_95:.2f}, "
            f"CVaR (95%): {cvar_95:.2f}. "
            f"Estimated climate impact on financial risk: {impact_pct:.1f}%."
        )
        
        return explanation

