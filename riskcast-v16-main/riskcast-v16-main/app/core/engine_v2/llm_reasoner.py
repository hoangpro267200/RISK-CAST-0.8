"""
RISKCAST Engine v2 - LLM Reasoner
Generates natural language explanations and reasoning for risk assessments
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os
from app.core.i18n.translator import Translator


@dataclass
class LLMReasoningResult:
    """LLM reasoning result"""
    explanation: str  # Main explanation
    key_drivers: List[str]  # Key risk drivers identified
    confidence_score: float  # 0-1
    suggestions: List[str]  # Mitigation suggestions
    business_justification: str  # Business-focused justification


class LLMReasoner:
    """LLM-based reasoner for risk explanations"""
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize LLM reasoner
        
        Args:
            use_llm: Whether to use actual LLM (requires API key) or deterministic logic
        """
        self.use_llm = use_llm
        self.anthropic_client = None
        
        # Try to initialize Anthropic client if available
        if use_llm:
            try:
                from anthropic import Anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key and api_key != "your_anthropic_api_key_here":
                    self.anthropic_client = Anthropic(api_key=api_key)
            except:
                self.use_llm = False
    
    def generate_reasoning_deterministic(self, factors: Dict[str, float],
                                        weights: Dict[str, float],
                                        score: float,
                                        profile: Dict) -> LLMReasoningResult:
        """
        Generate deterministic reasoning (fallback when LLM not available)
        
        Args:
            factors: Risk factor values
            weights: FAHP weights
            score: Final risk score
            profile: Risk profile dictionary
            
        Returns:
            LLMReasoningResult object
        """
        # Identify top factors
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
        top_3 = sorted_factors[:3]
        
        # Build explanation
        explanation_parts = []
        explanation_parts.append(f"Risk assessment indicates a {profile.get('level', 'Medium')} risk level (score: {score:.1f}/100).")
        
        if top_3:
            explanation_parts.append(f"The primary risk drivers are: {top_3[0][0]} ({top_3[0][1]:.2f}), {top_3[1][0]} ({top_3[1][1]:.2f}), and {top_3[2][0]} ({top_3[2][1]:.2f}).")
        
        # Factor-specific explanations
        if "climate" in factors and factors["climate"] > 0.6:
            explanation_parts.append("Climate conditions pose significant risk, particularly weather-related disruptions.")
        
        if "network" in factors and factors["network"] > 0.6:
            explanation_parts.append("Network and port dependencies create vulnerability to cascading disruptions.")
        
        if "carrier" in factors and factors.get("carrier", 0) > 0.6:
            explanation_parts.append("Carrier reliability concerns increase operational risk.")
        
        explanation = " ".join(explanation_parts)
        
        # Key drivers
        key_drivers = [factor[0] for factor in top_3]
        
        # Confidence based on data completeness and score consistency
        confidence = 0.8
        if len(factors) < 4:
            confidence *= 0.9  # Lower confidence with fewer factors
        if score < 20 or score > 90:
            confidence *= 0.95  # Slightly lower for extreme scores
        
        # Generate suggestions
        suggestions = []
        level = profile.get("level", "Medium")
        
        if level == "Critical" or score > 80:
            suggestions.append("Immediate risk mitigation required - consider alternative routes or carriers")
            suggestions.append("Increase insurance coverage and implement comprehensive contingency plans")
        elif level == "High" or score > 60:
            suggestions.append("Enhanced monitoring and proactive risk management recommended")
            suggestions.append("Review carrier performance and network redundancy options")
        else:
            suggestions.append("Standard risk management procedures should be sufficient")
            suggestions.append("Monitor shipment progress and maintain regular communication")
        
        # Business justification
        business_justification = f"From a business perspective, this {profile.get('level', 'Medium').lower()} risk level suggests "
        if score < 40:
            business_justification += "the shipment can proceed with standard operating procedures and standard insurance coverage."
        elif score < 70:
            business_justification += "enhanced monitoring and moderate contingency planning would be prudent to protect business interests."
        else:
            business_justification += "significant business value is at risk, requiring immediate attention and comprehensive risk mitigation strategies."
        
        return LLMReasoningResult(
            explanation=explanation,
            key_drivers=key_drivers,
            confidence_score=confidence,
            suggestions=suggestions,
            business_justification=business_justification
        )
    
    async def generate_reasoning_llm(self, factors: Dict[str, float],
                                    weights: Dict[str, float],
                                    score: float,
                                    profile: Dict) -> Optional[LLMReasoningResult]:
        """
        Generate reasoning using LLM (Anthropic Claude)
        
        Args:
            factors: Risk factor values
            weights: FAHP weights
            score: Final risk score
            profile: Risk profile dictionary
            
        Returns:
            LLMReasoningResult or None if LLM unavailable
        """
        if not self.anthropic_client:
            return None
        
        # Build prompt (DO NOT leak internal weights or API keys)
        prompt = f"""You are a risk analysis expert. Analyze this shipment risk assessment and provide a clear, business-focused explanation.

Risk Score: {score:.1f}/100
Risk Level: {profile.get('level', 'Medium')}

Top Risk Factors:
"""
        
        # Add top factors (not internal weights)
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)[:5]
        for factor_name, value in sorted_factors:
            # Map technical names to business-friendly names
            friendly_name = {
                "delay": "Delivery delay risk",
                "port": "Port congestion risk",
                "climate": "Weather and climate risk",
                "carrier": "Carrier reliability risk",
                "esg": "ESG and regulatory risk",
                "equipment": "Equipment availability risk",
            }.get(factor_name, factor_name.replace("_", " ").title())
            
            prompt += f"- {friendly_name}: {value:.2f}\n"
        
        prompt += f"""
Impact Matrix: {profile.get('matrix', {}).get('description', 'N/A')}

Provide:
1. A clear explanation of the risk assessment (2-3 sentences)
2. The top 3 key risk drivers
3. Confidence level (0-1) based on data quality
4. 3-4 actionable suggestions to mitigate risk
5. A business justification in executive-friendly language

Format your response clearly and avoid technical jargon. Focus on business impact and actionable insights.
"""
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response (simplified - would need more robust parsing)
            response_text = response.content[0].text
            
            # For now, return deterministic result (LLM integration can be enhanced)
            return self.generate_reasoning_deterministic(factors, weights, score, profile)
            
        except Exception as e:
            # Fallback to deterministic
            return self.generate_reasoning_deterministic(factors, weights, score, profile)
    
    async def generate_reasoning(self, factors: Dict[str, float],
                                weights: Dict[str, float],
                                score: float,
                                profile: Dict) -> LLMReasoningResult:
        """
        Main method to generate reasoning
        
        Args:
            factors: Risk factor values
            weights: FAHP weights
            score: Final risk score
            profile: Risk profile dictionary
            
        Returns:
            LLMReasoningResult object
        """
        if self.use_llm and self.anthropic_client:
            result = await self.generate_reasoning_llm(factors, weights, score, profile)
            if result:
                return result
        
        # Fallback to deterministic
        return self.generate_reasoning_deterministic(factors, weights, score, profile)
    
    def reasoning_to_dict(self, reasoning: LLMReasoningResult) -> Dict:
        """
        Convert reasoning result to dictionary
        
        Args:
            reasoning: LLMReasoningResult object
            
        Returns:
            Dictionary representation
        """
        return {
            "explanation": reasoning.explanation,
            "key_drivers": reasoning.key_drivers,
            "confidence_score": reasoning.confidence_score,
            "suggestions": reasoning.suggestions,
            "business_justification": reasoning.business_justification,
        }
    
    def generate_scenario_explanation_deterministic(self,
                                                   baseline: Dict[str, Any],
                                                   scenario: Dict[str, Any],
                                                   deltas: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate scenario explanation (deterministic fallback)
        
        Args:
            baseline: Baseline result dictionary
            scenario: Scenario result dictionary
            deltas: Delta analysis dictionary
            
        Returns:
            Explanation dictionary
        """
        baseline_score = baseline.get("risk_score", 0)
        scenario_score = scenario.get("simulation_score", scenario.get("risk_score", 0))
        delta = scenario_score - baseline_score
        
        # Build summary
        if abs(delta) < 1:
            summary = "Scenario shows minimal change from baseline risk assessment."
        elif delta > 10:
            summary = f"Scenario indicates significant risk increase (+{delta:.1f} points). "
        elif delta > 5:
            summary = f"Scenario shows moderate risk increase (+{delta:.1f} points). "
        elif delta < -10:
            summary = f"Scenario indicates significant risk reduction ({delta:.1f} points). "
        elif delta < -5:
            summary = f"Scenario shows moderate risk reduction ({delta:.1f} points). "
        else:
            summary = f"Scenario shows slight change ({delta:+.1f} points) from baseline."
        
        # Identify key drivers
        drivers_changed = scenario.get("drivers_changed", [])
        dominant_changes = deltas.get("dominant_factor_changes", [])
        
        driver_explanations = []
        for change in dominant_changes[:3]:
            factor = change.get("factor", "")
            delta_val = change.get("delta", 0)
            
            factor_name = {
                "port": "Port congestion",
                "climate": "Weather conditions",
                "carrier": "Carrier reliability",
                "esg": "ESG compliance",
                "equipment": "Equipment availability",
                "network": "Network dependencies",
                "delay": "Delivery delay risk",
            }.get(factor, factor.replace("_", " ").title())
            
            if delta_val > 0.1:
                driver_explanations.append(f"{factor_name} increased significantly (+{delta_val:.2f})")
            elif delta_val < -0.1:
                driver_explanations.append(f"{factor_name} decreased significantly ({delta_val:.2f})")
        
        # Build impact explanation
        impact = ""
        risk_level_shift = deltas.get("risk_level_shift", "")
        if "→" in risk_level_shift:
            impact = f"Risk level shifted: {risk_level_shift}. "
        
        if delta > 10:
            impact += "This represents a material change that requires attention. "
        elif delta > 5:
            impact += "This change warrants monitoring and may require mitigation actions. "
        
        # Generate recommendations
        recommendations = deltas.get("recommended_mitigations", [])
        
        if not recommendations:
            if delta > 10:
                recommendations = [
                    "Consider alternative routes or carriers to reduce risk",
                    "Increase insurance coverage and contingency planning",
                    "Implement enhanced monitoring and early warning systems"
                ]
            elif delta > 5:
                recommendations = [
                    "Review and strengthen risk mitigation measures",
                    "Monitor key risk factors closely",
                    "Maintain contingency plans ready for activation"
                ]
            elif delta < -5:
                recommendations = [
                    "Risk reduction confirmed - proceed with confidence",
                    "Maintain current mitigation strategies",
                    "Consider optimizing for cost or speed given lower risk"
                ]
            else:
                recommendations = [
                    "Maintain standard risk management procedures",
                    "Continue monitoring as planned"
                ]
        
        return {
            "summary": summary,
            "drivers": driver_explanations,
            "impact": impact,
            "recommendations": recommendations,
            "risk_level_shift": risk_level_shift,
            "score_change": delta,
            "percentage_change": deltas.get("percentage_change", 0)
        }
    
    async def generate_scenario_explanation(self,
                                           baseline: Dict[str, Any],
                                           scenario: Dict[str, Any],
                                           deltas: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate scenario explanation with AI reasoning
        
        Args:
            baseline: Baseline result dictionary
            scenario: Scenario result dictionary
            deltas: Delta analysis dictionary
            
        Returns:
            Explanation dictionary with summary, drivers, impact, recommendations
        """
        # For now, use deterministic (can be enhanced with LLM)
        return self.generate_scenario_explanation_deterministic(baseline, scenario, deltas)
    
    async def generate_region_reasoning(self,
                                       region: str,
                                       lang: str,
                                       profile: Dict[str, Any],
                                       factors: Dict[str, float],
                                       score: float,
                                       region_config: Optional[Dict] = None) -> LLMReasoningResult:
        """
        Generate region-aware reasoning with language support
        
        Args:
            region: Region code (VN, SEA, CN, EU, US, GLOBAL)
            lang: Language code (vi, en, zh)
            profile: Risk profile dictionary
            factors: Risk factor values
            score: Final risk score
            region_config: Optional region configuration
            
        Returns:
            LLMReasoningResult object with region-specific and translated explanations
        """
        # Initialize translator
        translator = Translator(lang)
        
        # Generate base reasoning
        base_result = await self.generate_reasoning(factors, {}, score, profile)
        
        # Add region-specific insights
        region_insights = self._get_region_insights(region, region_config, score, factors, lang)
        
        # Translate and format explanation
        explanation = self._build_region_explanation(
            base_result.explanation,
            region_insights,
            translator,
            lang
        )
        
        # Translate drivers (simplified - would need better mapping)
        translated_drivers = base_result.key_drivers.copy()
        
        # Translate suggestions
        translated_suggestions = base_result.suggestions.copy()
        
        # Translate business justification
        business_just = base_result.business_justification
        
        return LLMReasoningResult(
            explanation=explanation,
            key_drivers=translated_drivers,
            confidence_score=base_result.confidence_score,
            suggestions=translated_suggestions,
            business_justification=business_just
        )
    
    def _get_region_insights(self, region: str, region_config: Optional[Dict],
                            score: float, factors: Dict[str, float], lang: str) -> List[str]:
        """Get region-specific insights"""
        insights = []
        
        if not region_config:
            return insights
        
        # Region-specific patterns
        if region == "SEA":
            if factors.get("climate", 0) > 0.6:
                insights.append("Southwest monsoon typically reduces throughput at major transshipment ports such as Singapore PSA.")
        
        elif region == "CN":
            if factors.get("port", 0) > 0.7:
                insights.append("Golden Week causes predictable congestion spikes in Ningbo, Shanghai, and Shenzhen.")
        
        elif region == "US":
            if factors.get("port", 0) > 0.6:
                insights.append("ILWU labor negotiations can cause volatility at LA/LB terminals.")
        
        elif region == "EU":
            if factors.get("port", 0) > 0.5:
                insights.append("Port strikes are common, especially at major hubs like Rotterdam, Hamburg, and Antwerp.")
        
        # Add characteristics
        characteristics = region_config.get("characteristics", [])
        insights.extend(characteristics[:2])
        
        return insights
    
    def _build_region_explanation(self, base_explanation: str, region_insights: List[str],
                                  translator: Translator, lang: str) -> str:
        """Build region-aware explanation"""
        parts = [base_explanation]
        if region_insights:
            parts.append(" ")
            parts.extend(region_insights)
        return " ".join(parts)


