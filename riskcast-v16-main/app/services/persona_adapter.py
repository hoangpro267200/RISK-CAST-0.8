"""
RISKCAST Multi-Persona Adapter
===============================
Adapt risk output based on user persona for optimal decision-making.

Personas:
- EXECUTIVE: 3-5 KPIs, high-level, actionable
- ANALYST: Full breakdown, methodology, comparisons
- OPERATIONS: Actionable mitigation steps, timelines
- INSURANCE: Underwriting data, actuarial metrics, loss scenarios

Author: RISKCAST Team
Version: 2.0
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserPersona(Enum):
    """User persona types."""
    EXECUTIVE = "executive"
    ANALYST = "analyst"
    OPERATIONS = "operations"
    INSURANCE = "insurance"


@dataclass
class ExecutiveSummary:
    """Executive-level risk summary."""
    overall_risk: float
    risk_level: str
    expected_impact: str
    recommendation: str
    confidence: float
    key_drivers: List[Dict]
    action_items: List[Dict]


@dataclass
class InsuranceUnderwriting:
    """Insurance underwriting data."""
    risk_class: str
    suggested_premium_adjustment: Dict
    var_95: float
    cvar_95: float
    maximum_probable_loss: float
    loss_frequency: float
    loss_severity: float
    coverage_gaps: List[str]
    deductible_recommendation: float
    exclusions: List[str]


class PersonaAdapter:
    """
    Adapt risk output based on user persona.
    
    Each persona gets tailored information:
    - Executive: Quick decision support
    - Analyst: Deep technical details
    - Operations: Action-oriented mitigation
    - Insurance: Underwriting and actuarial data
    """
    
    @staticmethod
    def adapt(risk_data: Dict, persona: UserPersona) -> Dict:
        """
        Adapt risk data to specified persona.
        
        Args:
            risk_data: Full risk calculation result
            persona: Target user persona
            
        Returns:
            Persona-adapted response
        """
        adapters = {
            UserPersona.EXECUTIVE: PersonaAdapter.format_for_executive,
            UserPersona.ANALYST: PersonaAdapter.format_for_analyst,
            UserPersona.OPERATIONS: PersonaAdapter.format_for_operations,
            UserPersona.INSURANCE: PersonaAdapter.format_for_insurance,
        }
        
        adapter = adapters.get(persona, PersonaAdapter.format_for_executive)
        return adapter(risk_data)
    
    @staticmethod
    def format_for_executive(risk_data: Dict) -> Dict:
        """
        Executive view: 3-5 KPIs max, high-level, actionable.
        
        Focus on:
        - Overall risk score and level
        - Expected financial impact
        - Clear recommendation
        - Top 3 risk drivers
        - Maximum 3 action items
        """
        risk_score = risk_data.get('risk_score', risk_data.get('overall_risk', 0) * 10)
        expected_loss = risk_data.get('expected_loss', 0)
        
        return {
            "persona": "executive",
            "summary": {
                "overall_risk": round(risk_score, 1),
                "risk_level": PersonaAdapter._get_risk_level(risk_score),
                "expected_impact": f"${expected_loss:,.0f}",
                "recommendation": PersonaAdapter._get_executive_recommendation(risk_score),
                "confidence": risk_data.get('confidence', 0.85),
                "assessment_quality": PersonaAdapter._get_quality_grade(risk_data)
            },
            "key_drivers": PersonaAdapter._get_top_risk_drivers(risk_data, top_n=3),
            "comparison_to_baseline": PersonaAdapter._compare_to_baseline(risk_data),
            "action_items": PersonaAdapter._generate_executive_actions(risk_data, max_actions=3),
            "visual_indicator": PersonaAdapter._get_risk_indicator(risk_score)
        }
    
    @staticmethod
    def format_for_analyst(risk_data: Dict) -> Dict:
        """
        Analyst view: Full breakdown, all factors, methodology.
        
        Includes:
        - Executive summary
        - Complete risk factor breakdown
        - FAHP weights and TOPSIS rankings
        - Monte Carlo statistics
        - Sensitivity analysis
        - Uncertainty quantification
        - Comparable shipments
        """
        executive_summary = PersonaAdapter.format_for_executive(risk_data)['summary']
        
        return {
            "persona": "analyst",
            "executive_summary": executive_summary,
            "detailed_breakdown": {
                "risk_factors": risk_data.get('risk_factors', {}),
                "layer_scores": risk_data.get('layers', []),
                "fahp_weights": risk_data.get('fahp_weights', {}),
                "topsis_ranking": risk_data.get('topsis_result', {}),
                "monte_carlo_stats": risk_data.get('monte_carlo_results', {})
            },
            "methodology": {
                "engine_version": risk_data.get('engine_version', 'v2.0'),
                "model_components": ["FAHP", "TOPSIS", "Monte Carlo"],
                "calibration_date": risk_data.get('calibration_date', 'N/A'),
                "validation_metrics": risk_data.get('validation_metrics', {})
            },
            "sensitivity_analysis": PersonaAdapter._get_sensitivity_summary(risk_data),
            "uncertainty_analysis": risk_data.get('uncertainty', {}),
            "data_quality": {
                "completeness": risk_data.get('data_completeness', 0.8),
                "provenance": risk_data.get('input_provenance', {}),
                "fraud_signals": risk_data.get('fraud_analysis', {})
            },
            "scenario_analysis": PersonaAdapter._generate_analyst_scenarios(risk_data),
            "comparable_shipments": PersonaAdapter._find_similar_shipments(risk_data)
        }
    
    @staticmethod
    def format_for_operations(risk_data: Dict) -> Dict:
        """
        Operations view: Actionable mitigation steps, timelines.
        
        Focused on:
        - Clear risk alert
        - Step-by-step mitigation plan
        - Timeline impact
        - Carrier recommendations
        - Monitoring checkpoints
        """
        risk_score = risk_data.get('risk_score', risk_data.get('overall_risk', 0) * 10)
        
        return {
            "persona": "operations",
            "risk_alert": {
                "level": PersonaAdapter._get_risk_level(risk_score),
                "score": round(risk_score, 1),
                "requires_immediate_action": risk_score > 70,
                "requires_review": risk_score > 50,
                "alert_color": PersonaAdapter._get_alert_color(risk_score)
            },
            "mitigation_steps": PersonaAdapter._generate_mitigation_plan(risk_data),
            "timeline_impact": {
                "expected_delay_days": risk_data.get('expected_delay_days', 0),
                "delay_probability": risk_data.get('delay_probability', 0),
                "p90_delay": risk_data.get('monte_carlo_results', {}).get('p90_delay', 0),
                "critical_checkpoints": PersonaAdapter._identify_checkpoints(risk_data)
            },
            "carrier_recommendations": PersonaAdapter._suggest_carrier_alternatives(risk_data),
            "route_alternatives": PersonaAdapter._suggest_route_alternatives(risk_data),
            "monitoring_plan": PersonaAdapter._create_monitoring_plan(risk_data),
            "escalation_contacts": PersonaAdapter._get_escalation_matrix(risk_score)
        }
    
    @staticmethod
    def format_for_insurance(risk_data: Dict) -> Dict:
        """
        Insurance view: Underwriting data, actuarial metrics, loss scenarios.
        
        Includes:
        - Risk classification
        - Premium adjustment recommendation
        - Loss distribution (VaR, CVaR, MPL)
        - Actuarial metrics
        - Policy recommendations
        - Regulatory flags
        """
        risk_score = risk_data.get('risk_score', risk_data.get('overall_risk', 0) * 10)
        cargo_value = risk_data.get('cargo_value', 100000)
        
        mc_results = risk_data.get('monte_carlo_results', {})
        
        return {
            "persona": "insurance",
            "underwriting_summary": {
                "risk_class": PersonaAdapter._determine_risk_class(risk_score),
                "risk_score": round(risk_score, 2),
                "risk_grade": PersonaAdapter._get_risk_grade(risk_score),
                "suggested_premium_adjustment": PersonaAdapter._calculate_premium_adjustment(
                    risk_score, cargo_value
                ),
                "acceptability": PersonaAdapter._determine_acceptability(risk_score)
            },
            "loss_metrics": {
                "expected_loss": risk_data.get('expected_loss', 0),
                "var_95": mc_results.get('var_95', risk_data.get('var_95', 0)),
                "cvar_95": mc_results.get('cvar_95', risk_data.get('cvar_95', 0)),
                "var_99": mc_results.get('var_99', 0),
                "maximum_probable_loss": mc_results.get('max_loss', cargo_value * 0.3),
                "loss_distribution": mc_results.get('loss_histogram', [])
            },
            "actuarial_data": {
                "loss_frequency": PersonaAdapter._estimate_loss_frequency(risk_score),
                "loss_severity": PersonaAdapter._estimate_loss_severity(risk_data),
                "combined_ratio_impact": PersonaAdapter._estimate_combined_ratio_impact(risk_score),
                "burning_cost": PersonaAdapter._calculate_burning_cost(risk_data)
            },
            "policy_recommendations": {
                "coverage_type": PersonaAdapter._recommend_coverage_type(risk_data),
                "coverage_gaps": PersonaAdapter._identify_coverage_gaps(risk_data),
                "deductible_recommendation": PersonaAdapter._suggest_deductible(risk_score, cargo_value),
                "exclusions": PersonaAdapter._suggest_exclusions(risk_data),
                "conditions": PersonaAdapter._suggest_conditions(risk_data)
            },
            "regulatory_flags": PersonaAdapter._check_regulatory_requirements(risk_data),
            "reinsurance_implications": PersonaAdapter._assess_reinsurance_needs(risk_score, cargo_value)
        }
    
    # ========================
    # Helper Methods
    # ========================
    
    @staticmethod
    def _get_risk_level(score: float) -> str:
        """Map score to risk level."""
        if score < 25:
            return "low"
        elif score < 50:
            return "medium"
        elif score < 75:
            return "high"
        else:
            return "critical"
    
    @staticmethod
    def _get_alert_color(score: float) -> str:
        """Get alert color for UI."""
        if score < 25:
            return "#22c55e"  # Green
        elif score < 50:
            return "#eab308"  # Yellow
        elif score < 75:
            return "#f97316"  # Orange
        else:
            return "#ef4444"  # Red
    
    @staticmethod
    def _get_risk_indicator(score: float) -> Dict:
        """Get visual risk indicator for dashboards."""
        return {
            "value": round(score, 1),
            "max": 100,
            "color": PersonaAdapter._get_alert_color(score),
            "level": PersonaAdapter._get_risk_level(score),
            "icon": "⚠️" if score > 50 else "✓" if score < 30 else "⚡"
        }
    
    @staticmethod
    def _get_quality_grade(risk_data: Dict) -> str:
        """Get data quality grade."""
        completeness = risk_data.get('data_completeness', 0.7)
        if completeness >= 0.9:
            return "A"
        elif completeness >= 0.75:
            return "B"
        elif completeness >= 0.6:
            return "C"
        else:
            return "D"
    
    @staticmethod
    def _get_executive_recommendation(score: float) -> str:
        """Generate executive-level recommendation."""
        if score < 25:
            return "PROCEED: Low risk shipment. Standard monitoring recommended."
        elif score < 50:
            return "PROCEED WITH CAUTION: Moderate risk. Consider additional coverage."
        elif score < 75:
            return "REVIEW REQUIRED: High risk identified. Evaluate alternatives."
        else:
            return "DO NOT SHIP: Critical risk. Immediate mitigation required."
    
    @staticmethod
    def _get_top_risk_drivers(risk_data: Dict, top_n: int = 3) -> List[Dict]:
        """Extract top N risk contributors."""
        factors = risk_data.get('risk_factors', [])
        
        if isinstance(factors, list):
            sorted_factors = sorted(
                factors,
                key=lambda x: x.get('score', 0) if isinstance(x, dict) else 0,
                reverse=True
            )
            return [
                {
                    "factor": f.get('name', 'Unknown'),
                    "score": f.get('score', 0),
                    "contribution": f.get('contribution', 0),
                    "description": f.get('description', '')
                }
                for f in sorted_factors[:top_n]
                if isinstance(f, dict)
            ]
        
        return []
    
    @staticmethod
    def _compare_to_baseline(risk_data: Dict) -> Dict:
        """Compare to industry baseline."""
        score = risk_data.get('risk_score', 50)
        industry_avg = 45  # Industry average
        
        return {
            "industry_average": industry_avg,
            "your_score": round(score, 1),
            "difference": round(score - industry_avg, 1),
            "percentile": PersonaAdapter._estimate_percentile(score),
            "comparison": "above" if score > industry_avg else "below"
        }
    
    @staticmethod
    def _estimate_percentile(score: float) -> int:
        """Estimate score percentile."""
        # Simplified: assume normal distribution centered at 45
        if score < 20:
            return 10
        elif score < 35:
            return 25
        elif score < 50:
            return 50
        elif score < 65:
            return 75
        else:
            return 90
    
    @staticmethod
    def _generate_executive_actions(risk_data: Dict, max_actions: int = 3) -> List[Dict]:
        """Generate executive action items."""
        score = risk_data.get('risk_score', 50)
        actions = []
        
        if score > 70:
            actions.append({
                "action": "Escalate to risk committee",
                "priority": "immediate",
                "owner": "Risk Manager"
            })
        
        if score > 50:
            actions.append({
                "action": "Review insurance coverage",
                "priority": "high",
                "owner": "Finance"
            })
        
        if score > 40:
            actions.append({
                "action": "Monitor shipment closely",
                "priority": "medium",
                "owner": "Operations"
            })
        
        if not actions:
            actions.append({
                "action": "Proceed with standard monitoring",
                "priority": "low",
                "owner": "Operations"
            })
        
        return actions[:max_actions]
    
    @staticmethod
    def _generate_mitigation_plan(risk_data: Dict) -> List[Dict]:
        """Generate actionable mitigation steps for operations."""
        score = risk_data.get('risk_score', 50)
        top_factors = PersonaAdapter._get_top_risk_drivers(risk_data, top_n=5)
        
        mitigation_steps = []
        
        for factor in top_factors:
            factor_name = factor.get('factor', '').lower()
            contribution = factor.get('contribution', 0)
            
            if 'weather' in factor_name:
                mitigation_steps.append({
                    "action": "Monitor weather forecasts daily and prepare contingency",
                    "priority": "high" if contribution > 20 else "medium",
                    "timeline": "Ongoing until delivery",
                    "responsible": "Operations team",
                    "cost_estimate": "$0",
                    "risk_reduction": f"{contribution * 0.3:.1f}%"
                })
            
            elif 'carrier' in factor_name:
                mitigation_steps.append({
                    "action": "Request carrier performance guarantee or consider alternative",
                    "priority": "high",
                    "timeline": "Before booking confirmation",
                    "responsible": "Logistics manager",
                    "cost_estimate": "$200-500",
                    "risk_reduction": f"{contribution * 0.4:.1f}%"
                })
            
            elif 'route' in factor_name:
                mitigation_steps.append({
                    "action": "Evaluate alternative routes or multi-modal options",
                    "priority": "high",
                    "timeline": "Within 48 hours",
                    "responsible": "Route planning team",
                    "cost_estimate": "Varies",
                    "risk_reduction": f"{contribution * 0.5:.1f}%"
                })
            
            elif 'customs' in factor_name or 'port' in factor_name:
                mitigation_steps.append({
                    "action": "Pre-clear documentation and engage customs broker",
                    "priority": "medium",
                    "timeline": "Before shipment departure",
                    "responsible": "Compliance team",
                    "cost_estimate": "$300-800",
                    "risk_reduction": f"{contribution * 0.4:.1f}%"
                })
        
        # Add insurance recommendation for high risk
        if score > 60:
            cargo_value = risk_data.get('cargo_value', 100000)
            mitigation_steps.append({
                "action": "Purchase additional cargo insurance coverage",
                "priority": "high",
                "timeline": "Before shipment departure",
                "responsible": "Finance/Risk team",
                "cost_estimate": f"${cargo_value * 0.005:,.2f} (0.5% of cargo value)",
                "risk_reduction": "Financial protection, not risk reduction"
            })
        
        return mitigation_steps
    
    @staticmethod
    def _identify_checkpoints(risk_data: Dict) -> List[Dict]:
        """Identify critical monitoring checkpoints."""
        return [
            {"checkpoint": "Pre-departure inspection", "timing": "T-24h"},
            {"checkpoint": "Port of loading confirmation", "timing": "T+0"},
            {"checkpoint": "Mid-transit status check", "timing": "T+50%"},
            {"checkpoint": "Customs clearance", "timing": "T+90%"},
            {"checkpoint": "Final delivery confirmation", "timing": "T+100%"}
        ]
    
    @staticmethod
    def _suggest_carrier_alternatives(risk_data: Dict) -> List[Dict]:
        """Suggest alternative carriers."""
        current_carrier = risk_data.get('carrier', 'Unknown')
        
        # In production, this would query a carrier database
        return [
            {"carrier": "MAERSK", "reliability_score": 8.5, "cost_delta": "+5%"},
            {"carrier": "MSC", "reliability_score": 8.2, "cost_delta": "+2%"},
            {"carrier": "CMA CGM", "reliability_score": 8.0, "cost_delta": "0%"}
        ]
    
    @staticmethod
    def _suggest_route_alternatives(risk_data: Dict) -> List[Dict]:
        """Suggest alternative routes."""
        return [
            {"route": "Direct", "transit_days": 28, "risk_adjustment": 0},
            {"route": "Via Singapore", "transit_days": 32, "risk_adjustment": -5},
            {"route": "Via Panama", "transit_days": 25, "risk_adjustment": +3}
        ]
    
    @staticmethod
    def _create_monitoring_plan(risk_data: Dict) -> Dict:
        """Create monitoring plan based on risk level."""
        score = risk_data.get('risk_score', 50)
        
        if score > 70:
            frequency = "Every 6 hours"
            escalation_threshold = "Any deviation"
        elif score > 50:
            frequency = "Daily"
            escalation_threshold = "Delay > 24 hours"
        else:
            frequency = "Every 3 days"
            escalation_threshold = "Delay > 48 hours"
        
        return {
            "monitoring_frequency": frequency,
            "escalation_threshold": escalation_threshold,
            "notification_channels": ["Email", "SMS", "Dashboard"],
            "responsible_parties": ["Operations", "Account Manager"]
        }
    
    @staticmethod
    def _get_escalation_matrix(score: float) -> List[Dict]:
        """Get escalation contacts based on risk level."""
        if score > 80:
            return [
                {"level": 1, "contact": "Risk Manager", "response_time": "1 hour"},
                {"level": 2, "contact": "VP Operations", "response_time": "2 hours"},
                {"level": 3, "contact": "CEO", "response_time": "4 hours"}
            ]
        elif score > 60:
            return [
                {"level": 1, "contact": "Operations Lead", "response_time": "4 hours"},
                {"level": 2, "contact": "Risk Manager", "response_time": "8 hours"}
            ]
        else:
            return [
                {"level": 1, "contact": "Operations Team", "response_time": "24 hours"}
            ]
    
    @staticmethod
    def _get_sensitivity_summary(risk_data: Dict) -> Dict:
        """Get sensitivity analysis summary."""
        return risk_data.get('sensitivity_analysis', {
            "most_sensitive_factor": "weather_risk",
            "sensitivity_range": {"min": 35, "max": 72},
            "key_drivers_impact": []
        })
    
    @staticmethod
    def _generate_analyst_scenarios(risk_data: Dict) -> List[Dict]:
        """Generate scenario analysis for analysts."""
        base_score = risk_data.get('risk_score', 50)
        
        return [
            {
                "scenario": "Best Case",
                "description": "All risk factors at minimum",
                "score": max(10, base_score - 20),
                "probability": 0.15
            },
            {
                "scenario": "Base Case",
                "description": "Current assessment",
                "score": base_score,
                "probability": 0.60
            },
            {
                "scenario": "Worst Case",
                "description": "All risk factors at maximum",
                "score": min(95, base_score + 25),
                "probability": 0.25
            }
        ]
    
    @staticmethod
    def _find_similar_shipments(risk_data: Dict) -> List[Dict]:
        """Find comparable historical shipments."""
        # In production, this would query historical database
        return [
            {"shipment_id": "SHP-2024-001", "similarity": 0.92, "outcome": "On-time"},
            {"shipment_id": "SHP-2024-002", "similarity": 0.87, "outcome": "3-day delay"},
            {"shipment_id": "SHP-2023-999", "similarity": 0.85, "outcome": "On-time"}
        ]
    
    # ========================
    # Insurance Methods
    # ========================
    
    @staticmethod
    def _determine_risk_class(score: float) -> str:
        """Map risk score to insurance risk class."""
        if score < 25:
            return "Class A (Preferred)"
        elif score < 45:
            return "Class B (Standard)"
        elif score < 65:
            return "Class C (Standard Plus)"
        elif score < 80:
            return "Class D (Substandard)"
        else:
            return "Class E (High Risk / Decline)"
    
    @staticmethod
    def _get_risk_grade(score: float) -> str:
        """Get letter grade for risk."""
        if score < 20:
            return "A+"
        elif score < 30:
            return "A"
        elif score < 40:
            return "B+"
        elif score < 50:
            return "B"
        elif score < 60:
            return "C"
        elif score < 75:
            return "D"
        else:
            return "F"
    
    @staticmethod
    def _determine_acceptability(score: float) -> Dict:
        """Determine underwriting acceptability."""
        if score < 60:
            return {"status": "acceptable", "conditions": "standard"}
        elif score < 80:
            return {"status": "conditional", "conditions": "enhanced due diligence required"}
        else:
            return {"status": "decline", "conditions": "risk exceeds appetite"}
    
    @staticmethod
    def _calculate_premium_adjustment(risk_score: float, cargo_value: float) -> Dict:
        """Calculate insurance premium adjustment."""
        # Base premium: 0.5% of cargo value
        base_rate = 0.005
        
        # Risk multiplier
        if risk_score < 25:
            multiplier = 0.6  # 40% discount
        elif risk_score < 45:
            multiplier = 0.8  # 20% discount
        elif risk_score < 65:
            multiplier = 1.0  # Standard
        elif risk_score < 80:
            multiplier = 1.5  # 50% surcharge
        else:
            multiplier = 2.5  # 150% surcharge
        
        adjusted_rate = base_rate * multiplier
        premium = cargo_value * adjusted_rate
        
        return {
            "base_premium_rate": base_rate,
            "risk_multiplier": multiplier,
            "adjusted_premium_rate": adjusted_rate,
            "suggested_premium_usd": round(premium, 2),
            "adjustment_reason": PersonaAdapter._explain_premium_adjustment(risk_score),
            "rate_per_thousand": round(adjusted_rate * 1000, 2)
        }
    
    @staticmethod
    def _explain_premium_adjustment(risk_score: float) -> str:
        """Explain premium adjustment reasoning."""
        if risk_score < 25:
            return "Low risk profile warrants premium discount"
        elif risk_score < 45:
            return "Below-average risk justifies moderate discount"
        elif risk_score < 65:
            return "Average risk, standard premium applies"
        elif risk_score < 80:
            return "Elevated risk requires premium surcharge"
        else:
            return "High risk requires significant premium increase"
    
    @staticmethod
    def _estimate_loss_frequency(risk_score: float) -> float:
        """Estimate annual loss frequency."""
        # Industry average: ~2% loss rate
        base_frequency = 0.02
        
        # Adjust based on risk score
        adjustment = (risk_score - 50) / 100
        frequency = base_frequency * (1 + adjustment * 2)
        
        return round(max(0.001, min(0.15, frequency)), 4)
    
    @staticmethod
    def _estimate_loss_severity(risk_data: Dict) -> float:
        """Estimate average loss severity."""
        cargo_value = risk_data.get('cargo_value', 100000)
        risk_score = risk_data.get('risk_score', 50)
        
        # Base severity: 15% of cargo value
        base_severity = 0.15
        
        # Adjust based on risk
        adjustment = (risk_score - 50) / 200
        severity_rate = base_severity * (1 + adjustment)
        
        return round(cargo_value * severity_rate, 2)
    
    @staticmethod
    def _estimate_combined_ratio_impact(risk_score: float) -> float:
        """Estimate impact on insurer's combined ratio."""
        # Simplified: higher risk = higher claims = higher combined ratio
        base_impact = 0  # Neutral
        
        if risk_score > 70:
            return 5.0  # +5% impact
        elif risk_score > 50:
            return 2.0  # +2% impact
        elif risk_score < 30:
            return -2.0  # -2% (favorable)
        else:
            return 0
    
    @staticmethod
    def _calculate_burning_cost(risk_data: Dict) -> float:
        """Calculate burning cost rate."""
        frequency = PersonaAdapter._estimate_loss_frequency(
            risk_data.get('risk_score', 50)
        )
        severity = PersonaAdapter._estimate_loss_severity(risk_data)
        cargo_value = risk_data.get('cargo_value', 100000)
        
        burning_cost = (frequency * severity) / cargo_value
        return round(burning_cost * 100, 4)  # As percentage
    
    @staticmethod
    def _recommend_coverage_type(risk_data: Dict) -> str:
        """Recommend coverage type."""
        risk_score = risk_data.get('risk_score', 50)
        cargo_type = risk_data.get('cargo_type', 'standard')
        
        if risk_score > 70 or cargo_type in ['hazardous', 'fragile']:
            return "All-Risk with Enhanced Coverage"
        elif risk_score > 50:
            return "All-Risk (Institute Cargo Clause A)"
        else:
            return "Named Perils (Institute Cargo Clause C)"
    
    @staticmethod
    def _identify_coverage_gaps(risk_data: Dict) -> List[str]:
        """Identify potential coverage gaps."""
        gaps = []
        
        risk_score = risk_data.get('risk_score', 50)
        cargo_type = risk_data.get('cargo_type', 'standard')
        
        if risk_score > 70:
            gaps.append("Delay in delivery coverage recommended")
        
        if cargo_type in ['fragile', 'electronics']:
            gaps.append("Breakage extension required")
        
        if 'war' in risk_data.get('route', '').lower():
            gaps.append("War risk coverage required")
        
        return gaps
    
    @staticmethod
    def _suggest_deductible(risk_score: float, cargo_value: float) -> float:
        """Suggest appropriate deductible."""
        # Higher risk = higher deductible
        if risk_score > 70:
            deductible_rate = 0.05  # 5%
        elif risk_score > 50:
            deductible_rate = 0.02  # 2%
        else:
            deductible_rate = 0.01  # 1%
        
        deductible = cargo_value * deductible_rate
        
        # Apply min/max limits
        return round(max(500, min(50000, deductible)), 2)
    
    @staticmethod
    def _suggest_exclusions(risk_data: Dict) -> List[str]:
        """Suggest policy exclusions."""
        exclusions = []
        
        risk_score = risk_data.get('risk_score', 50)
        
        if risk_score > 80:
            exclusions.append("Delay in delivery")
            exclusions.append("Market loss")
        
        exclusions.append("Inherent vice")
        exclusions.append("Willful misconduct")
        
        return exclusions
    
    @staticmethod
    def _suggest_conditions(risk_data: Dict) -> List[str]:
        """Suggest policy conditions."""
        conditions = []
        
        risk_score = risk_data.get('risk_score', 50)
        
        if risk_score > 60:
            conditions.append("Pre-shipment inspection required")
            conditions.append("Notify insurer 48h before departure")
        
        conditions.append("Prompt notice of loss")
        conditions.append("Duty to mitigate")
        
        return conditions
    
    @staticmethod
    def _check_regulatory_requirements(risk_data: Dict) -> Dict:
        """Check regulatory compliance requirements."""
        return {
            "sanctions_check_required": True,
            "aml_screening_required": risk_data.get('cargo_value', 0) > 100000,
            "export_license_check": risk_data.get('cargo_type') in ['hazardous', 'dual-use'],
            "solvency_ii_compliant": True,
            "reporting_requirements": ["Claims register", "Loss ratio tracking"]
        }
    
    @staticmethod
    def _assess_reinsurance_needs(risk_score: float, cargo_value: float) -> Dict:
        """Assess reinsurance implications."""
        if cargo_value > 1000000 and risk_score > 60:
            return {
                "facultative_recommended": True,
                "treaty_capacity_check": True,
                "estimated_cession": f"{min(90, 50 + risk_score/2):.0f}%"
            }
        else:
            return {
                "facultative_recommended": False,
                "treaty_capacity_check": False,
                "estimated_cession": "Treaty capacity sufficient"
            }


# Convenience functions for API
def adapt_for_persona(risk_data: Dict, persona: str) -> Dict:
    """
    Adapt risk data for specified persona.
    
    Args:
        risk_data: Full risk calculation result
        persona: Persona name ('executive', 'analyst', 'operations', 'insurance')
    
    Returns:
        Persona-adapted response
    """
    persona_enum = UserPersona(persona.lower())
    return PersonaAdapter.adapt(risk_data, persona_enum)
