"""
RISKCAST Engine v2 - Risk Profile and Impact Matrix
Creates comprehensive risk profile with probability, severity, and quadrant analysis
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class RiskLevel(Enum):
    """Risk level classification"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ProbabilityLevel(Enum):
    """Probability level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SeverityLevel(Enum):
    """Severity level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ImpactMatrix:
    """Risk impact matrix"""
    probability: str  # "low", "medium", "high"
    severity: str     # "low", "medium", "high"
    quadrant: int     # 1-9 (3x3 matrix)
    description: str  # Human-readable description


@dataclass
class RiskProfile:
    """Comprehensive risk profile"""
    score: float  # 0-100
    level: str    # "Low", "Medium", "High", "Critical"
    confidence: float  # 0-1
    explanation: List[str]  # Explanation points
    factors: Dict[str, float]  # Risk factor breakdown
    matrix: ImpactMatrix  # Impact matrix
    drivers: List[str]    # Key risk drivers
    recommendations: List[str]  # Risk mitigation recommendations


class RiskProfileBuilder:
    """Builder for risk profiles"""
    RISK_LEVEL_THRESHOLDS = {
        RiskLevel.LOW: (0, 30),
        RiskLevel.MEDIUM: (30, 60),
        RiskLevel.HIGH: (60, 80),
        RiskLevel.CRITICAL: (80, 100),
    }
    PROBABILITY_THRESHOLDS = {
        ProbabilityLevel.LOW: (0, 0.4),
        ProbabilityLevel.MEDIUM: (0.4, 0.7),
        ProbabilityLevel.HIGH: (0.7, 1.0),
    }
    SEVERITY_THRESHOLDS = {
        SeverityLevel.LOW: (0, 40),
        SeverityLevel.MEDIUM: (40, 70),
        SeverityLevel.HIGH: (70, 100),
    }
    
    def __init__(self):
        """Initialize risk profile builder"""
        pass
    
    def determine_risk_level(self, score: float) -> RiskLevel:
        """
        Determine risk level from score
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            RiskLevel enum
        """
        if score < 30:
            return RiskLevel.LOW
        elif score < 60:
            return RiskLevel.MEDIUM
        elif score < 80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def determine_probability(self, score: float, factors: Dict[str, float]) -> ProbabilityLevel:
        """
        Determine probability level
        
        Args:
            score: Risk score
            factors: Risk factor breakdown
            
        Returns:
            ProbabilityLevel enum
        """
        # Use score as base, adjust based on factors
        probability_score = score / 100.0
        
        # Adjust based on variability in factors (high variance = higher uncertainty)
        if factors:
            factor_values = list(factors.values())
            variance = sum((v - sum(factor_values) / len(factor_values)) ** 2 for v in factor_values) / len(factor_values)
            # Higher variance = slightly lower probability confidence
            probability_score *= (1.0 - min(0.2, variance))
        
        if probability_score < 0.4:
            return ProbabilityLevel.LOW
        elif probability_score < 0.7:
            return ProbabilityLevel.MEDIUM
        else:
            return ProbabilityLevel.HIGH
    
    def determine_severity(self, score: float, operational_inputs: Dict) -> SeverityLevel:
        """
        Determine severity level
        
        Args:
            score: Risk score
            operational_inputs: Operational inputs (for cargo value, etc.)
            
        Returns:
            SeverityLevel enum
        """
        # Severity based on score and impact magnitude
        severity_score = score
        
        # Adjust based on cargo value (higher value = higher severity)
        cargo_value = operational_inputs.get("cargo_value", 0)
        if cargo_value > 500000:  # High value cargo
            severity_score = min(100, severity_score * 1.1)
        elif cargo_value > 100000:  # Medium value
            severity_score = min(100, severity_score * 1.05)
        
        if severity_score < 40:
            return SeverityLevel.LOW
        elif severity_score < 70:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.HIGH
    
    def compute_quadrant(self, probability: ProbabilityLevel, severity: SeverityLevel) -> int:
        """
        Compute quadrant in 3x3 matrix
        
        Args:
            probability: Probability level
            severity: Severity level
            
        Returns:
            Quadrant number (1-9)
        """
        prob_map = {
            ProbabilityLevel.LOW: 1,
            ProbabilityLevel.MEDIUM: 2,
            ProbabilityLevel.HIGH: 3,
        }
        
        sev_map = {
            SeverityLevel.LOW: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.HIGH: 3,
        }
        
        prob_idx = prob_map[probability]
        sev_idx = sev_map[severity]
        
        # Quadrant: (probability-1) * 3 + severity
        quadrant = (prob_idx - 1) * 3 + sev_idx
        
        return quadrant
    
    def get_quadrant_description(self, quadrant: int) -> str:
        """
        Get human-readable quadrant description
        
        Args:
            quadrant: Quadrant number (1-9)
            
        Returns:
            Description string
        """
        descriptions = {
            1: "Low probability, low severity - Minimal risk",
            2: "Low probability, medium severity - Moderate risk, monitor",
            3: "Low probability, high severity - Low likelihood but high impact if occurs",
            4: "Medium probability, low severity - Moderate risk, standard precautions",
            5: "Medium probability, medium severity - Moderate risk, enhanced monitoring",
            6: "Medium probability, high severity - Significant risk, active mitigation needed",
            7: "High probability, low severity - Frequent but manageable issues",
            8: "High probability, medium severity - High risk, immediate action required",
            9: "High probability, high severity - Critical risk, urgent mitigation essential",
        }
        
        return descriptions.get(quadrant, "Unknown risk profile")
    
    def identify_key_drivers(self, factors: Dict[str, float], top_n: int = 3) -> List[str]:
        """
        Identify key risk drivers
        
        Args:
            factors: Risk factor breakdown
            top_n: Number of top drivers to identify
            
        Returns:
            List of driver names
        """
        if not factors:
            return []
        
        # Sort by value (descending)
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
        
        # Get top N
        drivers = [factor_name for factor_name, _ in sorted_factors[:top_n]]
        
        return drivers
    
    def generate_explanation(self, score: float, level: RiskLevel, factors: Dict[str, float],
                            components: Dict[str, float]) -> List[str]:
        """
        Generate explanation points
        
        Args:
            score: Risk score
            level: Risk level
            factors: Risk factor breakdown
            components: Score components
            
        Returns:
            List of explanation strings
        """
        explanation = []
        
        explanation.append(f"Overall risk score: {score:.1f}/100 ({level.value} risk)")
        
        # Top contributing factors
        if factors:
            top_factor = max(factors.items(), key=lambda x: x[1])
            explanation.append(f"Primary risk driver: {top_factor[0]} ({top_factor[1]:.2f})")
        
        # Component breakdown
        if "climate" in components:
            explanation.append(f"Climate risk contributes {components['climate']:.1%} to overall score")
        
        if "network" in components:
            explanation.append(f"Network risk contributes {components['network']:.1%} to overall score")
        
        return explanation
    
    def generate_recommendations(self, level: RiskLevel, drivers: List[str],
                                factors: Dict[str, float]) -> List[str]:
        """
        Generate risk mitigation recommendations
        
        Args:
            level: Risk level
            drivers: Key risk drivers
            factors: Risk factor breakdown
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Level-based recommendations
        if level == RiskLevel.CRITICAL:
            recommendations.append("URGENT: Implement comprehensive risk mitigation plan immediately")
            recommendations.append("Consider alternative routes or carriers if available")
            recommendations.append("Increase insurance coverage for high-value cargo")
        
        elif level == RiskLevel.HIGH:
            recommendations.append("Implement enhanced monitoring and contingency planning")
            recommendations.append("Review carrier reliability and network redundancy")
            recommendations.append("Consider risk insurance or hedging strategies")
        
        elif level == RiskLevel.MEDIUM:
            recommendations.append("Monitor shipment progress closely")
            recommendations.append("Ensure adequate insurance coverage")
            recommendations.append("Maintain communication with logistics partners")
        
        else:  # LOW
            recommendations.append("Standard monitoring and procedures sufficient")
            recommendations.append("Maintain regular check-ins with carrier")
        
        # Driver-specific recommendations
        if "climate" in drivers:
            recommendations.append("Monitor weather forecasts and adjust schedule if needed")
        
        if "network" in drivers or "port" in drivers:
            recommendations.append("Monitor port congestion and consider alternative ports")
        
        if "carrier" in drivers:
            recommendations.append("Review carrier performance metrics and consider alternatives")
        
        return recommendations
    
    def build_profile(self, score: float, factors: Dict[str, float],
                     components: Dict[str, float],
                     operational_inputs: Dict,
                     confidence: float = 0.8) -> RiskProfile:
        """
        Build comprehensive risk profile
        
        Args:
            score: Final risk score (0-100)
            factors: Risk factor breakdown
            components: Score component breakdown
            operational_inputs: Operational inputs
            confidence: Confidence score (0-1)
            
        Returns:
            RiskProfile object
        """
        # Determine risk level
        level = self.determine_risk_level(score)
        
        # Determine probability and severity
        probability = self.determine_probability(score, factors)
        severity = self.determine_severity(score, operational_inputs)
        
        # Compute quadrant
        quadrant = self.compute_quadrant(probability, severity)
        quadrant_desc = self.get_quadrant_description(quadrant)
        
        # Create impact matrix
        impact_matrix = ImpactMatrix(
            probability=probability.value,
            severity=severity.value,
            quadrant=quadrant,
            description=quadrant_desc
        )
        
        # Identify key drivers
        drivers = self.identify_key_drivers(factors, top_n=3)
        
        # Generate explanation
        explanation = self.generate_explanation(score, level, factors, components)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(level, drivers, factors)
        
        # Build profile
        profile = RiskProfile(
            score=score,
            level=level.value,
            confidence=confidence,
            explanation=explanation,
            factors=factors,
            matrix=impact_matrix,
            drivers=drivers,
            recommendations=recommendations
        )
        
        return profile
    
    def profile_to_dict(self, profile: RiskProfile) -> Dict:
        """
        Convert risk profile to dictionary (for JSON serialization)
        
        Args:
            profile: RiskProfile object
            
        Returns:
            Dictionary representation
        """
        return {
            "score": profile.score,
            "level": profile.level,
            "confidence": profile.confidence,
            "explanation": profile.explanation,
            "factors": profile.factors,
            "matrix": {
                "probability": profile.matrix.probability,
                "severity": profile.matrix.severity,
                "quadrant": profile.matrix.quadrant,
                "description": profile.matrix.description,
            },
            "drivers": profile.drivers,
            "recommendations": profile.recommendations,
        }
















