"""
AI System Advisor - Action Handlers
Execute system actions requested by AI
"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid

# Lazy imports to avoid dependency issues
try:
    from app.core.report.pdf_builder import PDFBuilder
    PDF_BUILDER_AVAILABLE = True
except ImportError:
    PDF_BUILDER_AVAILABLE = False
    PDFBuilder = None

try:
    from app.core.scenario_engine.simulation_engine import SimulationEngine
    from app.core.scenario_engine.delta_engine import DeltaEngine
    SCENARIO_ENGINE_AVAILABLE = True
except ImportError:
    SCENARIO_ENGINE_AVAILABLE = False
    SimulationEngine = None
    DeltaEngine = None

from app.core.engine_state import get_last_result_v2
from app.ai_system_advisor.data_access import DataAccess


class ActionHandlers:
    """Handles system actions"""
    
    def __init__(self):
        """Initialize action handlers"""
        self.data_access = DataAccess()
        
        # Initialize engines if available
        if SCENARIO_ENGINE_AVAILABLE:
            self.simulation_engine = SimulationEngine()
            self.delta_engine = DeltaEngine()
        else:
            self.simulation_engine = None
            self.delta_engine = None
        
        # File storage for exports
        root_dir = Path(__file__).resolve().parent.parent.parent
        self.export_storage = root_dir / "data" / "exports"
        self.export_storage.mkdir(parents=True, exist_ok=True)
    
    async def export_pdf(
        self,
        session_id: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Export current risk assessment to PDF
        
        Args:
            session_id: Session identifier
            options: Export options
            
        Returns:
            Export result with file information
        """
        try:
            # Get current assessment
            assessment = self.data_access.get_current_risk_assessment(session_id)
            if not assessment:
                return {
                    "success": False,
                    "error": "No risk assessment available"
                }
            
            # Get options
            template = options.get("template", "standard")
            include_charts = options.get("include_charts", True)
            language = options.get("language", "en")
            
            # Generate PDF (using existing PDF builder if available)
            if PDF_BUILDER_AVAILABLE and PDFBuilder:
                try:
                    pdf_builder = PDFBuilder()
                    pdf_content = await pdf_builder.build_report(
                        assessment,
                        template=template,
                        include_charts=include_charts,
                        language=language
                    )
                except Exception as e:
                    # Fallback: create simple PDF
                    print(f"[ActionHandlers] PDF builder error, using fallback: {e}")
                    pdf_content = self._create_simple_pdf(assessment, language)
            else:
                # PDF builder not available
                pdf_content = self._create_simple_pdf(assessment, language)
            
            # Save file
            file_id = f"pdf-{uuid.uuid4().hex[:8]}"
            file_path = self.export_storage / f"{file_id}.pdf"
            file_path.write_bytes(pdf_content)
            
            return {
                "success": True,
                "file_id": file_id,
                "file_url": f"/api/v1/ai/advisor/downloads/{file_id}.pdf",
                "file_size": len(pdf_content),
                "expires_at": None  # TODO: Implement expiry
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def export_excel(
        self,
        session_id: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Export to Excel format
        
        Args:
            session_id: Session identifier
            options: Export options
            
        Returns:
            Export result
        """
        try:
            assessment = self.data_access.get_current_risk_assessment(session_id)
            if not assessment:
                return {
                    "success": False,
                    "error": "No risk assessment available"
                }
            
            # TODO: Implement Excel export using openpyxl or similar
            # For now, return placeholder
            return {
                "success": False,
                "error": "Excel export not yet implemented"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def compare_shipments(
        self,
        shipment_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple shipments
        
        Args:
            shipment_ids: List of shipment IDs to compare
            
        Returns:
            Comparison result
        """
        try:
            if len(shipment_ids) < 2:
                return {
                    "success": False,
                    "error": "Need at least 2 shipments to compare"
                }
            
            # TODO: Load shipments from storage/database
            # For now, return placeholder
            return {
                "success": False,
                "error": "Shipment comparison not yet implemented (requires historical data storage)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_scenario(
        self,
        session_id: str,
        scenario_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run what-if scenario
        
        Args:
            session_id: Session identifier
            scenario_type: Type of scenario
            parameters: Scenario parameters
            
        Returns:
            Scenario result
        """
        try:
            # Get baseline assessment
            baseline = self.data_access.get_current_risk_assessment(session_id)
            if not baseline:
                return {
                    "success": False,
                    "error": "No baseline assessment available"
                }
            
            # Build scenario context
            scenario_context = {
                "scenario_type": scenario_type,
                "parameters": parameters or {}
            }
            
            # Run scenario using scenario engine
            if not SCENARIO_ENGINE_AVAILABLE or not self.simulation_engine:
                return {
                    "success": False,
                    "error": "Scenario engine not available"
                }
            
            try:
                scenario_result = self.simulation_engine.run_scenario(
                    baseline,
                    scenario_context
                )
                
                # Calculate deltas
                if self.delta_engine:
                    deltas = self.delta_engine.calculate_deltas(
                        baseline,
                        scenario_result
                    )
                else:
                    deltas = {"score_delta": scenario_result.get('risk_score', 0) - baseline.get('risk_score', 0)}
                
                return {
                    "success": True,
                    "scenario_type": scenario_type,
                    "baseline_score": baseline.get('risk_score', 0),
                    "scenario_score": scenario_result.get('risk_score', 0),
                    "delta": deltas.get('score_delta', 0),
                    "deltas": deltas
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Scenario execution failed: {str(e)}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_recommendations(
        self,
        session_id: str,
        limit: int = 5,
        sort_by: str = "risk_reduction"
    ) -> Dict[str, Any]:
        """
        Get mitigation recommendations
        
        Args:
            session_id: Session identifier
            limit: Maximum recommendations
            sort_by: Sort order
            
        Returns:
            Recommendations result
        """
        try:
            assessment = self.data_access.get_current_risk_assessment(session_id)
            if not assessment:
                return {
                    "success": False,
                    "error": "No risk assessment available"
                }
            
            # Get scenarios (which contain recommendations)
            scenarios = assessment.get('scenarios', [])
            
            if not scenarios:
                # Generate basic recommendations from risk drivers
                recommendations = self._generate_basic_recommendations(assessment)
            else:
                recommendations = scenarios[:limit]
            
            # Sort if needed
            if sort_by == "risk_reduction":
                recommendations.sort(key=lambda x: x.get('riskReduction', 0), reverse=True)
            elif sort_by == "cost_benefit":
                # Sort by risk_reduction / cost_impact
                recommendations.sort(
                    key=lambda x: x.get('riskReduction', 0) / max(x.get('costImpact', 1), 1),
                    reverse=True
                )
            elif sort_by == "feasibility":
                recommendations.sort(key=lambda x: x.get('feasibility', 0), reverse=True)
            
            return {
                "success": True,
                "recommendations": recommendations[:limit]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_function(
        self,
        function_name: str,
        function_args: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Execute a function call
        
        Args:
            function_name: Function name
            function_args: Function arguments
            session_id: Session identifier
            
        Returns:
            Function execution result
        """
        try:
            if function_name == "export_pdf":
                return await self.export_pdf(session_id, function_args)
            elif function_name == "export_excel":
                return await self.export_excel(session_id, function_args)
            elif function_name == "compare_shipments":
                return await self.compare_shipments(function_args.get("shipment_ids", []))
            elif function_name == "run_scenario":
                return await self.run_scenario(
                    session_id,
                    function_args.get("scenario_type"),
                    function_args.get("parameters")
                )
            elif function_name == "get_recommendations":
                return await self.get_recommendations(
                    session_id,
                    limit=function_args.get("limit", 5),
                    sort_by=function_args.get("sort_by", "risk_reduction")
                )
            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {function_name}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_simple_pdf(self, assessment: Dict[str, Any], language: str) -> bytes:
        """Create simple PDF as fallback"""
        # Simple text-based PDF placeholder
        # In production, this would generate a basic PDF
        try:
            # Try to use reportlab if available
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            import io
            
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.drawString(100, 750, "RISKCAST Risk Assessment Report")
            p.drawString(100, 730, f"Risk Score: {assessment.get('risk_score', 'N/A')}")
            p.save()
            buffer.seek(0)
            return buffer.getvalue()
        except ImportError:
            # If reportlab not available, return placeholder
            return b"%PDF-1.4\n%PDF placeholder - reportlab not installed"
    
    def _generate_basic_recommendations(self, assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate basic recommendations from assessment"""
        recommendations = []
        
        risk_score = assessment.get('risk_score', 0) or \
                    assessment.get('profile', {}).get('score', 0) or \
                    assessment.get('overview', {}).get('riskScore', {}).get('score', 0)
        
        if risk_score >= 70:
            recommendations.append({
                "title": "Immediate Risk Mitigation",
                "description": "High risk detected - consider alternative routes or carriers",
                "riskReduction": 10.0,
                "costImpact": 2000.0,
                "feasibility": 0.8
            })
            recommendations.append({
                "title": "Enhanced Insurance Coverage",
                "description": "Increase insurance coverage for high-risk shipment",
                "riskReduction": 5.0,
                "costImpact": 1500.0,
                "feasibility": 0.95
            })
        elif risk_score >= 40:
            recommendations.append({
                "title": "Enhanced Monitoring",
                "description": "Add real-time tracking and alerts",
                "riskReduction": 3.0,
                "costImpact": 500.0,
                "feasibility": 0.9
            })
        
        return recommendations
