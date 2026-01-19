"""
AI System Advisor - Data Access
Reads system data (engine outputs, history, metrics)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.core.engine_state import get_last_result_v2
from app.core.state_storage import load_state
from app.memory import memory_system
from app.ai_system_advisor.types import SystemContext


class DataAccess:
    """Accesses system data for AI advisor"""
    
    def __init__(self):
        """Initialize data access"""
        pass
    
    def get_current_risk_assessment(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get current risk assessment from engine
        
        Args:
            session_id: Session identifier (used for context, not directly)
            
        Returns:
            Risk assessment dictionary or None
        """
        try:
            # Get last result from engine state
            result = get_last_result_v2()
            
            if not result or not isinstance(result, dict):
                return None
            
            # Return normalized result
            return result
        except Exception as e:
            print(f"[DataAccess] Error getting risk assessment: {e}")
            return None
    
    def get_financial_metrics(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get financial metrics from current assessment
        
        Args:
            session_id: Session identifier
            
        Returns:
            Financial metrics dictionary
        """
        assessment = self.get_current_risk_assessment(session_id)
        
        if not assessment:
            return None
        
        # Extract financial metrics
        loss = assessment.get('loss')
        if not loss:
            return None
        
        return {
            'expected_loss': loss.get('expectedLoss', loss.get('expected_loss', 0)),
            'var95': loss.get('p95', loss.get('var95', 0)),
            'cvar99': loss.get('p99', loss.get('cvar99', 0)),
            'tail_contribution': loss.get('tailContribution', loss.get('tail_contribution', 0))
        }
    
    def get_esg_metrics(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get ESG metrics from current assessment
        
        Args:
            session_id: Session identifier
            
        Returns:
            ESG metrics dictionary
        """
        assessment = self.get_current_risk_assessment(session_id)
        
        if not assessment:
            return None
        
        # Extract ESG metrics if available
        esg = assessment.get('esg') or assessment.get('esg_score')
        if not esg:
            return None
        
        if isinstance(esg, dict):
            return esg
        elif isinstance(esg, (int, float)):
            return {'esg_score': esg}
        
        return None
    
    def get_shipment_data(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get shipment data from current assessment or state
        
        Args:
            session_id: Session identifier
            
        Returns:
            Shipment data dictionary
        """
        # Try from assessment first
        assessment = self.get_current_risk_assessment(session_id)
        if assessment:
            shipment = assessment.get('shipment') or assessment.get('overview', {}).get('shipment')
            if shipment:
                return shipment
        
        # Fallback: try state storage
        try:
            # Try to get from memory system
            latest_shipment = memory_system.get('latest_shipment')
            if latest_shipment:
                return latest_shipment
        except Exception:
            pass
        
        return None
    
    def get_scenario_results(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get scenario analysis results
        
        Args:
            session_id: Session identifier
            
        Returns:
            Scenario results dictionary
        """
        assessment = self.get_current_risk_assessment(session_id)
        
        if not assessment:
            return None
        
        # Extract scenario data
        scenarios = assessment.get('scenarios') or assessment.get('riskScenarioProjections')
        if scenarios:
            return {
                'scenarios': scenarios,
                'projections': assessment.get('riskScenarioProjections', [])
            }
        
        return None
    
    def get_historical_shipments(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get historical shipment data
        
        Args:
            session_id: Session identifier
            limit: Maximum number of shipments to return
            
        Returns:
            List of historical shipment dictionaries
        """
        # TODO: Implement when historical data storage is available
        # For now, return empty list
        return []
    
    def get_system_context(
        self,
        session_id: str,
        page_context: Optional[Dict[str, Any]] = None
    ) -> SystemContext:
        """
        Get complete system context for session
        
        Args:
            session_id: Session identifier
            page_context: Optional page context from frontend
            
        Returns:
            SystemContext object
        """
        # Get all data
        assessment = self.get_current_risk_assessment(session_id)
        shipment = self.get_shipment_data(session_id)
        financial = self.get_financial_metrics(session_id)
        esg = self.get_esg_metrics(session_id)
        scenarios = self.get_scenario_results(session_id)
        history = self.get_historical_shipments(session_id, limit=5)
        
        # Determine available actions
        available_actions = [
            'export_pdf',
            'export_excel',
            'get_recommendations',
            'get_summary'
        ]
        
        if scenarios:
            available_actions.append('run_scenario')
        
        if len(history) > 0:
            available_actions.append('compare_shipments')
        
        return SystemContext(
            session_id=session_id,
            current_assessment=assessment,
            shipment=shipment,
            financial_metrics=financial,
            esg_metrics=esg,
            scenario_results=scenarios,
            historical_data=history,
            available_actions=available_actions
        )
    
    def format_context_for_prompt(
        self,
        context: SystemContext
    ) -> str:
        """
        Format system context for LLM prompt
        
        Args:
            context: SystemContext object
            
        Returns:
            Formatted context string
        """
        parts = []
        
        # Current assessment
        if context.current_assessment:
            risk_score = context.current_assessment.get('risk_score') or \
                        context.current_assessment.get('profile', {}).get('score') or \
                        context.current_assessment.get('overview', {}).get('riskScore', {}).get('score')
            risk_level = context.current_assessment.get('risk_level') or \
                        context.current_assessment.get('profile', {}).get('level') or \
                        context.current_assessment.get('overview', {}).get('riskScore', {}).get('level')
            
            if risk_score is not None:
                parts.append(f"Current Risk Assessment:")
                parts.append(f"- Risk Score: {risk_score:.1f}/100")
                if risk_level:
                    parts.append(f"- Risk Level: {risk_level}")
        
        # Shipment info
        if context.shipment:
            pol = context.shipment.get('pol') or context.shipment.get('pol_code') or context.shipment.get('origin')
            pod = context.shipment.get('pod') or context.shipment.get('pod_code') or context.shipment.get('destination')
            if pol and pod:
                parts.append(f"Shipment Route: {pol} → {pod}")
        
        # Financial metrics
        if context.financial_metrics:
            el = context.financial_metrics.get('expected_loss', 0)
            var95 = context.financial_metrics.get('var95', 0)
            if el > 0:
                parts.append(f"Financial Metrics:")
                parts.append(f"- Expected Loss: ${el:,.0f}")
                if var95 > 0:
                    parts.append(f"- VaR 95%: ${var95:,.0f}")
        
        # Drivers
        if context.current_assessment:
            drivers = context.current_assessment.get('drivers') or []
            if drivers and len(drivers) > 0:
                parts.append(f"Top Risk Drivers:")
                for i, driver in enumerate(drivers[:3], 1):
                    name = driver.get('name', 'Unknown')
                    impact = driver.get('impact', 0)
                    parts.append(f"{i}. {name}: {impact:.1f}% impact")
        
        # Available actions
        if context.available_actions:
            parts.append(f"Available Actions: {', '.join(context.available_actions)}")
        
        return "\n".join(parts) if parts else "No current assessment data available."
