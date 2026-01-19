"""
RISKCAST Scenario Engine
=========================
Enable "What-If" analysis for risk mitigation planning.

Features:
- Compare baseline against multiple scenarios
- Cost-benefit analysis for mitigations
- Recommendation engine for optimal strategy
- Batch scenario processing

Author: RISKCAST Team
Version: 2.0
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from copy import deepcopy
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScenarioConfig:
    """Configuration for a single scenario."""
    name: str
    description: str
    changes: Dict[str, Any]
    estimated_cost: float = 0.0
    implementation_time_hours: float = 0.0
    feasibility: str = "high"  # high, medium, low


@dataclass
class ScenarioResult:
    """Result of evaluating a single scenario."""
    name: str
    description: str
    changes: Dict[str, Any]
    risk_data: Dict
    risk_score: float
    risk_score_delta: float
    expected_loss_delta: float
    improvement_pct: float
    cost: float
    roi: float  # (Risk reduction value) / cost
    is_recommended: bool
    benefits: List[str]


@dataclass
class ScenarioComparisonResult:
    """Complete scenario comparison result."""
    baseline: Dict
    scenarios: List[ScenarioResult]
    recommendation: Dict
    summary: Dict
    timestamp: datetime


class ScenarioEngine:
    """
    Enable "What-If" analysis for risk mitigation planning.
    
    Capabilities:
    1. Compare baseline against alternatives
    2. Evaluate cost-benefit of each scenario
    3. Rank scenarios by risk-adjusted ROI
    4. Generate optimal strategy recommendation
    """
    
    # Preset scenario templates
    PRESET_SCENARIOS = {
        "alternative_carrier": {
            "name": "Alternative Carrier",
            "description": "Switch to a higher-rated carrier",
            "changes": {"carrier_rating": 8.5, "carrier": "premium"},
            "estimated_cost": 500,
            "implementation_time_hours": 2
        },
        "route_via_singapore": {
            "name": "Route via Singapore",
            "description": "Transit through Singapore instead of direct",
            "changes": {"route": "via-singapore", "transit_time": 32},
            "estimated_cost": 1200,
            "implementation_time_hours": 4
        },
        "air_freight": {
            "name": "Air Freight",
            "description": "Ship via air instead of ocean",
            "changes": {"transport_mode": "air", "transit_time": 5},
            "estimated_cost": 15000,
            "implementation_time_hours": 24
        },
        "enhanced_packaging": {
            "name": "Enhanced Packaging",
            "description": "Upgrade to premium packaging",
            "changes": {"packaging_quality": 9.0},
            "estimated_cost": 800,
            "implementation_time_hours": 8
        },
        "premium_insurance": {
            "name": "Premium Insurance",
            "description": "Add comprehensive insurance coverage",
            "changes": {"insurance_coverage": "full"},
            "estimated_cost": 2500,
            "implementation_time_hours": 1
        },
        "delay_shipment": {
            "name": "Delay Shipment",
            "description": "Delay departure to avoid weather window",
            "changes": {"weather_risk": 3.0, "departure_delay_days": 7},
            "estimated_cost": 200,
            "implementation_time_hours": 0
        },
        "split_shipment": {
            "name": "Split Shipment",
            "description": "Split cargo into two smaller shipments",
            "changes": {"cargo_value": 0.5, "split_shipment": True},
            "estimated_cost": 3000,
            "implementation_time_hours": 12
        }
    }
    
    def __init__(self, risk_calculator: Optional[Callable] = None):
        """
        Initialize scenario engine.
        
        Args:
            risk_calculator: Function that takes shipment dict and returns risk result.
                           If None, uses default engine.
        """
        if risk_calculator is None:
            from app.core.engine.risk_engine_v16 import calculate_enterprise_risk
            self.calculate_risk = calculate_enterprise_risk
        else:
            self.calculate_risk = risk_calculator
    
    def compare_scenarios(
        self,
        baseline: Dict,
        scenarios: List[Dict],
        include_presets: bool = False
    ) -> ScenarioComparisonResult:
        """
        Compare baseline shipment against alternative scenarios.
        
        Args:
            baseline: Base shipment configuration
            scenarios: List of scenario configurations
            include_presets: Whether to include preset scenarios
            
        Returns:
            ScenarioComparisonResult with ranked scenarios
        """
        logger.info(f"Comparing {len(scenarios)} scenarios against baseline")
        
        # Calculate baseline risk
        baseline_risk = self._calculate_risk_safe(baseline)
        baseline_score = self._extract_score(baseline_risk)
        baseline_loss = baseline_risk.get('expected_loss', 0)
        
        baseline_result = {
            'description': 'Current plan',
            'config': baseline,
            'risk_data': baseline_risk,
            'risk_score': baseline_score
        }
        
        # Add preset scenarios if requested
        all_scenarios = list(scenarios)
        if include_presets:
            for preset_key, preset_config in self.PRESET_SCENARIOS.items():
                if not any(s.get('name') == preset_config['name'] for s in scenarios):
                    all_scenarios.append(preset_config)
        
        # Evaluate each scenario
        scenario_results = []
        
        for scenario in all_scenarios:
            try:
                result = self._evaluate_scenario(
                    baseline=baseline,
                    baseline_score=baseline_score,
                    baseline_loss=baseline_loss,
                    scenario=scenario
                )
                scenario_results.append(result)
            except Exception as e:
                logger.warning(f"Failed to evaluate scenario {scenario.get('name')}: {e}")
        
        # Sort by improvement (descending)
        scenario_results.sort(key=lambda x: x.improvement_pct, reverse=True)
        
        # Mark recommended scenarios
        self._mark_recommendations(scenario_results)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            baseline_score, scenario_results
        )
        
        # Generate summary
        summary = self._generate_summary(baseline_score, scenario_results)
        
        return ScenarioComparisonResult(
            baseline=baseline_result,
            scenarios=scenario_results,
            recommendation=recommendation,
            summary=summary,
            timestamp=datetime.utcnow()
        )
    
    def _calculate_risk_safe(self, shipment: Dict) -> Dict:
        """Calculate risk with error handling."""
        try:
            return self.calculate_risk(shipment)
        except Exception as e:
            logger.error(f"Risk calculation failed: {e}")
            return {'overall_risk': 5.0, 'expected_loss': 0}
    
    def _extract_score(self, risk_data: Dict) -> float:
        """Extract risk score from result."""
        if 'risk_score' in risk_data:
            return float(risk_data['risk_score'])
        elif 'overall_risk' in risk_data:
            return float(risk_data['overall_risk']) * 10
        return 50.0
    
    def _evaluate_scenario(
        self,
        baseline: Dict,
        baseline_score: float,
        baseline_loss: float,
        scenario: Dict
    ) -> ScenarioResult:
        """Evaluate a single scenario."""
        # Apply scenario changes to baseline
        scenario_config = deepcopy(baseline)
        changes = scenario.get('changes', {})
        
        for key, value in changes.items():
            if key == 'cargo_value' and isinstance(value, float) and value < 1:
                # Multiplicative change (e.g., 0.5 = 50% of original)
                scenario_config['cargo_value'] = baseline.get('cargo_value', 100000) * value
            else:
                scenario_config[key] = value
        
        # Calculate scenario risk
        risk_data = self._calculate_risk_safe(scenario_config)
        scenario_score = self._extract_score(risk_data)
        scenario_loss = risk_data.get('expected_loss', 0)
        
        # Calculate deltas
        risk_score_delta = scenario_score - baseline_score
        expected_loss_delta = scenario_loss - baseline_loss
        
        # Improvement percentage
        improvement_pct = ((baseline_score - scenario_score) / max(baseline_score, 1)) * 100
        
        # Cost and ROI
        cost = scenario.get('estimated_cost', 0)
        
        # ROI: (Loss reduction) / cost
        loss_reduction = max(0, baseline_loss - scenario_loss)
        roi = loss_reduction / max(cost, 1) if cost > 0 else float('inf') if loss_reduction > 0 else 0
        
        # Benefits
        benefits = self._summarize_benefits(
            risk_score_delta, expected_loss_delta, improvement_pct
        )
        
        return ScenarioResult(
            name=scenario.get('name', 'Unnamed Scenario'),
            description=scenario.get('description', ''),
            changes=changes,
            risk_data=risk_data,
            risk_score=scenario_score,
            risk_score_delta=risk_score_delta,
            expected_loss_delta=expected_loss_delta,
            improvement_pct=improvement_pct,
            cost=cost,
            roi=roi,
            is_recommended=False,  # Will be set later
            benefits=benefits
        )
    
    def _summarize_benefits(
        self,
        risk_delta: float,
        loss_delta: float,
        improvement: float
    ) -> List[str]:
        """Summarize benefits of a scenario."""
        benefits = []
        
        if risk_delta < -10:
            benefits.append(f"Reduces risk score by {abs(risk_delta):.1f} points")
        elif risk_delta < 0:
            benefits.append(f"Slightly reduces risk ({abs(risk_delta):.1f} points)")
        
        if loss_delta < -1000:
            benefits.append(f"Reduces expected loss by ${abs(loss_delta):,.0f}")
        elif loss_delta < 0:
            benefits.append(f"Minor loss reduction (${abs(loss_delta):,.0f})")
        
        if improvement > 20:
            benefits.append(f"Significant improvement ({improvement:.1f}%)")
        
        if not benefits:
            if risk_delta > 0:
                benefits.append("No improvement (risk increases)")
            else:
                benefits.append("Minimal impact")
        
        return benefits
    
    def _mark_recommendations(self, results: List[ScenarioResult]):
        """Mark which scenarios are recommended."""
        for result in results:
            # Recommend if:
            # 1. Improves risk by at least 5%
            # 2. ROI > 1 (or free)
            # 3. Not the worst option
            
            is_improvement = result.improvement_pct > 5
            is_cost_effective = result.roi > 1 or result.cost == 0
            is_not_worst = result.risk_score_delta < 0
            
            result.is_recommended = is_improvement and is_cost_effective and is_not_worst
    
    def _generate_recommendation(
        self,
        baseline_score: float,
        results: List[ScenarioResult]
    ) -> Dict:
        """Generate overall recommendation."""
        recommended = [r for r in results if r.is_recommended]
        
        if not recommended:
            return {
                'recommended_scenario': 'Baseline (no change)',
                'rationale': 'No cost-effective improvements identified',
                'key_benefits': [],
                'estimated_savings': 0,
                'implementation_priority': 'none'
            }
        
        # Best scenario by improvement
        best = recommended[0]
        
        return {
            'recommended_scenario': best.name,
            'rationale': f"Reduces risk by {best.improvement_pct:.1f}% with ROI of {best.roi:.2f}x",
            'key_benefits': best.benefits,
            'estimated_savings': max(0, -best.expected_loss_delta),
            'estimated_cost': best.cost,
            'implementation_priority': 'high' if best.improvement_pct > 15 else 'medium'
        }
    
    def _generate_summary(
        self,
        baseline_score: float,
        results: List[ScenarioResult]
    ) -> Dict:
        """Generate summary statistics."""
        improving = [r for r in results if r.risk_score_delta < 0]
        worsening = [r for r in results if r.risk_score_delta > 0]
        
        best = min(results, key=lambda x: x.risk_score) if results else None
        worst = max(results, key=lambda x: x.risk_score) if results else None
        
        return {
            'total_scenarios_evaluated': len(results),
            'scenarios_improving_risk': len(improving),
            'scenarios_worsening_risk': len(worsening),
            'best_case_score': best.risk_score if best else baseline_score,
            'worst_case_score': worst.risk_score if worst else baseline_score,
            'baseline_score': baseline_score,
            'max_possible_improvement': (baseline_score - best.risk_score) if best else 0,
            'recommended_count': sum(1 for r in results if r.is_recommended)
        }
    
    def get_preset_scenarios(self) -> Dict[str, Dict]:
        """Get available preset scenarios."""
        return deepcopy(self.PRESET_SCENARIOS)
    
    def to_dict(self, result: ScenarioComparisonResult) -> Dict:
        """Convert result to dictionary for API response."""
        return {
            'baseline': result.baseline,
            'scenarios': [
                {
                    'name': s.name,
                    'description': s.description,
                    'changes': s.changes,
                    'risk_score': s.risk_score,
                    'risk_score_delta': s.risk_score_delta,
                    'expected_loss_delta': s.expected_loss_delta,
                    'improvement_pct': s.improvement_pct,
                    'cost': s.cost,
                    'roi': s.roi,
                    'is_recommended': s.is_recommended,
                    'benefits': s.benefits
                }
                for s in result.scenarios
            ],
            'recommendation': result.recommendation,
            'summary': result.summary,
            'timestamp': result.timestamp.isoformat()
        }


# Convenience function for API
def compare_shipment_scenarios(
    baseline: Dict,
    scenarios: List[Dict],
    include_presets: bool = False
) -> Dict:
    """
    Compare shipment scenarios.
    
    Args:
        baseline: Base shipment configuration
        scenarios: List of scenario configurations
        include_presets: Whether to include preset scenarios
        
    Returns:
        Comparison result as dictionary
    """
    engine = ScenarioEngine()
    result = engine.compare_scenarios(baseline, scenarios, include_presets)
    return engine.to_dict(result)


def get_available_presets() -> Dict[str, Dict]:
    """Get available preset scenario templates."""
    engine = ScenarioEngine()
    return engine.get_preset_scenarios()
