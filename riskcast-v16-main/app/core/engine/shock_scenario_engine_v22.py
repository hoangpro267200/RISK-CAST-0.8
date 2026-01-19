"""
RiskCast V22 - Shock Scenario Engine (Macro + Disruption)
==========================================================
Stress testing engine for macro shocks and supply chain disruptions

Author: RiskCast AI Team
Version: 22.0
Phase: 2.6 - Shock Scenario Engine
License: Proprietary
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from copy import deepcopy


class ShockScenarioEngineV22:
    """
    Shock Scenario Engine that applies macro and disruption shocks to
    existing shipment risk profiles and recalculates adjusted impacts.
    
    Scenarios:
    - Macro: Fuel spikes, demand crashes, rate volatility
    - Disruption: Port strikes, conflicts, climate events, pandemics
    
    Uses existing V22 risk assessment as baseline and adjusts layer scores
    to model "what-if" scenarios without external dependencies.
    """
    
    def __init__(self):
        """Initialize shock scenario engine with default scenario library"""
        
        # Import here to avoid circular dependency
        try:
            from .risk_scoring_engine import RiskScoringEngineV21
        except ImportError:
            from risk_scoring_engine import RiskScoringEngineV21
        
        self.scoring_engine = RiskScoringEngineV21()
        
        # Define standard shock scenarios
        self.DEFAULT_SCENARIOS = [
            {
                "id": "fuel_spike_30",
                "name": "Fuel price surge +30%",
                "type": "macro",
                "category": "cost",
                "intensity": "moderate"
            },
            {
                "id": "demand_crash_25",
                "name": "Global demand drops -25%",
                "type": "macro",
                "category": "demand",
                "intensity": "moderate"
            },
            {
                "id": "port_strike_major",
                "name": "Major port labor strike",
                "type": "disruption",
                "category": "port",
                "intensity": "high"
            },
            {
                "id": "war_risk_corridor",
                "name": "Conflict escalation in trade route corridor",
                "type": "disruption",
                "category": "geo",
                "intensity": "high"
            },
            {
                "id": "climate_extreme_event",
                "name": "Extreme climate event on route",
                "type": "disruption",
                "category": "climate",
                "intensity": "high"
            },
            {
                "id": "pandemic_resurgence",
                "name": "Pandemic resurgence with restrictions",
                "type": "disruption",
                "category": "health",
                "intensity": "critical"
            }
        ]
    
    def list_scenarios(self) -> List[Dict]:
        """
        Return list of available shock scenarios
        
        Returns:
            List of scenario definitions with id, name, type, category, intensity
        """
        return deepcopy(self.DEFAULT_SCENARIOS)
    
    def run_scenarios(self,
                     input_data: Dict,
                     base_risk: Dict,
                     gfi_result: Optional[Dict] = None,
                     monte_carlo_result: Optional[Dict] = None) -> Dict:
        """
        Run shock scenarios and compute stress test results
        
        Args:
            input_data: Full shipment input data
            base_risk: Complete risk_assessment from V22
            gfi_result: Global Freight Index result (optional)
            monte_carlo_result: Monte Carlo simulation result (optional)
        
        Returns:
            Comprehensive shock scenario analysis
        """
        
        # Extract base case information
        base_layers = base_risk['layer_scores']
        base_overall = base_risk['overall_score']
        base_level = base_risk['risk_level']
        base_expected_loss = base_risk['financial_impact']['expected_loss_usd']
        
        # Run each scenario
        scenarios = []
        
        for scenario_def in self.DEFAULT_SCENARIOS:
            # Apply shock to layer scores
            new_layers = self._apply_scenario_to_layers(
                scenario_def,
                base_layers,
                input_data,
                gfi_result
            )
            
            # Recalculate overall score and risk level
            overall_score, risk_level, risk_grade = self._recalculate_overall_and_level(
                new_layers
            )
            
            # Estimate delay impact
            delay_metrics = self._estimate_delay_impact(
                scenario_def,
                new_layers,
                base_layers,
                input_data,
                monte_carlo_result
            )
            
            # Estimate financial impact
            expected_loss = self._estimate_financial_impact(
                overall_score,
                base_overall,
                base_expected_loss,
                input_data.get('cargo', {}).get('insurance_value', 100000)
            )
            
            # Build complete scenario result
            scenario_result = self._build_scenario_result(
                scenario_def,
                new_layers,
                base_layers,
                overall_score,
                risk_level,
                risk_grade,
                base_risk,
                delay_metrics,
                expected_loss
            )
            
            scenarios.append(scenario_result)
        
        # Build summary statistics
        summary = self._build_summary(scenarios, base_risk)
        
        return {
            'base_case': {
                'overall_score': float(base_overall),
                'risk_level': base_level,
                'risk_grade': base_risk.get('risk_grade', 'B'),
                'expected_loss_usd': float(base_expected_loss)
            },
            'scenarios': scenarios,
            'summary': summary,
            'scenario_count': len(scenarios)
        }
    
    def _apply_scenario_to_layers(self,
                                  scenario: Dict,
                                  base_layers: Dict[str, float],
                                  input_data: Dict,
                                  gfi_result: Optional[Dict]) -> Dict[str, float]:
        """
        Apply shock scenario to risk layer scores
        
        Returns:
            Adjusted layer scores (new dict)
        """
        
        # Start with copy of base layers
        new_layers = deepcopy(base_layers)
        
        scenario_id = scenario['id']
        cargo = input_data.get('cargo', {})
        transport = input_data.get('transport', {})
        
        # Scenario-specific adjustments
        if scenario_id == "fuel_spike_30":
            # Fuel price surge affects market and carrier operations
            new_layers['market_volatility'] = min(100, new_layers['market_volatility'] + 12)
            new_layers['carrier_performance'] = min(100, new_layers['carrier_performance'] + 5)
            
            # Amplify if GFI shows high pressure
            if gfi_result and gfi_result['pressure']['pressure_level'] in ['high', 'extreme']:
                new_layers['market_volatility'] = min(100, new_layers['market_volatility'] * 1.2)
        
        elif scenario_id == "demand_crash_25":
            # Demand crash reduces congestion but increases market uncertainty
            new_layers['market_volatility'] = min(100, new_layers['market_volatility'] + 8)
            new_layers['port_congestion'] = max(0, new_layers['port_congestion'] - 5)  # Less congestion
            new_layers['seller_credibility'] = min(100, new_layers['seller_credibility'] + 5)  # Seller stress
            new_layers['buyer_credibility'] = min(100, new_layers['buyer_credibility'] + 3)  # Buyer cancellations
        
        elif scenario_id == "port_strike_major":
            # Port strike severely impacts congestion and schedule
            new_layers['port_congestion'] = min(100, new_layers['port_congestion'] + 20)
            new_layers['transit_time_variance'] = min(100, new_layers['transit_time_variance'] + 10)
            new_layers['documentation_complexity'] = min(100, new_layers['documentation_complexity'] + 5)
            new_layers['carrier_performance'] = min(100, new_layers['carrier_performance'] + 8)
        
        elif scenario_id == "war_risk_corridor":
            # Geopolitical conflict affects compliance and insurance
            new_layers['trade_compliance'] = min(100, new_layers['trade_compliance'] + 15)
            new_layers['market_volatility'] = min(100, new_layers['market_volatility'] + 10)
            new_layers['route_complexity'] = min(100, new_layers['route_complexity'] + 12)
            
            # Insurance inadequacy if no war coverage
            insurance_coverage = cargo.get('insurance_coverage', '').lower()
            if insurance_coverage not in ['war_risks', 'all_risks']:
                new_layers['insurance_adequacy'] = min(100, new_layers['insurance_adequacy'] + 10)
        
        elif scenario_id == "climate_extreme_event":
            # Extreme weather event
            new_layers['weather_climate'] = min(100, new_layers['weather_climate'] + 20)
            new_layers['transit_time_variance'] = min(100, new_layers['transit_time_variance'] + 8)
            
            # Extra impact on temperature-sensitive cargo
            sensitivity = cargo.get('sensitivity', '').lower()
            if sensitivity in ['temperature', 'perishable']:
                new_layers['cargo_sensitivity'] = min(100, new_layers['cargo_sensitivity'] + 10)
        
        elif scenario_id == "pandemic_resurgence":
            # Pandemic with lockdowns and restrictions
            new_layers['port_congestion'] = min(100, new_layers['port_congestion'] + 15)
            new_layers['documentation_complexity'] = min(100, new_layers['documentation_complexity'] + 12)
            new_layers['transit_time_variance'] = min(100, new_layers['transit_time_variance'] + 15)
            new_layers['carrier_performance'] = min(100, new_layers['carrier_performance'] + 10)
            new_layers['trade_compliance'] = min(100, new_layers['trade_compliance'] + 8)
        
        # Ensure all values are in valid range
        for key in new_layers:
            new_layers[key] = float(np.clip(new_layers[key], 0, 100))
        
        return new_layers
    
    def _recalculate_overall_and_level(self, 
                                       new_layers: Dict[str, float]) -> Tuple[float, str, str]:
        """
        Recalculate overall score and risk level using V21/V22 weights
        
        Returns:
            (overall_score, risk_level, risk_grade)
        """
        
        # Use V21 weights and calculation logic
        overall_score = 0.0
        
        for layer_name, layer_def in self.scoring_engine.RISK_LAYERS.items():
            score = new_layers.get(layer_name, 50)
            weight = layer_def['weight']
            overall_score += score * weight
        
        # Determine risk level (same thresholds as V21)
        if overall_score < 30:
            risk_level = 'low'
        elif overall_score < 50:
            risk_level = 'medium'
        elif overall_score < 70:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        # Calculate risk grade
        risk_grade = self.scoring_engine._score_to_grade(overall_score)
        
        return float(overall_score), risk_level, risk_grade
    
    def _estimate_delay_impact(self,
                               scenario: Dict,
                               new_layers: Dict[str, float],
                               base_layers: Dict[str, float],
                               input_data: Dict,
                               monte_carlo_result: Optional[Dict]) -> Dict:
        """
        Estimate delay impact for scenario
        
        Returns:
            {'p50': float, 'p95': float} delay in days
        """
        
        # Option A: Use Monte Carlo if available
        if monte_carlo_result and 'eta_stats' in monte_carlo_result:
            # Scale MC delays based on layer changes
            base_p50 = monte_carlo_result['eta_stats']['p50']
            base_p95 = monte_carlo_result['eta_stats']['p95']
            
            # Calculate impact factor from key delay-related layers
            impact_factor = 1.0 + (
                (new_layers['port_congestion'] - base_layers['port_congestion']) / 100 * 0.6 +
                (new_layers['weather_climate'] - base_layers['weather_climate']) / 100 * 0.4 +
                (new_layers['documentation_complexity'] - base_layers['documentation_complexity']) / 100 * 0.3
            )
            
            p50_delay = base_p50 * impact_factor
            p95_delay = base_p95 * impact_factor * 1.1  # P95 amplifies more
        
        # Option B: Heuristic if Monte Carlo not available
        else:
            base_transit = input_data.get('transport', {}).get('transit_time', 14)
            
            # Calculate delay factor from risk layers
            delay_factor = (
                new_layers['port_congestion'] +
                new_layers['weather_climate'] +
                new_layers['transit_time_variance']
            ) / 300  # Normalize
            
            p50_delay = base_transit * delay_factor * 0.7
            p95_delay = base_transit * delay_factor * 1.8
        
        return {
            'p50': float(max(0, p50_delay)),
            'p95': float(max(0, p95_delay))
        }
    
    def _estimate_financial_impact(self,
                                   scenario_overall_score: float,
                                   base_overall_score: float,
                                   base_expected_loss: float,
                                   cargo_value: float) -> float:
        """
        Estimate expected financial loss under scenario
        
        Uses proportional scaling based on overall score change
        """
        
        if base_overall_score == 0:
            ratio = 1.5
        else:
            ratio = scenario_overall_score / base_overall_score
        
        # Scale expected loss
        scenario_loss = base_expected_loss * ratio
        
        # Cap at cargo value
        scenario_loss = min(scenario_loss, cargo_value * 0.5)  # Max 50% of value
        
        return float(round(scenario_loss, 2))
    
    def _build_scenario_result(self,
                              scenario: Dict,
                              new_layers: Dict[str, float],
                              base_layers: Dict[str, float],
                              overall_score: float,
                              risk_level: str,
                              risk_grade: str,
                              base_risk: Dict,
                              delay_metrics: Dict,
                              expected_loss_usd: float) -> Dict:
        """
        Build complete scenario result object
        """
        
        # Calculate deltas
        delta_vs_base = overall_score - base_risk['overall_score']
        delta_loss = expected_loss_usd - base_risk['financial_impact']['expected_loss_usd']
        
        # Identify changed layers
        layer_changes = {}
        for layer_name in new_layers:
            delta = new_layers[layer_name] - base_layers.get(layer_name, 0)
            if abs(delta) >= 1.0:  # Only show meaningful changes
                layer_changes[layer_name] = f"{delta:+.0f} pts"
        
        # Get top risk drivers in scenario
        sorted_layers = sorted(new_layers.items(), key=lambda x: x[1], reverse=True)
        top_drivers = [
            {
                'layer': layer_name,
                'score': float(score)
            }
            for layer_name, score in sorted_layers[:3]
        ]
        
        # Generate scenario-specific description and recommendations
        assumptions_desc, recommendations = self._generate_scenario_narrative(
            scenario,
            layer_changes,
            delta_vs_base,
            risk_level
        )
        
        return {
            'id': scenario['id'],
            'name': scenario['name'],
            'type': scenario['type'],
            'category': scenario['category'],
            'intensity': scenario['intensity'],
            'assumptions': {
                'description': assumptions_desc,
                'changes': layer_changes
            },
            'impact': {
                'overall_score': float(round(overall_score, 2)),
                'risk_level': risk_level,
                'risk_grade': risk_grade,
                'delta_vs_base': float(round(delta_vs_base, 2)),
                'expected_loss_usd': float(round(expected_loss_usd, 2)),
                'delta_expected_loss_usd': float(round(delta_loss, 2)),
                'delay_days_p50': float(round(delay_metrics['p50'], 2)),
                'delay_days_p95': float(round(delay_metrics['p95'], 2))
            },
            'drivers': {
                'top_risk_layers': top_drivers
            },
            'recommendation': recommendations
        }
    
    def _generate_scenario_narrative(self,
                                    scenario: Dict,
                                    layer_changes: Dict,
                                    delta_score: float,
                                    risk_level: str) -> Tuple[str, Dict]:
        """
        Generate human-readable narrative for scenario
        
        Returns:
            (description, recommendations)
        """
        
        scenario_id = scenario['id']
        
        # Scenario-specific narratives
        narratives = {
            'fuel_spike_30': {
                'description': 'Global bunker fuel costs surge by 30%, causing carriers to tighten capacity and raise rates. Market volatility increases significantly.',
                'summary': f'Fuel shock pushes shipment into {risk_level.upper()} risk zone with +{delta_score:.0f} point increase.',
                'actions': [
                    'Secure short-term contracts with fuel adjustment caps.',
                    'Shift to more fuel-efficient carriers or routes.',
                    'Re-evaluate shipment timing to avoid peak fuel periods.',
                    'Consider intermodal options to reduce fuel dependency.'
                ]
            },
            'demand_crash_25': {
                'description': 'Global shipping demand collapses by 25% due to economic downturn. Rates soften but market uncertainty spikes.',
                'summary': f'Demand crash creates {risk_level.upper()} risk environment with mixed impacts.',
                'actions': [
                    'Leverage spot market for better rates if capacity allows.',
                    'Monitor seller/buyer financial stability closely.',
                    'Avoid long-term commitments until market stabilizes.',
                    'Negotiate volume-flexible contracts with downside protection.'
                ]
            },
            'port_strike_major': {
                'description': 'Major labor strike at origin or destination port causing severe congestion, delays, and operational chaos.',
                'summary': f'Port strike escalates risk to {risk_level.upper()} with major delays expected.',
                'actions': [
                    'Divert to alternative ports immediately if possible.',
                    'Book priority berthing services at destination.',
                    'Engage customs broker for expedited clearance.',
                    'Communicate delays proactively to all stakeholders.',
                    'Consider air freight for critical/time-sensitive cargo.'
                ]
            },
            'war_risk_corridor': {
                'description': 'Armed conflict escalates in trade route corridor. Increased insurance costs, sanctions risk, and route diversions.',
                'summary': f'Geopolitical crisis pushes risk to {risk_level.upper()} with compliance and safety concerns.',
                'actions': [
                    'Upgrade insurance to include war risks and strikes coverage.',
                    'Conduct enhanced sanctions screening immediately.',
                    'Identify alternative routing options away from conflict zone.',
                    'Monitor geopolitical developments and prepare contingencies.',
                    'Consider delaying shipment until situation stabilizes.'
                ]
            },
            'climate_extreme_event': {
                'description': 'Extreme climate event (hurricane, typhoon, flood) impacts route during transit period. Severe weather delays expected.',
                'summary': f'Climate emergency elevates risk to {risk_level.upper()} with weather-related delays.',
                'actions': [
                    'Delay departure until after extreme weather event passes.',
                    'Upgrade cargo insurance to cover weather-related damage.',
                    'Request specialized weather routing from carrier.',
                    'Monitor meteorological forecasts continuously.',
                    'Prepare contingency plans for extended delays.'
                ]
            },
            'pandemic_resurgence': {
                'description': 'New pandemic wave with port lockdowns, capacity restrictions, and heightened health protocols causing widespread disruption.',
                'summary': f'Pandemic scenario creates {risk_level.upper()} risk with systemic disruption.',
                'actions': [
                    'Secure capacity commitments from multiple carriers immediately.',
                    'Build inventory buffers to reduce shipping frequency.',
                    'Establish backup suppliers in lower-risk regions.',
                    'Monitor health protocols at all ports of call.',
                    'Implement robust tracking and visibility systems.',
                    'Consider reshoring or nearshoring critical supplies.'
                ]
            }
        }
        
        narrative = narratives.get(scenario_id, {
            'description': f'{scenario["name"]} scenario applied to shipment.',
            'summary': f'Scenario pushes risk to {risk_level.upper()}.',
            'actions': ['Monitor situation closely.', 'Implement mitigation measures.']
        })
        
        return narrative['description'], {
            'summary': narrative['summary'],
            'actions': narrative['actions'][:4]  # Top 4 actions
        }
    
    def _build_summary(self, scenarios: List[Dict], base_risk: Dict) -> Dict:
        """
        Build summary statistics across all scenarios
        """
        
        # Find worst case
        worst_case = max(scenarios, key=lambda s: s['impact']['overall_score'])
        
        # Count scenarios by risk level
        risk_distribution = {
            'low': 0,
            'medium': 0,
            'high': 0,
            'critical': 0
        }
        
        for scenario in scenarios:
            level = scenario['impact']['risk_level']
            if level in risk_distribution:
                risk_distribution[level] += 1
        
        # Find max delay
        max_delay_p95 = max(s['impact']['delay_days_p95'] for s in scenarios)
        
        # Average impact
        avg_delta = np.mean([s['impact']['delta_vs_base'] for s in scenarios])
        
        return {
            'worst_case_scenario_id': worst_case['id'],
            'worst_case_scenario_name': worst_case['name'],
            'worst_case_overall_score': worst_case['impact']['overall_score'],
            'worst_case_expected_loss_usd': worst_case['impact']['expected_loss_usd'],
            'max_delay_p95_days': float(round(max_delay_p95, 2)),
            'scenario_risk_distribution': risk_distribution,
            'average_score_delta': float(round(avg_delta, 2)),
            'scenarios_worse_than_base': sum(1 for s in scenarios if s['impact']['delta_vs_base'] > 0),
            'resilience_score': self._calculate_resilience_score(scenarios, base_risk)
        }
    
    def _calculate_resilience_score(self, scenarios: List[Dict], base_risk: Dict) -> float:
        """
        Calculate shipment resilience score (0-100, higher = more resilient)
        
        Based on:
        - How much scores increase under shocks
        - How many scenarios stay in same/better risk level
        """
        
        base_level = base_risk['risk_level']
        
        # Count scenarios that don't worsen risk level
        risk_level_order = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        base_level_index = risk_level_order.get(base_level, 1)
        
        stable_scenarios = sum(
            1 for s in scenarios
            if risk_level_order.get(s['impact']['risk_level'], 1) <= base_level_index
        )
        
        # Calculate average score increase
        avg_increase = np.mean([s['impact']['delta_vs_base'] for s in scenarios])
        
        # Resilience formula
        stability_component = (stable_scenarios / len(scenarios)) * 50
        resistance_component = max(0, 50 - avg_increase * 2)  # Lower increase = higher resilience
        
        resilience = stability_component + resistance_component
        
        return float(round(min(100, max(0, resilience)), 2))
