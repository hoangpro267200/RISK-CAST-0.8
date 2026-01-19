"""
AI System Advisor - Recommendation Engine
Generate intelligent risk mitigation recommendations
"""

from typing import Dict, List, Optional, Any
from app.ai_system_advisor.types import Recommendation


class RecommendationEngine:
    """Generates intelligent recommendations"""
    
    def __init__(self):
        """Initialize recommendation engine"""
        pass
    
    def generate_recommendations(
        self,
        risk_assessment: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Recommendation]:
        """
        Generate recommendations from risk assessment
        
        Args:
            risk_assessment: Risk assessment dictionary
            context: Optional context
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Extract key data
        risk_score = risk_assessment.get('risk_score', 0) or \
                    risk_assessment.get('profile', {}).get('score', 0) or \
                    risk_assessment.get('overview', {}).get('riskScore', {}).get('score', 0)
        
        drivers = risk_assessment.get('drivers', [])
        layers = risk_assessment.get('layers', []) or \
                 risk_assessment.get('breakdown', {}).get('layers', [])
        
        financial = risk_assessment.get('loss', {})
        expected_loss = financial.get('expectedLoss', financial.get('expected_loss', 0))
        
        # Generate recommendations based on risk level
        if risk_score >= 70:
            # High risk - aggressive recommendations
            recommendations.extend(self._generate_high_risk_recommendations(
                risk_score, drivers, expected_loss
            ))
        elif risk_score >= 40:
            # Moderate risk - balanced recommendations
            recommendations.extend(self._generate_moderate_risk_recommendations(
                risk_score, drivers, expected_loss
            ))
        else:
            # Low risk - preventive recommendations
            recommendations.extend(self._generate_low_risk_recommendations(
                risk_score, drivers
            ))
        
        # Add driver-specific recommendations
        if drivers:
            recommendations.extend(self._generate_driver_specific_recommendations(drivers))
        
        # Add layer-specific recommendations
        if layers:
            recommendations.extend(self._generate_layer_specific_recommendations(layers))
        
        # Remove duplicates and sort by priority
        recommendations = self._deduplicate_recommendations(recommendations)
        recommendations.sort(key=lambda x: x.priority)
        
        return recommendations
    
    def _generate_high_risk_recommendations(
        self,
        risk_score: float,
        drivers: List[Dict],
        expected_loss: float
    ) -> List[Recommendation]:
        """Generate recommendations for high risk"""
        recs = []
        
        recs.append(Recommendation(
            title="Immediate Route Alternative",
            description=f"Consider alternative route to reduce {risk_score:.1f} risk score. Expected loss of ${expected_loss:,.0f} justifies route change.",
            risk_reduction=15.0,
            cost_impact=3000.0,
            feasibility=0.7,
            priority=1,
            category="ROUTING"
        ))
        
        recs.append(Recommendation(
            title="Premium Insurance Coverage",
            description=f"Increase insurance coverage to protect against ${expected_loss:,.0f} expected loss. High risk warrants comprehensive protection.",
            risk_reduction=8.0,
            cost_impact=2000.0,
            feasibility=0.95,
            priority=2,
            category="INSURANCE"
        ))
        
        recs.append(Recommendation(
            title="Enhanced Monitoring & Alerts",
            description="Implement real-time tracking with automated alerts for delays, weather, and port congestion.",
            risk_reduction=5.0,
            cost_impact=800.0,
            feasibility=0.9,
            priority=3,
            category="MONITORING"
        ))
        
        return recs
    
    def _generate_moderate_risk_recommendations(
        self,
        risk_score: float,
        drivers: List[Dict],
        expected_loss: float
    ) -> List[Recommendation]:
        """Generate recommendations for moderate risk"""
        recs = []
        
        recs.append(Recommendation(
            title="Standard Insurance Coverage",
            description=f"Standard insurance coverage recommended for ${expected_loss:,.0f} expected loss.",
            risk_reduction=4.0,
            cost_impact=1000.0,
            feasibility=0.95,
            priority=1,
            category="INSURANCE"
        ))
        
        recs.append(Recommendation(
            title="Enhanced Monitoring",
            description="Add real-time tracking and weekly status updates.",
            risk_reduction=3.0,
            cost_impact=500.0,
            feasibility=0.9,
            priority=2,
            category="MONITORING"
        ))
        
        return recs
    
    def _generate_low_risk_recommendations(
        self,
        risk_score: float,
        drivers: List[Dict]
    ) -> List[Recommendation]:
        """Generate recommendations for low risk"""
        recs = []
        
        recs.append(Recommendation(
            title="Standard Monitoring",
            description="Continue with standard monitoring procedures. Low risk level indicates minimal concerns.",
            risk_reduction=1.0,
            cost_impact=0.0,
            feasibility=1.0,
            priority=1,
            category="MONITORING"
        ))
        
        return recs
    
    def _generate_driver_specific_recommendations(
        self,
        drivers: List[Dict]
    ) -> List[Recommendation]:
        """Generate recommendations based on specific risk drivers"""
        recs = []
        
        for driver in drivers[:3]:  # Top 3 drivers
            name = driver.get('name', '').lower()
            impact = driver.get('impact', 0)
            
            if 'port' in name or 'congestion' in name:
                recs.append(Recommendation(
                    title="Port Congestion Mitigation",
                    description=f"Port congestion is a major driver ({impact:.1f}% impact). Consider alternative ports or timing adjustment.",
                    risk_reduction=impact * 0.3,
                    cost_impact=1500.0,
                    feasibility=0.75,
                    priority=2,
                    category="ROUTING"
                ))
            elif 'weather' in name or 'climate' in name:
                recs.append(Recommendation(
                    title="Weather Risk Mitigation",
                    description=f"Weather risk is significant ({impact:.1f}% impact). Consider weather insurance or route adjustment.",
                    risk_reduction=impact * 0.25,
                    cost_impact=1200.0,
                    feasibility=0.8,
                    priority=2,
                    category="INSURANCE"
                ))
            elif 'carrier' in name or 'reliability' in name:
                recs.append(Recommendation(
                    title="Carrier Reliability Improvement",
                    description=f"Carrier reliability concerns ({impact:.1f}% impact). Consider alternative carrier or enhanced monitoring.",
                    risk_reduction=impact * 0.2,
                    cost_impact=1000.0,
                    feasibility=0.7,
                    priority=3,
                    category="CARRIER"
                ))
        
        return recs
    
    def _generate_layer_specific_recommendations(
        self,
        layers: List[Dict]
    ) -> List[Recommendation]:
        """Generate recommendations based on risk layers"""
        recs = []
        
        # Find high-risk layers
        high_risk_layers = [l for l in layers if l.get('score', 0) >= 70]
        
        for layer in high_risk_layers[:2]:  # Top 2 high-risk layers
            name = layer.get('name', '').lower()
            score = layer.get('score', 0)
            
            if 'packaging' in name:
                recs.append(Recommendation(
                    title="Packaging Quality Improvement",
                    description=f"Packaging quality is a concern (score: {score:.1f}). Improve packaging to reduce cargo damage risk.",
                    risk_reduction=5.0,
                    cost_impact=800.0,
                    feasibility=0.85,
                    priority=3,
                    category="CARGO"
                ))
            elif 'container' in name:
                recs.append(Recommendation(
                    title="Container Match Optimization",
                    description=f"Container match is suboptimal (score: {score:.1f}). Optimize container selection.",
                    risk_reduction=4.0,
                    cost_impact=600.0,
                    feasibility=0.8,
                    priority=3,
                    category="EQUIPMENT"
                ))
        
        return recs
    
    def analyze_cost_benefit(
        self,
        recommendation: Recommendation,
        risk_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze cost-benefit of recommendation
        
        Args:
            recommendation: Recommendation object
            risk_assessment: Risk assessment
            
        Returns:
            Cost-benefit analysis
        """
        financial = risk_assessment.get('loss', {})
        expected_loss = financial.get('expectedLoss', financial.get('expected_loss', 0))
        
        # Calculate benefit (risk reduction * expected loss)
        benefit = (recommendation.risk_reduction / 100) * expected_loss
        
        # Cost-benefit ratio
        cost_benefit_ratio = benefit / max(recommendation.cost_impact, 1)
        
        # ROI
        roi = ((benefit - recommendation.cost_impact) / max(recommendation.cost_impact, 1)) * 100
        
        return {
            "benefit": benefit,
            "cost": recommendation.cost_impact,
            "cost_benefit_ratio": cost_benefit_ratio,
            "roi": roi,
            "payback_period_days": None,  # Could calculate if we have time data
            "recommendation": "STRONG" if cost_benefit_ratio > 2 else "MODERATE" if cost_benefit_ratio > 1 else "WEAK"
        }
    
    def rank_recommendations(
        self,
        recommendations: List[Recommendation],
        sort_by: str = "risk_reduction"
    ) -> List[Recommendation]:
        """
        Rank recommendations
        
        Args:
            recommendations: List of recommendations
            sort_by: Sort criteria
            
        Returns:
            Sorted list
        """
        if sort_by == "risk_reduction":
            return sorted(recommendations, key=lambda x: x.risk_reduction, reverse=True)
        elif sort_by == "cost_benefit":
            # Would need cost-benefit analysis for each
            return sorted(recommendations, key=lambda x: x.risk_reduction / max(x.cost_impact, 1), reverse=True)
        elif sort_by == "feasibility":
            return sorted(recommendations, key=lambda x: x.feasibility, reverse=True)
        else:
            return recommendations
    
    def _deduplicate_recommendations(
        self,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """Remove duplicate recommendations"""
        seen = set()
        unique = []
        
        for rec in recommendations:
            key = (rec.title, rec.category)
            if key not in seen:
                seen.add(key)
                unique.append(rec)
        
        return unique
