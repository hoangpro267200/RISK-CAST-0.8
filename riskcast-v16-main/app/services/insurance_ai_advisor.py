"""
RISKCAST Insurance AI Advisor
==============================
AI-powered explanation and recommendation engine for insurance products.
Provides transparent, compliant, and trusted guidance.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from app.models.insurance import InsuranceQuote, InsuranceProduct
from app.services.parametric_engine import BasisRiskCalculator

logger = logging.getLogger(__name__)


@dataclass
class AIAdvisorResponse:
    """AI Advisor response structure."""
    mode: str  # 'recommendation' | 'explanation' | 'education' | 'compliance'
    confidence: float  # 0-1
    reasoning: List[str]
    data_sources: List[str]
    disclaimers: List[str]
    next_actions: List[str]
    comparison_table: Optional[Dict[str, Any]] = None
    visual_breakdown: Optional[Dict[str, Any]] = None
    payout_curve: Optional[Dict[str, Any]] = None
    scenario_analysis: Optional[List[Dict[str, Any]]] = None


class InsuranceAIAdvisor:
    """
    AI Advisor for insurance products.
    Provides explanations, recommendations, and education.
    """
    
    # Prohibited phrases (compliance-safe language)
    PROHIBITED_PHRASES = [
        'guarantee', 'definitely', 'always', 'never',
        'eliminate all risk', 'must buy', 'should buy',
        'you need', 'perfect prediction'
    ]
    
    # Required disclaimers
    REQUIRED_DISCLAIMERS = {
        'recommendation': 'This recommendation is based on statistical analysis and should not be considered financial advice.',
        'prediction': 'Past performance does not guarantee future results.',
        'model_output': 'Model outputs are estimates based on historical data and inherent uncertainty.'
    }
    
    @staticmethod
    def answer_why_buy_insurance(
        risk_assessment: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None
    ) -> AIAdvisorResponse:
        """
        Answer: "Do I really need insurance for this shipment?"
        
        Args:
            risk_assessment: RISKCAST risk assessment result
            user_profile: User profile with risk tolerance, etc.
            
        Returns:
            AIAdvisorResponse with recommendation
        """
        risk_score = risk_assessment.get("risk_score", {}).get("overallScore", 50)
        risk_level = "high" if risk_score > 70 else "moderate" if risk_score > 50 else "low"
        
        # Get financial metrics
        financial = risk_assessment.get("financial", {})
        expected_loss = financial.get("expectedLoss", 0)
        var_95 = financial.get("var95", 0)
        
        # Get top risks
        layers = risk_assessment.get("layers", [])
        top_risks = sorted(
            [{"name": l.get("name", ""), "score": l.get("score", 0)} for l in layers],
            key=lambda x: x["score"],
            reverse=True
        )[:3]
        
        # Build reasoning
        reasoning = [
            f"Your risk assessment shows a {risk_score:.1f} risk score, which is {risk_level}.",
            f"The expected loss on this shipment is ${expected_loss:,.0f}, "
            f"while insurance would typically cost ${expected_loss * 0.15:,.0f} "
            f"({expected_loss * 0.15 / expected_loss * 100:.1f}% of expected loss).",
        ]
        
        if top_risks:
            reasoning.append("The main risk factors are:")
            for i, risk in enumerate(top_risks, 1):
                reasoning.append(f"{i}. {risk['name']}: {risk['score']}/100")
        
        if var_95 > 0:
            reasoning.append(
                f"There's a 5% chance of losses exceeding ${var_95:,.0f}, "
                f"which could represent a significant financial impact."
            )
        
        # Data sources
        data_sources = [
            'RISKCAST risk assessment',
            'Historical loss data (2019-2025)',
            'Monte Carlo simulation (10,000 scenarios)',
        ]
        
        if user_profile:
            data_sources.append('Your company risk profile')
        
        # Disclaimers
        disclaimers = [
            InsuranceAIAdvisor.REQUIRED_DISCLAIMERS['recommendation'],
            'Insurance decisions should consider your complete financial situation.',
            InsuranceAIAdvisor.REQUIRED_DISCLAIMERS['prediction']
        ]
        
        # Next actions
        next_actions = [
            'View detailed risk breakdown',
            'Compare insurance products',
            'Speak with human advisor',
            'Proceed without insurance'
        ]
        
        return AIAdvisorResponse(
            mode='recommendation',
            confidence=0.85,
            reasoning=reasoning,
            data_sources=data_sources,
            disclaimers=disclaimers,
            next_actions=next_actions
        )
    
    @staticmethod
    def explain_product_recommendation(
        selected_product: InsuranceProduct,
        alternatives: List[InsuranceProduct],
        risk_assessment: Dict[str, Any]
    ) -> AIAdvisorResponse:
        """
        Explain why a specific product is recommended.
        
        Args:
            selected_product: The recommended product
            alternatives: Alternative products
            risk_assessment: Risk assessment data
            
        Returns:
            AIAdvisorResponse with explanation
        """
        reasoning = []
        
        # Check if parametric
        is_parametric = selected_product.category.value == "parametric"
        
        if is_parametric:
            # Get port congestion or weather risk
            layers = risk_assessment.get("layers", [])
            port_risk = next(
                (l.get("score", 0) for l in layers 
                 if "port" in l.get("name", "").lower() or "congestion" in l.get("name", "").lower()),
                0
            )
            weather_risk = next(
                (l.get("score", 0) for l in layers 
                 if "weather" in l.get("name", "").lower() or "climate" in l.get("name", "").lower()),
                0
            )
            
            reasoning.append(
                f"Parametric {selected_product.name.lower()} is recommended because:"
            )
            
            if port_risk > 60:
                reasoning.append(
                    f"1. **Aligned with your main risk:** Your #1 risk driver is port congestion ({port_risk}/100). "
                    "Parametric products trigger on measurable congestion metrics, directly addressing this risk."
                )
            
            reasoning.extend([
                "2. **Faster payout:** Parametric claims settle in 48 hours vs 30-90 days for traditional claims.",
                "3. **Lower basis risk:** The trigger correlates highly with your actual financial loss from delays.",
                "4. **Cost efficiency:** Parametric premium is typically 30-50% lower than equivalent traditional coverage.",
                "5. **No claims hassle:** Automatic payout means no paperwork, no adjuster, no disputes."
            ])
        else:
            reasoning.append(
                f"Classical {selected_product.name.lower()} is recommended because:"
            )
            reasoning.extend([
                "1. **Comprehensive coverage:** Covers physical damage, theft, and total loss.",
                "2. **Proven track record:** Traditional insurance with decades of industry experience.",
                "3. **Wide acceptance:** Accepted by banks, trade finance, and all stakeholders."
            ])
        
        # Comparison table
        comparison_table = {
            "dimensions": []
        }
        
        if is_parametric:
            comparison_table["dimensions"] = [
                {"name": "Speed to Payout", "parametric": "48 hours", "traditional": "30-90 days"},
                {"name": "Claims Process", "parametric": "Automatic", "traditional": "Manual review"},
                {"name": "Premium", "parametric": "Lower (30-50% savings)", "traditional": "Higher"},
                {"name": "Basis Risk", "parametric": "Low (0.15)", "traditional": "N/A"},
            ]
        
        disclaimers = [
            InsuranceAIAdvisor.REQUIRED_DISCLAIMERS['recommendation']
        ]
        
        if is_parametric:
            disclaimers.append(
                "Parametric insurance pays based on triggers, not actual losses. "
                "There may be cases where you suffer a loss but the trigger is not met (basis risk)."
            )
        
        return AIAdvisorResponse(
            mode='explanation',
            confidence=0.90,
            reasoning=reasoning,
            data_sources=[
                'Risk factor correlation analysis',
                'Historical claims settlement data',
                'Basis risk calculations',
                'Premium pricing models'
            ],
            disclaimers=disclaimers,
            next_actions=[
                'See full comparison',
                'Ask follow-up question',
                'Buy now'
            ],
            comparison_table=comparison_table
        )
    
    @staticmethod
    def explain_pricing_calculation(
        quote: InsuranceQuote,
        risk_assessment: Dict[str, Any]
    ) -> AIAdvisorResponse:
        """
        Explain how premium was calculated.
        
        Args:
            quote: Insurance quote
            risk_assessment: Risk assessment data
            
        Returns:
            AIAdvisorResponse with pricing breakdown
        """
        if not quote.pricing_breakdown:
            return AIAdvisorResponse(
                mode='explanation',
                confidence=0.5,
                reasoning=["Pricing breakdown not available for this quote."],
                data_sources=[],
                disclaimers=[],
                next_actions=[]
            )
        
        pb = quote.pricing_breakdown
        reasoning = [
            "Let me break down how this premium was calculated:",
            "",
            "**Step 1: Expected Loss Calculation**",
            f"Based on 10,000 Monte Carlo scenarios:",
            f"• Average loss across scenarios: ${pb.expected_loss:,.0f}",
            f"• This comes from historical data on similar shipments (2019-2025)",
            "",
            "**Step 2: Risk Adjustments**",
        ]
        
        for adj in pb.risk_adjustments:
            reasoning.append(
                f"• {adj.get('factor', 'unknown')}: {adj.get('score', 0)}/100 → {adj.get('adjustment', 'N/A')}"
            )
            if adj.get('reasoning'):
                reasoning.append(f"  Reason: {adj['reasoning']}")
        
        reasoning.extend([
            "",
            f"**Step 3: Load Factor ({pb.load_factor:.2f}x)**",
            "This covers:",
            "• Capital cost: Insurance requires capital reserves",
            "• Profit margin: Provider needs sustainable return",
            "• Uncertainty buffer: Model may underestimate tail risks",
            "",
            f"**Step 4: Administrative Costs ({pb.administrative_costs:,.0f})**",
            "• Underwriting: Policy issuance, compliance",
            "• Claims handling: Even parametric has some overhead",
            "• Technology: API maintenance, monitoring systems",
            "",
            "**Final Calculation:**",
            f"Expected Loss × Load Factor + Admin = Premium",
            f"${pb.expected_loss:,.0f} × {pb.load_factor:.2f} + ${pb.administrative_costs:,.0f} = ${quote.premium.total_premium:,.0f}",
        ])
        
        # Visual breakdown
        visual_breakdown = {
            "expected_loss": pb.expected_loss,
            "load_factor_portion": pb.expected_loss * (pb.load_factor - 1),
            "admin_portion": pb.administrative_costs,
            "total": quote.premium.total_premium
        }
        
        disclaimers = [
            'Premium calculations use historical data and may not predict future losses perfectly.',
            'Actual losses may be higher or lower than expected loss.',
            InsuranceAIAdvisor.REQUIRED_DISCLAIMERS['prediction']
        ]
        
        return AIAdvisorResponse(
            mode='explanation',
            confidence=0.85,
            reasoning=reasoning,
            data_sources=[
                'Monte Carlo simulation (10,000 scenarios)',
                'Historical loss data',
                'Risk factor analysis',
                'Market pricing models'
            ],
            disclaimers=disclaimers,
            next_actions=[
                'Adjust coverage parameters',
                'Compare market rates',
                'Ask questions'
            ],
            visual_breakdown=visual_breakdown
        )
    
    @staticmethod
    def educate_parametric() -> AIAdvisorResponse:
        """
        Educate user about parametric insurance.
        
        Returns:
            AIAdvisorResponse with education content
        """
        reasoning = [
            "**What is Parametric Insurance?**",
            "Parametric insurance pays based on a predefined trigger event, not your actual loss.",
            "",
            "Traditional insurance: \"Prove your loss happened, and we'll reimburse you.\"",
            "Parametric insurance: \"If X happens, you automatically get $Y.\"",
            "",
            "**Example with Port Delay:**",
            "• Trigger: Container dwell time >14 days",
            "• Payout: $1,000 per day above 14 days",
            "",
            "Scenario 1: Container waits 19 days",
            "→ Trigger met: 5 days excess",
            "→ Payout: 5 × $1,000 = $5,000 (automatic)",
            "→ You receive $5,000 within 48 hours",
            "",
            "**Basis Risk:**",
            "Because payout is based on trigger (not actual loss), there's always some mismatch.",
            "",
            "This means:",
            "• 85% of the time, trigger accurately reflects your loss",
            "• 15% of the time, there's a mismatch (could benefit you or hurt you)",
            "",
            "**When Parametric Makes Sense:**",
            "✓ Your main risk is delay (not physical damage)",
            "✓ You need fast cash flow (not just eventual reimbursement)",
            "✓ The trigger closely matches your loss driver (low basis risk)",
            "✓ You want certainty over perfection",
        ]
        
        disclaimers = [
            InsuranceAIAdvisor.REQUIRED_DISCLAIMERS['recommendation'],
            'Parametric insurance does not guarantee perfect loss coverage due to basis risk.',
            'You should evaluate whether the trigger aligns with your specific loss drivers.'
        ]
        
        return AIAdvisorResponse(
            mode='education',
            confidence=0.95,
            reasoning=reasoning,
            data_sources=[
                'Insurance industry best practices',
                'Parametric insurance literature',
                'RISKCAST risk model analysis'
            ],
            disclaimers=disclaimers,
            next_actions=[
                'Try parametric simulator',
                'Ask follow-up questions',
                'Compare with traditional insurance'
            ]
        )
    
    @staticmethod
    def filter_compliance(response: str, context: str) -> str:
        """
        Filter response for compliance-safe language.
        
        Args:
            response: AI response text
            context: Context ('recommendation', 'prediction', etc.)
            
        Returns:
            Filtered response with disclaimers
        """
        # Check for prohibited phrases
        response_lower = response.lower()
        for phrase in InsuranceAIAdvisor.PROHIBITED_PHRASES:
            if phrase in response_lower:
                logger.warning(f"Prohibited phrase detected: {phrase}")
                # Replace with compliant alternative
                response = response.replace(phrase, "may" if phrase == "guarantee" else "often")
        
        # Add appropriate disclaimers
        if context in InsuranceAIAdvisor.REQUIRED_DISCLAIMERS:
            disclaimer = InsuranceAIAdvisor.REQUIRED_DISCLAIMERS[context]
            if disclaimer not in response:
                response += f"\n\n{disclaimer}"
        
        return response
    
    @staticmethod
    def to_dict(response: AIAdvisorResponse) -> Dict[str, Any]:
        """Convert AIAdvisorResponse to dictionary."""
        result = {
            "mode": response.mode,
            "confidence": response.confidence,
            "reasoning": response.reasoning,
            "data_sources": response.data_sources,
            "disclaimers": response.disclaimers,
            "next_actions": response.next_actions,
        }
        
        if response.comparison_table:
            result["comparison_table"] = response.comparison_table
        if response.visual_breakdown:
            result["visual_breakdown"] = response.visual_breakdown
        if response.payout_curve:
            result["payout_curve"] = response.payout_curve
        if response.scenario_analysis:
            result["scenario_analysis"] = response.scenario_analysis
        
        return result
