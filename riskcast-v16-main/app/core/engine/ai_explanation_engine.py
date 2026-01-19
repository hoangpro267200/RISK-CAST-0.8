"""
RiskCast V22 - AI Explanation Engine
=====================================
Generates human-readable explanations for risk scores and drivers

Author: RiskCast AI Team
Version: 22.0
Module: #1 - AI Explanation Engine
License: Proprietary
"""

from typing import Dict, List, Tuple


class AIExplanationEngineV22:
    """
    AI Explanation Engine that generates natural language explanations
    for risk scores, helping users understand "why" behind the numbers.
    
    This engine uses rule-based logic to provide clear, actionable insights
    without requiring external ML models or LLM APIs.
    """
    
    # Layer name to human-readable mapping
    LAYER_NAMES = {
        'mode_reliability': 'Transport Mode Reliability',
        'carrier_performance': 'Carrier Performance',
        'route_complexity': 'Route Complexity',
        'transit_time_variance': 'Transit Time Variance',
        'cargo_sensitivity': 'Cargo Sensitivity',
        'packing_quality': 'Packing Quality',
        'dg_compliance': 'Dangerous Goods Compliance',
        'incoterm_risk': 'Incoterm Risk',
        'seller_credibility': 'Seller Credibility',
        'buyer_credibility': 'Buyer Credibility',
        'insurance_adequacy': 'Insurance Adequacy',
        'documentation_complexity': 'Documentation Complexity',
        'trade_compliance': 'Trade Compliance',
        'port_congestion': 'Port Congestion',
        'weather_climate': 'Weather & Climate',
        'market_volatility': 'Market Volatility'
    }
    
    # Category name to human-readable mapping
    CATEGORY_NAMES = {
        'transport': 'Transportation',
        'cargo': 'Cargo Handling',
        'commercial': 'Commercial Terms',
        'compliance': 'Regulatory Compliance',
        'external': 'External Factors'
    }
    
    def generate_explanation(self, 
                            layer_scores: Dict, 
                            category_scores: Dict,
                            overall_score: float,
                            risk_level: str) -> Dict:
        """
        Main entry point: Generate comprehensive explanation for risk assessment
        
        Args:
            layer_scores: Dictionary of individual risk layer scores (0-100)
            category_scores: Dictionary of category-level scores (0-100)
            overall_score: Overall risk score (0-100)
            risk_level: Risk level string ('low', 'medium', 'high', 'critical')
        
        Returns:
            Dictionary containing:
            - overview: Overall risk summary
            - drivers: Top 3 risk drivers with explanations
            - layer_explanations: Explanation for each risk layer
            - category_explanations: Explanation for each category
            - recommendations: Quick action items
        """
        
        # Generate overall explanation
        overview = self._explain_overall(overall_score, risk_level)
        
        # Extract and explain key risk drivers
        key_drivers = self._extract_key_drivers(layer_scores)
        drivers = []
        for layer_name, score in key_drivers:
            drivers.append({
                'layer': self.LAYER_NAMES.get(layer_name, layer_name),
                'score': round(score, 2),
                'explanation': self._explain_layer(layer_name, score),
                'impact': self._assess_impact(score)
            })
        
        # Generate layer-by-layer explanations
        layer_explanations = {}
        for layer_name, score in layer_scores.items():
            layer_explanations[layer_name] = {
                'display_name': self.LAYER_NAMES.get(layer_name, layer_name),
                'score': round(score, 2),
                'explanation': self._explain_layer(layer_name, score),
                'severity': self._score_to_severity(score)
            }
        
        # Generate category explanations
        category_explanations = {}
        for category_name, score in category_scores.items():
            category_explanations[category_name] = {
                'display_name': self.CATEGORY_NAMES.get(category_name, category_name),
                'score': round(score, 2),
                'explanation': self._explain_category(category_name, score),
                'severity': self._score_to_severity(score)
            }
        
        # Generate quick recommendations
        recommendations = self._generate_quick_recommendations(key_drivers, risk_level)
        
        return {
            'overview': overview,
            'drivers': drivers,
            'layer_explanations': layer_explanations,
            'category_explanations': category_explanations,
            'recommendations': recommendations,
            'insights': self._generate_insights(layer_scores, category_scores, overall_score)
        }
    
    def _explain_overall(self, overall_score: float, risk_level: str) -> str:
        """
        Generate overall risk summary (2-3 sentences)
        
        Args:
            overall_score: Overall risk score (0-100)
            risk_level: Risk level string
        
        Returns:
            Human-readable summary text
        """
        
        risk_level_upper = risk_level.upper()
        
        if overall_score < 30:
            return (
                f"This shipment has a {risk_level_upper} risk profile with a score of {overall_score:.1f}/100. "
                f"The risk factors are well-controlled and within acceptable ranges. "
                f"Standard operating procedures should be sufficient for successful delivery."
            )
        elif overall_score < 50:
            return (
                f"This shipment presents {risk_level_upper} risk with a score of {overall_score:.1f}/100. "
                f"While manageable, several factors require attention to ensure smooth execution. "
                f"Consider implementing recommended mitigation measures to reduce potential disruptions."
            )
        elif overall_score < 70:
            return (
                f"This shipment carries {risk_level_upper} risk at {overall_score:.1f}/100. "
                f"Multiple significant risk factors have been identified that could impact delivery. "
                f"Immediate action is recommended to address key vulnerabilities and prevent potential losses."
            )
        else:
            return (
                f"This shipment faces CRITICAL risk with a score of {overall_score:.1f}/100. "
                f"Severe risk factors are present that pose substantial threats to successful delivery. "
                f"Urgent intervention and comprehensive mitigation strategies are essential before proceeding."
            )
    
    def _explain_layer(self, layer_name: str, score: float) -> str:
        """
        Generate explanation for individual risk layer
        
        Args:
            layer_name: Name of the risk layer
            score: Risk score for this layer (0-100)
        
        Returns:
            Short explanation text (1-2 lines)
        """
        
        # Layer-specific explanations based on score ranges
        explanations = {
            'mode_reliability': {
                'low': 'Transport mode shows excellent reliability with minimal inherent risks.',
                'moderate': 'Transport mode has acceptable reliability but some inherent variability.',
                'elevated': 'Transport mode presents notable reliability concerns requiring attention.',
                'critical': 'Transport mode shows poor reliability posing significant delivery risks.'
            },
            'carrier_performance': {
                'low': 'Carrier demonstrates strong on-time performance and service quality.',
                'moderate': 'Carrier performance is acceptable but with occasional delays.',
                'elevated': 'Carrier has concerning performance history with frequent issues.',
                'critical': 'Carrier shows poor track record with high probability of delays or failures.'
            },
            'route_complexity': {
                'low': 'Route is straightforward with minimal complexity and well-established.',
                'moderate': 'Route has moderate complexity with some challenging segments.',
                'elevated': 'Route is complex with multiple risk points and longer distances.',
                'critical': 'Route involves extremely complex logistics with high failure potential.'
            },
            'transit_time_variance': {
                'low': 'Schedule is highly reliable with minimal variance expected.',
                'moderate': 'Some schedule variability expected but generally predictable.',
                'elevated': 'Significant schedule uncertainty with potential for major delays.',
                'critical': 'Schedule is highly unpredictable with extreme delay risks.'
            },
            'cargo_sensitivity': {
                'low': 'Cargo is robust and can withstand standard handling conditions.',
                'moderate': 'Cargo requires standard care during handling and transport.',
                'elevated': 'Cargo is sensitive and requires special handling procedures.',
                'critical': 'Cargo is extremely fragile or valuable requiring maximum protection.'
            },
            'packing_quality': {
                'low': 'Packaging is robust and provides excellent protection.',
                'moderate': 'Packaging is adequate for standard transport conditions.',
                'elevated': 'Packaging quality is questionable for the cargo type.',
                'critical': 'Packaging is insufficient and poses high damage risk.'
            },
            'dg_compliance': {
                'low': 'No dangerous goods concerns, standard cargo handling applies.',
                'moderate': 'Minor compliance requirements for specialized cargo.',
                'elevated': 'Dangerous goods present requiring strict compliance measures.',
                'critical': 'High-risk dangerous goods with severe compliance and safety concerns.'
            },
            'incoterm_risk': {
                'low': 'Incoterm provides clear responsibility allocation with minimal risk exposure.',
                'moderate': 'Incoterm allocation is standard with acceptable risk distribution.',
                'elevated': 'Incoterm places significant responsibility and risk on you.',
                'critical': 'Incoterm exposes you to maximum liability and control challenges.'
            },
            'seller_credibility': {
                'low': 'Seller is well-established with strong credibility indicators.',
                'moderate': 'Seller appears legitimate but with limited verification.',
                'elevated': 'Seller credibility concerns exist requiring due diligence.',
                'critical': 'Seller shows poor credibility with high fraud or default risk.'
            },
            'buyer_credibility': {
                'low': 'Buyer is credible with strong business indicators.',
                'moderate': 'Buyer appears reliable but with limited information.',
                'elevated': 'Buyer credibility issues warrant additional verification.',
                'critical': 'Buyer presents serious credibility concerns and payment risks.'
            },
            'insurance_adequacy': {
                'low': 'Insurance coverage is comprehensive and appropriate for cargo value.',
                'moderate': 'Insurance coverage is adequate but could be enhanced.',
                'elevated': 'Insurance coverage is insufficient for the cargo value and risks.',
                'critical': 'Severely inadequate insurance creating major financial exposure.'
            },
            'documentation_complexity': {
                'low': 'Documentation requirements are straightforward and routine.',
                'moderate': 'Standard documentation with manageable complexity.',
                'elevated': 'Complex documentation requirements increase delay and error risk.',
                'critical': 'Extremely complex documentation posing high compliance failure risk.'
            },
            'trade_compliance': {
                'low': 'Trade route is clear with minimal regulatory restrictions.',
                'moderate': 'Standard compliance requirements with no major restrictions.',
                'elevated': 'Significant trade restrictions or sanctions concerns present.',
                'critical': 'Severe trade compliance risks including potential sanctions violations.'
            },
            'port_congestion': {
                'low': 'Ports are efficient with minimal congestion expected.',
                'moderate': 'Normal port operations with some congestion possible.',
                'elevated': 'Significant port congestion likely causing delays.',
                'critical': 'Severe port congestion creating major delay and cost risks.'
            },
            'weather_climate': {
                'low': 'Weather conditions are favorable for the planned transit period.',
                'moderate': 'Normal seasonal weather with manageable risks.',
                'elevated': 'Adverse weather conditions likely during transit.',
                'critical': 'Severe weather threats posing major disruption risks.'
            },
            'market_volatility': {
                'low': 'Market conditions are stable with predictable pricing.',
                'moderate': 'Normal market fluctuations expected.',
                'elevated': 'High market volatility affecting rates and capacity.',
                'critical': 'Extreme market instability creating severe cost and availability risks.'
            }
        }
        
        # Determine severity level
        severity = self._score_to_severity(score)
        
        # Get explanation or use generic
        if layer_name in explanations:
            return explanations[layer_name].get(severity, 
                f"Risk score of {score:.1f} indicates {severity} concern level.")
        else:
            return f"This factor scores {score:.1f}/100, indicating {severity} risk level."
    
    def _explain_category(self, category_name: str, score: float) -> str:
        """
        Generate explanation for risk category
        
        Args:
            category_name: Name of the risk category
            score: Risk score for this category (0-100)
        
        Returns:
            Category-level explanation text
        """
        
        category_explanations = {
            'transport': {
                'low': 'Transportation arrangements are solid with reliable carriers and routes.',
                'moderate': 'Transportation setup is acceptable but has some vulnerabilities to monitor.',
                'elevated': 'Transportation factors present significant risks requiring mitigation.',
                'critical': 'Transportation arrangements are highly problematic and need immediate revision.'
            },
            'cargo': {
                'low': 'Cargo characteristics and handling requirements are well-managed.',
                'moderate': 'Cargo presents standard risks that are manageable with proper care.',
                'elevated': 'Cargo characteristics create substantial handling and protection challenges.',
                'critical': 'Cargo is extremely vulnerable with severe damage or loss risks.'
            },
            'commercial': {
                'low': 'Commercial terms and party relationships are favorable and well-structured.',
                'moderate': 'Commercial arrangements are standard with acceptable risk allocation.',
                'elevated': 'Commercial terms expose you to significant financial or liability risks.',
                'critical': 'Commercial structure is highly unfavorable with severe exposure.'
            },
            'compliance': {
                'low': 'Regulatory compliance requirements are clear and easily manageable.',
                'moderate': 'Standard compliance obligations with no unusual complications.',
                'elevated': 'Complex compliance landscape with substantial violation risks.',
                'critical': 'Severe compliance challenges with high penalty or seizure risks.'
            },
            'external': {
                'low': 'External conditions are favorable with minimal disruption threats.',
                'moderate': 'Normal external factors with manageable variability.',
                'elevated': 'External environment presents notable disruption risks.',
                'critical': 'External threats are severe and could derail the shipment.'
            }
        }
        
        severity = self._score_to_severity(score)
        
        if category_name in category_explanations:
            return category_explanations[category_name].get(severity,
                f"{self.CATEGORY_NAMES.get(category_name, category_name)} shows {severity} risk at {score:.1f}/100.")
        else:
            return f"This category scores {score:.1f}/100, indicating {severity} overall risk level."
    
    def _extract_key_drivers(self, layer_scores: Dict) -> List[Tuple[str, float]]:
        """
        Extract top 3 highest-risk layers
        
        Args:
            layer_scores: Dictionary of layer scores
        
        Returns:
            List of (layer_name, score) tuples for top 3 drivers
        """
        
        # Sort layers by score (highest first) and take top 3
        sorted_layers = sorted(layer_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_layers[:3]
    
    def _score_to_severity(self, score: float) -> str:
        """
        Convert numeric score to severity level
        
        Args:
            score: Risk score (0-100)
        
        Returns:
            Severity level string
        """
        
        if score < 30:
            return 'low'
        elif score < 50:
            return 'moderate'
        elif score < 70:
            return 'elevated'
        else:
            return 'critical'
    
    def _assess_impact(self, score: float) -> str:
        """
        Assess the impact level based on score
        
        Args:
            score: Risk score (0-100)
        
        Returns:
            Impact description
        """
        
        if score < 30:
            return 'Minimal Impact'
        elif score < 50:
            return 'Moderate Impact'
        elif score < 70:
            return 'High Impact'
        else:
            return 'Critical Impact'
    
    def _generate_quick_recommendations(self, 
                                       key_drivers: List[Tuple[str, float]], 
                                       risk_level: str) -> List[str]:
        """
        Generate quick action recommendations based on top drivers
        
        Args:
            key_drivers: List of top risk drivers
            risk_level: Overall risk level
        
        Returns:
            List of actionable recommendation strings
        """
        
        recommendations = []
        
        # Add urgency based on risk level
        if risk_level in ['high', 'critical']:
            recommendations.append(
                "⚠️ URGENT: Immediate action required to address critical risk factors."
            )
        
        # Add driver-specific recommendations
        driver_actions = {
            'carrier_performance': 'Consider upgrading to a premium carrier with better reliability.',
            'port_congestion': 'Book priority berthing or consider alternative ports to avoid delays.',
            'cargo_sensitivity': 'Upgrade packaging and request special handling throughout transit.',
            'insurance_adequacy': 'Increase insurance coverage to All Risks to protect cargo value.',
            'weather_climate': 'Monitor weather forecasts and prepare contingency routing plans.',
            'trade_compliance': 'Conduct thorough sanctions screening and engage compliance experts.',
            'documentation_complexity': 'Hire experienced customs broker to handle documentation.',
            'route_complexity': 'Simplify route or add tracking checkpoints for complex segments.',
            'incoterm_risk': 'Review Incoterm choice and consider shifting more risk to carrier.',
            'seller_credibility': 'Conduct enhanced due diligence on seller before payment.',
            'buyer_credibility': 'Request payment guarantees or letter of credit for security.',
            'packing_quality': 'Inspect and reinforce packaging before shipment departure.',
            'dg_compliance': 'Engage dangerous goods specialist for compliance certification.',
            'market_volatility': 'Lock in rates with contract to avoid market fluctuations.',
            'transit_time_variance': 'Select guaranteed delivery service with penalty clauses.',
            'mode_reliability': 'Consider alternative transport mode for better reliability.'
        }
        
        # Add top 3 driver recommendations
        for layer_name, score in key_drivers:
            if score > 50:  # Only recommend for elevated risks
                action = driver_actions.get(layer_name, 
                    f"Address {self.LAYER_NAMES.get(layer_name, layer_name)} risk factors.")
                recommendations.append(f"• {action}")
        
        # Cap at 5 recommendations
        return recommendations[:5]
    
    def _generate_insights(self, 
                          layer_scores: Dict, 
                          category_scores: Dict,
                          overall_score: float) -> Dict:
        """
        Generate analytical insights about the risk profile
        
        Args:
            layer_scores: Individual layer scores
            category_scores: Category scores
            overall_score: Overall risk score
        
        Returns:
            Dictionary of insights
        """
        
        insights = {
            'strongest_area': None,
            'weakest_area': None,
            'risk_distribution': None,
            'attention_required': []
        }
        
        # Find strongest and weakest categories
        if category_scores:
            sorted_categories = sorted(category_scores.items(), key=lambda x: x[1])
            insights['strongest_area'] = {
                'category': self.CATEGORY_NAMES.get(sorted_categories[0][0], sorted_categories[0][0]),
                'score': round(sorted_categories[0][1], 2),
                'comment': 'This area is well-managed with low risk exposure.'
            }
            insights['weakest_area'] = {
                'category': self.CATEGORY_NAMES.get(sorted_categories[-1][0], sorted_categories[-1][0]),
                'score': round(sorted_categories[-1][1], 2),
                'comment': 'This area needs the most attention and improvement.'
            }
        
        # Analyze risk distribution
        high_risk_count = sum(1 for score in layer_scores.values() if score > 60)
        moderate_risk_count = sum(1 for score in layer_scores.values() if 40 <= score <= 60)
        low_risk_count = sum(1 for score in layer_scores.values() if score < 40)
        
        if high_risk_count > 5:
            insights['risk_distribution'] = 'Risk is widespread across multiple factors requiring comprehensive mitigation.'
        elif high_risk_count > 2:
            insights['risk_distribution'] = 'Risk is concentrated in several key areas that should be prioritized.'
        elif high_risk_count > 0:
            insights['risk_distribution'] = 'Risk is limited to specific factors that can be targeted effectively.'
        else:
            insights['risk_distribution'] = 'Risk is well-distributed and generally under control.'
        
        # Areas requiring attention
        for layer_name, score in layer_scores.items():
            if score > 70:
                insights['attention_required'].append({
                    'layer': self.LAYER_NAMES.get(layer_name, layer_name),
                    'score': round(score, 2),
                    'urgency': 'HIGH'
                })
        
        return insights






