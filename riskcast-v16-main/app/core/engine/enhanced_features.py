"""
RiskCast V22 - Enhanced Algorithmic Features Module
====================================================
Advanced AI-like features for optimization and prediction

Author: RiskCast AI Team
Version: 22.0
License: Proprietary
"""

from typing import Dict, List


class EnhancedAlgorithmicFeaturesV21:
    """
    Advanced AI-like features for optimization and prediction
    """
    
    @staticmethod
    def dynamic_weight_adjustment(layer_scores: Dict, 
                                 priority: str,
                                 cargo_value: float) -> Dict:
        """
        Dynamically adjust layer weights based on context
        """
        # Import here to avoid circular dependency
        try:
            from .risk_scoring_engine import RiskScoringEngineV21
        except ImportError:
            from risk_scoring_engine import RiskScoringEngineV21
        
        adjusted_weights = {}
        for layer_name, layer_def in RiskScoringEngineV21.RISK_LAYERS.items():
            adjusted_weights[layer_name] = layer_def.copy()
        
        if cargo_value > 500000:
            adjusted_weights['insurance_adequacy']['weight'] *= 1.5
            adjusted_weights['cargo_sensitivity']['weight'] *= 1.3
        
        if priority == 'fastest':
            adjusted_weights['transit_time_variance']['weight'] *= 1.4
            adjusted_weights['carrier_performance']['weight'] *= 1.3
        elif priority == 'cheapest':
            adjusted_weights['market_volatility']['weight'] *= 1.2
        
        total_weight = sum(l['weight'] for l in adjusted_weights.values())
        for layer in adjusted_weights.values():
            layer['weight'] /= total_weight
        
        return adjusted_weights
    
    @staticmethod
    def predictive_delay_model(transport: Dict, 
                               layer_scores: Dict) -> Dict:
        """
        ML-style delay prediction model
        """
        
        base_transit = transport.get('transit_time', 14)
        
        delay_factors = {
            'carrier_performance': layer_scores.get('carrier_performance', 50) / 100 * 0.15,
            'port_congestion': layer_scores.get('port_congestion', 40) / 100 * 0.20,
            'weather_climate': layer_scores.get('weather_climate', 35) / 100 * 0.10,
            'documentation': layer_scores.get('documentation_complexity', 40) / 100 * 0.08
        }
        
        total_delay_factor = sum(delay_factors.values())
        
        expected_delay_days = base_transit * total_delay_factor
        
        delay_probability = min(0.95, total_delay_factor * 1.5)
        
        return {
            'expected_transit_days': round(base_transit + expected_delay_days, 1),
            'delay_probability': round(delay_probability * 100, 1),
            'p50_delay': round(expected_delay_days * 0.7, 1),
            'p95_delay': round(expected_delay_days * 2.0, 1),
            'delay_breakdown': {k: round(v * base_transit, 2) for k, v in delay_factors.items()}
        }
    
    @staticmethod
    def route_optimization_suggestions(transport: Dict,
                                      layer_scores: Dict) -> List[Dict]:
        """
        Suggest alternative routes/modes
        """
        
        suggestions = []
        current_mode = transport.get('mode', 'sea_freight')
        
        if current_mode == 'sea_freight':
            if layer_scores.get('transit_time_variance', 0) > 60:
                suggestions.append({
                    'alternative': 'air_freight',
                    'benefit': 'Reduce transit time by 70%',
                    'trade_off': 'Cost increase ~4-5x',
                    'risk_reduction': 25
                })
        
        if layer_scores.get('carrier_performance', 0) > 65:
            suggestions.append({
                'alternative': 'premium_carrier',
                'benefit': 'Improve on-time rate to 95%+',
                'trade_off': 'Cost increase ~15-20%',
                'risk_reduction': 15
            })
        
        if layer_scores.get('port_congestion', 0) > 65:
            suggestions.append({
                'alternative': 'alternative_port',
                'benefit': 'Avoid congested ports',
                'trade_off': 'Possible longer inland transport',
                'risk_reduction': 12
            })
        
        return suggestions
    
    @staticmethod
    def insurance_optimization(cargo: Dict, 
                              layer_scores: Dict,
                              overall_risk: float) -> Dict:
        """
        Intelligent insurance recommendations
        """
        
        cargo_value = cargo.get('insurance_value', 0)
        current_coverage = cargo.get('insurance_coverage', 'icc_c').lower()
        
        recommendations = {
            'current_coverage': current_coverage,
            'current_premium_estimate': cargo_value * 0.003,
            'recommendations': []
        }
        
        if overall_risk > 60:
            if current_coverage != 'icc_a':
                recommendations['recommendations'].append({
                    'upgrade_to': 'icc_a',
                    'reason': 'High risk warrants all-risks coverage',
                    'additional_premium': cargo_value * 0.002,
                    'benefit': 'Covers all losses except inherent vice'
                })
        
        if layer_scores.get('cargo_sensitivity', 0) > 60:
            recommendations['recommendations'].append({
                'add_on': 'damage_survey_clause',
                'reason': 'Sensitive cargo needs assessment',
                'additional_premium': 150,
                'benefit': 'Independent surveyor for claims'
            })
        
        if layer_scores.get('trade_compliance', 0) > 50:
            recommendations['recommendations'].append({
                'add_on': 'war_strikes_clause',
                'reason': 'Elevated geopolitical risk',
                'additional_premium': cargo_value * 0.001,
                'benefit': 'Protection against war/strikes'
            })
        
        return recommendations

