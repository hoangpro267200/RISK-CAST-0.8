"""
AI System Advisor - Summarizer
Generate executive summaries
"""

from typing import Dict, List, Optional, Any


class Summarizer:
    """Generates executive summaries"""
    
    def __init__(self):
        """Initialize summarizer"""
        pass
    
    def generate_executive_summary(
        self,
        risk_assessment: Dict[str, Any],
        language: str = "en",
        length: str = "medium"
    ) -> str:
        """
        Generate executive summary
        
        Args:
            risk_assessment: Risk assessment dictionary
            language: Language code (en, vi, zh)
            length: Summary length (short, medium, long)
            
        Returns:
            Executive summary string
        """
        # TODO: Add translation support when Translator is available
        
        # Extract key data
        risk_score = risk_assessment.get('risk_score', 0) or \
                    risk_assessment.get('profile', {}).get('score', 0) or \
                    risk_assessment.get('overview', {}).get('riskScore', {}).get('score', 0)
        
        risk_level = risk_assessment.get('risk_level') or \
                    risk_assessment.get('profile', {}).get('level') or \
                    risk_assessment.get('overview', {}).get('riskScore', {}).get('level', 'Unknown')
        
        drivers = risk_assessment.get('drivers', [])
        financial = risk_assessment.get('loss', {})
        expected_loss = financial.get('expectedLoss', financial.get('expected_loss', 0))
        
        shipment = risk_assessment.get('shipment') or \
                  risk_assessment.get('overview', {}).get('shipment', {})
        pol = shipment.get('pol') or shipment.get('pol_code', 'N/A')
        pod = shipment.get('pod') or shipment.get('pod_code', 'N/A')
        
        # Build summary based on length
        if length == "short":
            summary = self._generate_short_summary(risk_score, risk_level, pol, pod, expected_loss, drivers)
        elif length == "long":
            summary = self._generate_long_summary(risk_assessment, risk_score, risk_level, pol, pod, expected_loss, drivers)
        else:  # medium
            summary = self._generate_medium_summary(risk_score, risk_level, pol, pod, expected_loss, drivers)
        
        # Translate if needed
        if language != "en":
            # Simple translation (would use translator in production)
            pass
        
        return summary
    
    def _generate_short_summary(
        self,
        risk_score: float,
        risk_level: str,
        pol: str,
        pod: str,
        expected_loss: float,
        drivers: List[Dict]
    ) -> str:
        """Generate short summary (1-2 sentences)"""
        summary = f"Shipment from {pol} to {pod} has a {risk_level} risk level (score: {risk_score:.1f}/100)."
        
        if expected_loss > 0:
            summary += f" Expected financial loss: ${expected_loss:,.0f}."
        
        if drivers:
            top_driver = drivers[0]
            summary += f" Primary concern: {top_driver.get('name', 'Unknown')} ({top_driver.get('impact', 0):.1f}% impact)."
        
        return summary
    
    def _generate_medium_summary(
        self,
        risk_score: float,
        risk_level: str,
        pol: str,
        pod: str,
        expected_loss: float,
        drivers: List[Dict]
    ) -> str:
        """Generate medium summary (3-5 sentences)"""
        summary = f"Risk Assessment Summary:\n\n"
        summary += f"Shipment Route: {pol} → {pod}\n"
        summary += f"Overall Risk: {risk_level} ({risk_score:.1f}/100)\n\n"
        
        if expected_loss > 0:
            summary += f"Financial Impact: Expected loss of ${expected_loss:,.0f} based on current risk profile.\n\n"
        
        if drivers:
            summary += "Key Risk Drivers:\n"
            for i, driver in enumerate(drivers[:3], 1):
                summary += f"{i}. {driver.get('name', 'Unknown')}: {driver.get('impact', 0):.1f}% impact\n"
            summary += "\n"
        
        if risk_score >= 70:
            summary += "Recommendation: Immediate action required. Consider alternative routes, enhanced insurance, and comprehensive monitoring."
        elif risk_score >= 40:
            summary += "Recommendation: Enhanced monitoring and standard insurance coverage recommended."
        else:
            summary += "Recommendation: Standard procedures sufficient. Continue monitoring as planned."
        
        return summary
    
    def _generate_long_summary(
        self,
        risk_assessment: Dict[str, Any],
        risk_score: float,
        risk_level: str,
        pol: str,
        pod: str,
        expected_loss: float,
        drivers: List[Dict]
    ) -> str:
        """Generate long summary (detailed)"""
        summary = f"EXECUTIVE RISK ASSESSMENT SUMMARY\n"
        summary += "=" * 50 + "\n\n"
        
        # Shipment Overview
        summary += "SHIPMENT OVERVIEW\n"
        summary += f"Route: {pol} → {pod}\n"
        shipment = risk_assessment.get('shipment') or risk_assessment.get('overview', {}).get('shipment', {})
        if shipment.get('etd'):
            summary += f"ETD: {shipment.get('etd')}\n"
        if shipment.get('eta'):
            summary += f"ETA: {shipment.get('eta')}\n"
        summary += "\n"
        
        # Risk Assessment
        summary += "RISK ASSESSMENT\n"
        summary += f"Overall Risk Score: {risk_score:.1f}/100\n"
        summary += f"Risk Level: {risk_level}\n"
        confidence = risk_assessment.get('confidence') or \
                    risk_assessment.get('profile', {}).get('confidence') or \
                    risk_assessment.get('overview', {}).get('riskScore', {}).get('confidence', 0)
        if confidence:
            summary += f"Confidence: {confidence}%\n"
        summary += "\n"
        
        # Financial Impact
        if expected_loss > 0:
            summary += "FINANCIAL IMPACT\n"
            summary += f"Expected Loss: ${expected_loss:,.0f}\n"
            financial = risk_assessment.get('loss', {})
            var95 = financial.get('p95', financial.get('var95', 0))
            cvar99 = financial.get('p99', financial.get('cvar99', 0))
            if var95 > 0:
                summary += f"VaR 95%: ${var95:,.0f}\n"
            if cvar99 > 0:
                summary += f"CVaR 99%: ${cvar99:,.0f}\n"
            summary += "\n"
        
        # Risk Drivers
        if drivers:
            summary += "PRIMARY RISK DRIVERS\n"
            for i, driver in enumerate(drivers[:5], 1):
                summary += f"{i}. {driver.get('name', 'Unknown')}\n"
                summary += f"   Impact: {driver.get('impact', 0):.1f}%\n"
                if driver.get('description'):
                    summary += f"   {driver.get('description')}\n"
            summary += "\n"
        
        # Recommendations
        summary += "RECOMMENDATIONS\n"
        if risk_score >= 70:
            summary += "1. Immediate action required - consider alternative routes or carriers\n"
            summary += "2. Increase insurance coverage to protect against financial loss\n"
            summary += "3. Implement comprehensive monitoring and early warning systems\n"
        elif risk_score >= 40:
            summary += "1. Enhanced monitoring recommended\n"
            summary += "2. Standard insurance coverage sufficient\n"
            summary += "3. Maintain contingency plans ready\n"
        else:
            summary += "1. Continue with standard procedures\n"
            summary += "2. Monitor shipment progress\n"
            summary += "3. No immediate action required\n"
        
        return summary
    
    def generate_comparative_summary(
        self,
        shipments: List[Dict[str, Any]]
    ) -> str:
        """
        Generate comparative summary for multiple shipments
        
        Args:
            shipments: List of shipment assessments
            
        Returns:
            Comparative summary string
        """
        if len(shipments) < 2:
            return "Need at least 2 shipments to compare."
        
        summary = "SHIPMENT COMPARISON SUMMARY\n"
        summary += "=" * 50 + "\n\n"
        
        # Compare key metrics
        risk_scores = []
        expected_losses = []
        
        for i, shipment in enumerate(shipments, 1):
            risk_score = shipment.get('risk_score', 0) or \
                        shipment.get('profile', {}).get('score', 0)
            financial = shipment.get('loss', {})
            expected_loss = financial.get('expectedLoss', financial.get('expected_loss', 0))
            
            risk_scores.append(risk_score)
            expected_losses.append(expected_loss)
            
            shipment_data = shipment.get('shipment') or shipment.get('overview', {}).get('shipment', {})
            pol = shipment_data.get('pol') or shipment_data.get('pol_code', 'N/A')
            pod = shipment_data.get('pod') or shipment_data.get('pod_code', 'N/A')
            
            summary += f"Shipment {i}: {pol} → {pod}\n"
            summary += f"  Risk Score: {risk_score:.1f}/100\n"
            if expected_loss > 0:
                summary += f"  Expected Loss: ${expected_loss:,.0f}\n"
            summary += "\n"
        
        # Analysis
        if risk_scores:
            avg_risk = sum(risk_scores) / len(risk_scores)
            min_risk = min(risk_scores)
            max_risk = max(risk_scores)
            
            summary += "ANALYSIS\n"
            summary += f"Average Risk Score: {avg_risk:.1f}/100\n"
            summary += f"Lowest Risk: {min_risk:.1f}/100\n"
            summary += f"Highest Risk: {max_risk:.1f}/100\n"
            
            if max_risk - min_risk > 20:
                summary += "\nSignificant risk variation detected. Review highest risk shipment for mitigation opportunities.\n"
        
        return summary
    
    def generate_trend_summary(
        self,
        historical_data: List[Dict[str, Any]]
    ) -> str:
        """
        Generate trend summary from historical data
        
        Args:
            historical_data: List of historical assessments
            
        Returns:
            Trend summary string
        """
        if len(historical_data) < 2:
            return "Insufficient historical data for trend analysis."
        
        summary = "HISTORICAL RISK TREND\n"
        summary += "=" * 50 + "\n\n"
        
        # Extract risk scores over time
        risk_scores = []
        dates = []
        
        for data in historical_data:
            risk_score = data.get('risk_score', 0) or \
                        data.get('profile', {}).get('score', 0)
            timestamp = data.get('timestamp') or data.get('created_at', '')
            
            risk_scores.append(risk_score)
            dates.append(timestamp)
        
        if risk_scores:
            avg_risk = sum(risk_scores) / len(risk_scores)
            first_risk = risk_scores[0]
            last_risk = risk_scores[-1]
            trend = last_risk - first_risk
            
            summary += f"Period: {len(historical_data)} assessments\n"
            summary += f"Average Risk: {avg_risk:.1f}/100\n"
            summary += f"First Assessment: {first_risk:.1f}/100\n"
            summary += f"Latest Assessment: {last_risk:.1f}/100\n"
            summary += f"Trend: {trend:+.1f} points\n\n"
            
            if trend > 5:
                summary += "TREND: Increasing risk over time. Review recent changes and consider mitigation actions.\n"
            elif trend < -5:
                summary += "TREND: Decreasing risk over time. Risk management measures appear effective.\n"
            else:
                summary += "TREND: Stable risk level. Continue current risk management approach.\n"
        
        return summary
