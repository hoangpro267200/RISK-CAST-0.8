"""
AI System Advisor - Function Registry
Defines available functions for LLM function calling
"""

from typing import Dict, List, Any, Optional


class FunctionRegistry:
    """Registry of available functions for LLM"""
    
    def __init__(self):
        """Initialize function registry"""
        self._functions: Dict[str, Dict[str, Any]] = {}
        self._register_default_functions()
    
    def _register_default_functions(self):
        """Register default functions"""
        # Export PDF
        self.register_function(
            name="export_pdf",
            description="Export current risk assessment to PDF format",
            parameters={
                "type": "object",
                "properties": {
                    "template": {
                        "type": "string",
                        "enum": ["standard", "executive", "detailed"],
                        "description": "PDF template type",
                        "default": "standard"
                    },
                    "include_charts": {
                        "type": "boolean",
                        "description": "Include charts in PDF",
                        "default": True
                    },
                    "language": {
                        "type": "string",
                        "enum": ["en", "vi", "zh"],
                        "description": "PDF language",
                        "default": "en"
                    }
                }
            }
        )
        
        # Export Excel
        self.register_function(
            name="export_excel",
            description="Export current risk assessment to Excel format",
            parameters={
                "type": "object",
                "properties": {
                    "include_raw_data": {
                        "type": "boolean",
                        "description": "Include raw data in export",
                        "default": True
                    },
                    "include_charts": {
                        "type": "boolean",
                        "description": "Include charts as images",
                        "default": False
                    }
                }
            }
        )
        
        # Compare shipments
        self.register_function(
            name="compare_shipments",
            description="Compare multiple shipments side-by-side",
            parameters={
                "type": "object",
                "properties": {
                    "shipment_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of shipment IDs to compare",
                        "minItems": 2,
                        "maxItems": 5
                    },
                    "metrics": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["risk_score", "expected_loss", "delay_probability", "esg_score"]
                        },
                        "description": "Metrics to compare",
                        "default": ["risk_score", "expected_loss"]
                    }
                },
                "required": ["shipment_ids"]
            }
        )
        
        # Run scenario
        self.register_function(
            name="run_scenario",
            description="Run what-if scenario analysis",
            parameters={
                "type": "object",
                "properties": {
                    "scenario_type": {
                        "type": "string",
                        "enum": ["weather_shock", "port_congestion", "carrier_change", "route_change"],
                        "description": "Type of scenario to run"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Scenario-specific parameters",
                        "properties": {
                            "weather_severity": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Weather severity (0-1)"
                            },
                            "port_congestion_level": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Port congestion level (0-1)"
                            }
                        }
                    }
                },
                "required": ["scenario_type"]
            }
        )
        
        # Get recommendations
        self.register_function(
            name="get_recommendations",
            description="Get risk mitigation recommendations",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "Maximum number of recommendations",
                        "default": 5
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["risk_reduction", "cost_benefit", "feasibility"],
                        "description": "Sort recommendations by",
                        "default": "risk_reduction"
                    }
                }
            }
        )
        
        # Get summary
        self.register_function(
            name="get_summary",
            description="Get executive summary of risk assessment",
            parameters={
                "type": "object",
                "properties": {
                    "length": {
                        "type": "string",
                        "enum": ["short", "medium", "long"],
                        "description": "Summary length",
                        "default": "medium"
                    },
                    "language": {
                        "type": "string",
                        "enum": ["en", "vi", "zh"],
                        "description": "Summary language",
                        "default": "en"
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "description": "Include recommendations in summary",
                        "default": True
                    }
                }
            }
        )
        
        # Get financial metrics
        self.register_function(
            name="get_financial_metrics",
            description="Get detailed financial risk metrics (VaR, CVaR, expected loss)",
            parameters={
                "type": "object",
                "properties": {
                    "include_distributions": {
                        "type": "boolean",
                        "description": "Include loss distributions",
                        "default": False
                    },
                    "confidence_levels": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Confidence levels for VaR (e.g., [0.95, 0.99])",
                        "default": [0.95, 0.99]
                    }
                }
            }
        )
        
        # Get historical trend
        self.register_function(
            name="get_historical_trend",
            description="Get historical risk trend for shipments",
            parameters={
                "type": "object",
                "properties": {
                    "shipment_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Shipment IDs to analyze (optional, uses current if empty)"
                    },
                    "time_range": {
                        "type": "string",
                        "enum": ["30d", "90d", "1y"],
                        "description": "Time range for trend analysis",
                        "default": "90d"
                    },
                    "metric": {
                        "type": "string",
                        "enum": ["risk_score", "expected_loss", "delay_probability"],
                        "description": "Metric to track",
                        "default": "risk_score"
                    }
                }
            }
        )
    
    def register_function(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any]
    ):
        """
        Register a function
        
        Args:
            name: Function name
            description: Function description
            parameters: JSON Schema for parameters
        """
        self._functions[name] = {
            "name": name,
            "description": description,
            "parameters": parameters
        }
    
    def get_available_functions(self) -> List[Dict[str, Any]]:
        """
        Get list of available functions for LLM
        
        Returns:
            List of function definitions (Claude function calling format)
        """
        return list(self._functions.values())
    
    def get_function(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get function definition by name
        
        Args:
            name: Function name
            
        Returns:
            Function definition or None
        """
        return self._functions.get(name)
    
    def validate_function_call(
        self,
        function_call: Dict[str, Any]
    ) -> bool:
        """
        Validate function call
        
        Args:
            function_call: Function call dictionary
            
        Returns:
            True if valid, False otherwise
        """
        name = function_call.get('name')
        if not name or name not in self._functions:
            return False
        
        # Basic validation - could be enhanced with JSON Schema validation
        return True
