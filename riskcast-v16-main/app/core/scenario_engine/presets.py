"""
RISKCAST Scenario Engine - Preset Scenarios
Common predefined scenarios for quick testing
"""

from typing import Dict, Any, Optional, List


class ScenarioPresets:
    """Predefined scenario presets"""
    
    PRESETS = {
        "Heavy Rain Season Q3": {
            "description": "Simulates heavy monsoon/rainy season conditions in Q3 (July-September)",
            "adjustments": {
                "weather_hazard": +0.25,  # Significant increase in weather risk
                "port_congestion": +0.10,  # Moderate increase due to weather delays
                "delay": +0.15,  # Increased delay risk
            },
            "category": "seasonal",
            "applicable_routes": ["Asia", "Pacific"],
        },
        
        "Port Strike": {
            "description": "Simulates port labor strike or shutdown scenario",
            "adjustments": {
                "port_congestion": +0.40,  # Major port disruption
                "network": +0.25,  # Network cascade effects
                "delay": +0.30,  # Significant delay risk
                "carrier_reliability": -0.15,  # Carrier reliability drops
            },
            "category": "operational",
            "applicable_routes": ["All"],
        },
        
        "Equipment Shortage": {
            "description": "Simulates container/equipment shortage scenario",
            "adjustments": {
                "equipment": +0.35,  # Equipment availability crisis
                "port_congestion": +0.15,  # Port delays due to equipment wait
                "delay": +0.20,  # Increased delays
            },
            "category": "operational",
            "applicable_routes": ["All"],
        },
        
        "Carrier Reliability Drop": {
            "description": "Simulates significant drop in carrier performance",
            "adjustments": {
                "carrier_reliability": -0.30,  # Major reliability drop
                "network": +0.15,  # Network risk due to unreliable carrier
                "delay": +0.25,  # Increased delay probability
            },
            "category": "operational",
            "applicable_routes": ["All"],
        },
        
        "Holiday Peak Season": {
            "description": "Simulates peak shipping season (Q4 holidays, Chinese New Year, etc.)",
            "adjustments": {
                "port_congestion": +0.20,  # Peak season congestion
                "network": +0.15,  # Network stress
                "delay": +0.15,  # Increased delays
                "equipment": +0.10,  # Equipment shortages during peak
            },
            "category": "seasonal",
            "applicable_routes": ["All"],
        },
        
        "Extreme Weather Event": {
            "description": "Simulates extreme weather (hurricane, typhoon, blizzard)",
            "adjustments": {
                "weather_hazard": +0.45,  # Extreme weather risk
                "port_congestion": +0.20,  # Port closures/disruptions
                "delay": +0.35,  # Major delays
                "network": +0.20,  # Network disruptions
            },
            "category": "environmental",
            "applicable_routes": ["All"],
        },
        
        "Trade Route Disruption": {
            "description": "Simulates geopolitical or trade route disruption",
            "adjustments": {
                "network": +0.35,  # Major network disruption
                "port_congestion": +0.25,  # Alternative port congestion
                "delay": +0.30,  # Route delays
                "esg": +0.15,  # Regulatory/ESG concerns
            },
            "category": "geopolitical",
            "applicable_routes": ["All"],
        },
        
        "ESG Compliance Pressure": {
            "description": "Simulates increased ESG regulatory pressure",
            "adjustments": {
                "esg": +0.30,  # ESG risk increase
                "network": +0.10,  # Network adjustments for ESG
                "delay": +0.05,  # Slight delays for compliance
            },
            "category": "regulatory",
            "applicable_routes": ["EU", "North America"],
        },
    }
    
    @classmethod
    def get_preset(cls, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a preset scenario by name
        
        Args:
            name: Preset name
            
        Returns:
            Preset dictionary or None
        """
        return cls.PRESETS.get(name)
    
    @classmethod
    def list_presets(cls) -> List[Dict[str, Any]]:
        """
        List all available presets
        
        Returns:
            List of preset summaries
        """
        presets = []
        for name, preset in cls.PRESETS.items():
            presets.append({
                "name": name,
                "description": preset.get("description"),
                "category": preset.get("category"),
                "adjustments": preset.get("adjustments", {}),
            })
        
        return presets
    
    @classmethod
    def get_presets_by_category(cls, category: str) -> List[Dict[str, Any]]:
        """
        Get presets by category
        
        Args:
            category: Category name (seasonal, operational, environmental, etc.)
            
        Returns:
            List of presets in that category
        """
        presets = []
        for name, preset in cls.PRESETS.items():
            if preset.get("category") == category:
                presets.append({
                    "name": name,
                    "description": preset.get("description"),
                    "adjustments": preset.get("adjustments", {}),
                })
        
        return presets
    
    @classmethod
    def apply_preset(cls, name: str) -> Optional[Dict[str, float]]:
        """
        Get adjustments for a preset
        
        Args:
            name: Preset name
            
        Returns:
            Adjustments dictionary or None
        """
        preset = cls.get_preset(name)
        if preset:
            return preset.get("adjustments", {}).copy()
        return None

