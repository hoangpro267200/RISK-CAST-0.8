"""
RiskCast V22 - Risk Driver Tree Engine
=======================================
Hierarchical risk factor analysis with root cause inference

Author: RiskCast AI Team
Version: 22.0
Module: #2 - Risk Driver Tree Engine
License: Proprietary
"""

from typing import Dict, List, Tuple
from collections import defaultdict


class RiskDriverTreeEngineV22:
    """
    Risk Driver Tree Engine that builds hierarchical risk factor trees
    showing contribution of each layer to category-level and overall risk.
    
    Structure:
    Level 1: Categories (Transport, Cargo, Commercial, Compliance, External)
    Level 2: Risk layers within each category
    Level 3: Root causes inferred from scoring patterns
    
    This engine uses pure logic-based inference without ML models.
    """
    
    # Import layer configuration from V21 scoring engine
    # This ensures consistency with risk scoring
    def __init__(self):
        """Initialize with V21 risk layer configuration"""
        # We'll import the RISK_LAYERS dynamically to avoid circular dependency
        try:
            from .risk_scoring_engine import RiskScoringEngineV21
        except ImportError:
            from risk_scoring_engine import RiskScoringEngineV21
        
        self.RISK_LAYERS = RiskScoringEngineV21.RISK_LAYERS
    
    def build_driver_tree(self, layer_scores: Dict) -> Dict:
        """
        Build hierarchical risk driver tree
        
        Args:
            layer_scores: Dictionary of individual layer scores (0-100)
        
        Returns:
            Hierarchical tree structure:
            {
                "transport": {
                    "score": 55.2,
                    "severity": "medium",
                    "drivers": [
                        {
                            "layer": "carrier_performance",
                            "layer_display_name": "Carrier Performance",
                            "score": 72.0,
                            "severity": "critical",
                            "weight": 0.12,
                            "contribution": 8.64,
                            "root_causes": ["Unreliable carrier schedule", ...]
                        },
                        ...
                    ]
                },
                ...
            }
        """
        
        # Step 1: Categorize layers by their risk category
        categorized = self._categorize_layers(layer_scores)
        
        # Step 2: Build tree structure
        driver_tree = {}
        
        for category_key, layer_list in categorized.items():
            # Calculate category-level score
            category_score = self._calculate_category_score(layer_list, layer_scores)
            
            # Build drivers for this category
            drivers = []
            for layer_name in layer_list:
                score = layer_scores.get(layer_name, 0)
                layer_def = self.RISK_LAYERS.get(layer_name, {})
                weight = layer_def.get('weight', 0)
                
                # Calculate this layer's contribution to overall risk
                contribution = score * weight
                
                # Infer root causes
                root_causes = self._infer_root_causes(layer_name, score)
                
                # Get human-readable layer name
                layer_display_name = self._format_layer_name(layer_name)
                
                driver = {
                    'layer': layer_name,
                    'layer_display_name': layer_display_name,
                    'score': round(score, 2),
                    'severity': self._score_to_severity(score),
                    'weight': weight,
                    'contribution': round(contribution, 2),
                    'root_causes': root_causes,
                    'description': layer_def.get('description', '')
                }
                
                drivers.append(driver)
            
            # Sort drivers by score (highest first)
            drivers.sort(key=lambda x: x['score'], reverse=True)
            
            # Build category node
            driver_tree[category_key] = {
                'category_display_name': self._format_category_name(category_key),
                'score': round(category_score, 2),
                'severity': self._score_to_severity(category_score),
                'drivers': drivers,
                'driver_count': len(drivers),
                'high_risk_count': sum(1 for d in drivers if d['score'] > 60)
            }
        
        return driver_tree
    
    def _categorize_layers(self, layer_scores: Dict) -> Dict[str, List[str]]:
        """
        Group layers by their risk category
        
        Args:
            layer_scores: Dictionary of layer scores
        
        Returns:
            Dictionary mapping category to list of layer names
            {
                'transport': ['mode_reliability', 'carrier_performance', ...],
                'cargo': ['cargo_sensitivity', ...],
                ...
            }
        """
        
        categorized = defaultdict(list)
        
        for layer_name in layer_scores.keys():
            if layer_name in self.RISK_LAYERS:
                layer_def = self.RISK_LAYERS[layer_name]
                category = layer_def['category'].value  # Get enum value
                categorized[category].append(layer_name)
        
        return dict(categorized)
    
    def _calculate_category_score(self, 
                                  layers: List[str], 
                                  layer_scores: Dict) -> float:
        """
        Calculate weighted average score for a category
        
        Args:
            layers: List of layer names in this category
            layer_scores: Dictionary of all layer scores
        
        Returns:
            Weighted average score (0-100)
        """
        
        if not layers:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for layer_name in layers:
            if layer_name in self.RISK_LAYERS and layer_name in layer_scores:
                score = layer_scores[layer_name]
                weight = self.RISK_LAYERS[layer_name]['weight']
                
                weighted_sum += score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def _infer_root_causes(self, layer_name: str, score: float) -> List[str]:
        """
        Logic-based inference of root causes for a risk layer
        
        Args:
            layer_name: Name of the risk layer
            score: Risk score for this layer (0-100)
        
        Returns:
            List of inferred root cause descriptions
        """
        
        # For low risk scores, minimal causes
        if score < 40:
            return ["Minor contributor to overall risk"]
        
        # Layer-specific root cause inference
        root_causes = []
        
        if layer_name == 'mode_reliability':
            if score > 70:
                root_causes = [
                    "Transport mode has inherent reliability issues",
                    "High risk of delays due to mode characteristics",
                    "Historical performance shows frequent disruptions"
                ]
            elif score > 50:
                root_causes = [
                    "Moderate reliability concerns with this transport mode",
                    "Some historical variability in performance"
                ]
            else:
                root_causes = ["Transport mode shows acceptable reliability"]
        
        elif layer_name == 'carrier_performance':
            if score > 70:
                root_causes = [
                    "Unreliable carrier schedule and track record",
                    "Low on-time performance history",
                    "Frequent service delays or cancellations"
                ]
            elif score > 50:
                root_causes = [
                    "Performance variability with this carrier",
                    "Possible port delays or operational issues",
                    "Inconsistent service quality"
                ]
            else:
                root_causes = ["Carrier shows adequate performance metrics"]
        
        elif layer_name == 'route_complexity':
            if score > 70:
                root_causes = [
                    "Extremely complex routing with multiple risk points",
                    "Long distance with many potential failure points",
                    "Limited alternative routing options"
                ]
            elif score > 50:
                root_causes = [
                    "Route has notable complexity",
                    "Multiple transit segments increase risk",
                    "Some challenging geographic areas"
                ]
            else:
                root_causes = ["Route is relatively straightforward"]
        
        elif layer_name == 'transit_time_variance':
            if score > 70:
                root_causes = [
                    "Highly unpredictable schedule",
                    "Extreme variance in transit times",
                    "Poor schedule reliability on this route"
                ]
            elif score > 50:
                root_causes = [
                    "Schedule shows some variability",
                    "Moderate uncertainty in delivery timing"
                ]
            else:
                root_causes = ["Schedule is predictable and reliable"]
        
        elif layer_name == 'cargo_sensitivity':
            if score > 70:
                root_causes = [
                    "Fragile or high-risk cargo type",
                    "Inadequate protective packaging for sensitivity level",
                    "Requires specialized handling not guaranteed",
                    "Temperature/environmental sensitivity concerns"
                ]
            elif score > 50:
                root_causes = [
                    "Cargo requires special handling precautions",
                    "Moderate sensitivity to handling conditions",
                    "Enhanced care needed during transit"
                ]
            else:
                root_causes = ["Cargo is robust and standard handling applies"]
        
        elif layer_name == 'packing_quality':
            if score > 70:
                root_causes = [
                    "Packaging inadequate for cargo type",
                    "High risk of damage due to poor protection",
                    "Non-standard or insufficient packing materials"
                ]
            elif score > 50:
                root_causes = [
                    "Packaging quality is questionable",
                    "May not withstand full transit conditions",
                    "Consider reinforcement"
                ]
            else:
                root_causes = ["Packaging is appropriate and protective"]
        
        elif layer_name == 'dg_compliance':
            if score > 70:
                root_causes = [
                    "High-risk dangerous goods classification",
                    "Severe compliance and safety requirements",
                    "Incomplete or missing DG documentation",
                    "Mode restrictions for this DG class"
                ]
            elif score > 50:
                root_causes = [
                    "Dangerous goods present requiring strict compliance",
                    "Special handling and documentation needed",
                    "Regulatory restrictions apply"
                ]
            else:
                root_causes = ["No dangerous goods or minor compliance needs"]
        
        elif layer_name == 'incoterm_risk':
            if score > 70:
                root_causes = [
                    "Incoterm places maximum liability on buyer/seller",
                    "Extensive responsibility and control challenges",
                    "High exposure to transit risks",
                    "Limited recourse in case of issues"
                ]
            elif score > 50:
                root_causes = [
                    "Incoterm places significant responsibility on you",
                    "Notable risk allocation concerns",
                    "Consider negotiating better terms"
                ]
            else:
                root_causes = ["Incoterm provides favorable risk allocation"]
        
        elif layer_name == 'seller_credibility':
            if score > 70:
                root_causes = [
                    "Poor seller credibility indicators",
                    "High fraud or default risk",
                    "Insufficient verification or documentation",
                    "Concerns about business legitimacy"
                ]
            elif score > 50:
                root_causes = [
                    "Seller credibility concerns exist",
                    "Limited verification available",
                    "Due diligence recommended"
                ]
            else:
                root_causes = ["Seller appears credible and established"]
        
        elif layer_name == 'buyer_credibility':
            if score > 70:
                root_causes = [
                    "Serious buyer credibility concerns",
                    "Payment default risk",
                    "Poor business indicators",
                    "Insufficient financial information"
                ]
            elif score > 50:
                root_causes = [
                    "Buyer credibility issues warrant verification",
                    "Limited business history",
                    "Payment security recommended"
                ]
            else:
                root_causes = ["Buyer appears reliable and creditworthy"]
        
        elif layer_name == 'insurance_adequacy':
            if score > 70:
                root_causes = [
                    "Severely inadequate insurance coverage",
                    "Major financial exposure in case of loss",
                    "Coverage far below cargo value",
                    "Wrong type of coverage for risk profile"
                ]
            elif score > 50:
                root_causes = [
                    "Insurance coverage is insufficient",
                    "Gap between coverage and cargo value",
                    "Consider upgrading to comprehensive coverage"
                ]
            else:
                root_causes = ["Insurance coverage is appropriate"]
        
        elif layer_name == 'documentation_complexity':
            if score > 70:
                root_causes = [
                    "Extremely complex documentation requirements",
                    "High risk of compliance failure or errors",
                    "Multiple jurisdictions with conflicting requirements",
                    "Specialized expertise required"
                ]
            elif score > 50:
                root_causes = [
                    "Complex documentation requirements",
                    "Increased delay and error risk",
                    "Professional assistance recommended"
                ]
            else:
                root_causes = ["Documentation requirements are straightforward"]
        
        elif layer_name == 'trade_compliance':
            if score > 70:
                root_causes = [
                    "Severe trade compliance risks",
                    "Potential sanctions violations",
                    "High-risk origin or destination country",
                    "Restricted goods or parties involved"
                ]
            elif score > 50:
                root_causes = [
                    "Significant trade restrictions present",
                    "Compliance screening required",
                    "Regulatory concerns exist"
                ]
            else:
                root_causes = ["Trade route is clear with minimal restrictions"]
        
        elif layer_name == 'port_congestion':
            if score > 70:
                root_causes = [
                    "Origin or destination port is severely congested",
                    "Major queueing and operational delays expected",
                    "Port infrastructure issues",
                    "High vessel wait times"
                ]
            elif score > 50:
                root_causes = [
                    "Significant port congestion likely",
                    "Some delays expected at loading/discharge",
                    "Port efficiency concerns"
                ]
            else:
                root_causes = ["Ports are operating efficiently"]
        
        elif layer_name == 'weather_climate':
            if score > 70:
                root_causes = [
                    "Severe weather threats during transit period",
                    "Seasonal storms or hurricanes likely",
                    "Weather-sensitive cargo at high risk",
                    "Climate-related disruptions expected"
                ]
            elif score > 50:
                root_causes = [
                    "Adverse weather conditions possible",
                    "Seasonal climate factors present",
                    "Weather monitoring recommended"
                ]
            else:
                root_causes = ["Weather conditions are favorable"]
        
        elif layer_name == 'market_volatility':
            if score > 70:
                root_causes = [
                    "Extreme market instability",
                    "Severe cost fluctuations expected",
                    "Capacity availability issues",
                    "Unpredictable pricing environment"
                ]
            elif score > 50:
                root_causes = [
                    "High market volatility affecting rates",
                    "Price and capacity uncertainty",
                    "Market conditions unstable"
                ]
            else:
                root_causes = ["Market conditions are stable"]
        
        else:
            # Generic fallback for unknown layers
            if score > 70:
                root_causes = ["Critical risk factor requiring immediate attention"]
            elif score > 50:
                root_causes = ["Elevated risk requiring mitigation measures"]
            else:
                root_causes = ["Manageable risk level"]
        
        return root_causes
    
    def _score_to_severity(self, score: float) -> str:
        """
        Convert numeric score to severity level
        
        Args:
            score: Risk score (0-100)
        
        Returns:
            Severity level: 'low', 'medium', 'high', or 'critical'
        """
        
        if score < 30:
            return 'low'
        elif score < 50:
            return 'medium'
        elif score < 70:
            return 'high'
        else:
            return 'critical'
    
    def _format_layer_name(self, layer_name: str) -> str:
        """
        Convert layer_name to human-readable format
        
        Args:
            layer_name: Technical layer name (e.g., 'carrier_performance')
        
        Returns:
            Human-readable name (e.g., 'Carrier Performance')
        """
        
        return ' '.join(word.capitalize() for word in layer_name.split('_'))
    
    def _format_category_name(self, category_key: str) -> str:
        """
        Convert category key to human-readable format
        
        Args:
            category_key: Technical category key (e.g., 'transport')
        
        Returns:
            Human-readable name (e.g., 'Transportation')
        """
        
        category_names = {
            'transport': 'Transportation',
            'cargo': 'Cargo Handling',
            'commercial': 'Commercial Terms',
            'compliance': 'Regulatory Compliance',
            'external': 'External Factors'
        }
        
        return category_names.get(category_key, category_key.capitalize())
    
    def get_tree_summary(self, driver_tree: Dict) -> Dict:
        """
        Generate summary statistics for the driver tree
        
        Args:
            driver_tree: Risk driver tree structure
        
        Returns:
            Summary statistics dictionary
        """
        
        summary = {
            'total_categories': len(driver_tree),
            'total_drivers': sum(cat['driver_count'] for cat in driver_tree.values()),
            'high_risk_drivers': sum(cat['high_risk_count'] for cat in driver_tree.values()),
            'riskiest_category': None,
            'safest_category': None,
            'categories_by_risk': []
        }
        
        # Sort categories by risk score
        sorted_categories = sorted(
            driver_tree.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        if sorted_categories:
            summary['riskiest_category'] = {
                'name': sorted_categories[0][1]['category_display_name'],
                'score': sorted_categories[0][1]['score']
            }
            summary['safest_category'] = {
                'name': sorted_categories[-1][1]['category_display_name'],
                'score': sorted_categories[-1][1]['score']
            }
            
            summary['categories_by_risk'] = [
                {
                    'name': cat[1]['category_display_name'],
                    'score': cat[1]['score'],
                    'severity': cat[1]['severity']
                }
                for cat in sorted_categories
            ]
        
        return summary






