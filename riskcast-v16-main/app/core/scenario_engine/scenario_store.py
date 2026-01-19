"""
RISKCAST Scenario Engine - Scenario Storage Module
Save, load, and manage scenario configurations
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime
import os


class ScenarioStore:
    """Scenario storage manager"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize scenario store
        
        Args:
            storage_path: Path to storage directory (default: app/data/scenarios)
        """
        if storage_path:
            self.storage_dir = Path(storage_path)
        else:
            # Default to app/data/scenarios
            base_dir = Path(__file__).parent.parent.parent.parent
            self.storage_dir = base_dir / "data" / "scenarios"
        
        # Ensure directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage file
        self.storage_file = self.storage_dir / "scenarios.json"
        
        # Initialize storage if needed
        if not self.storage_file.exists():
            self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize empty storage file"""
        initial_data = {
            "scenarios": {},
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "1.0",
            }
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
    
    def _load_storage(self) -> Dict[str, Any]:
        """Load storage file"""
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._initialize_storage()
            return self._load_storage()
    
    def _save_storage(self, data: Dict[str, Any]):
        """Save storage file"""
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_scenario(self, 
                     name: str,
                     adjustments: Dict[str, float],
                     result: Optional[Dict[str, Any]] = None,
                     baseline_score: Optional[float] = None,
                     description: Optional[str] = None) -> bool:
        """
        Save a scenario
        
        Args:
            name: Scenario name (must be unique)
            adjustments: Adjustment dictionary
            result: Optional simulation result
            baseline_score: Optional baseline score for reference
            description: Optional scenario description
            
        Returns:
            True if saved successfully
        """
        data = self._load_storage()
        
        # Check if name already exists
        if name in data["scenarios"]:
            return False  # Name conflict
        
        # Create scenario entry
        scenario_entry = {
            "name": name,
            "adjustments": adjustments,
            "baseline_score": baseline_score,
            "description": description,
            "created": datetime.now().isoformat(),
            "last_run": None,
        }
        
        # Optionally store result (can be large)
        if result:
            scenario_entry["last_result"] = {
                "simulation_score": result.get("simulation_score"),
                "delta_from_baseline": result.get("delta_from_baseline"),
                "risk_level": result.get("profile", {}).get("level"),
            }
            scenario_entry["last_run"] = datetime.now().isoformat()
        
        # Save
        data["scenarios"][name] = scenario_entry
        self._save_storage(data)
        
        return True
    
    def load_scenario(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a scenario
        
        Args:
            name: Scenario name
            
        Returns:
            Scenario dictionary or None if not found
        """
        data = self._load_storage()
        return data["scenarios"].get(name)
    
    def list_scenarios(self) -> List[Dict[str, Any]]:
        """
        List all saved scenarios
        
        Returns:
            List of scenario summaries
        """
        data = self._load_storage()
        scenarios = data.get("scenarios", {})
        
        # Return summaries (without full results)
        summaries = []
        for name, scenario in scenarios.items():
            summaries.append({
                "name": name,
                "description": scenario.get("description"),
                "adjustments": scenario.get("adjustments", {}),
                "baseline_score": scenario.get("baseline_score"),
                "created": scenario.get("created"),
                "last_run": scenario.get("last_run"),
                "last_result": scenario.get("last_result"),
            })
        
        # Sort by creation date (newest first)
        summaries.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        return summaries
    
    def delete_scenario(self, name: str) -> bool:
        """
        Delete a scenario
        
        Args:
            name: Scenario name
            
        Returns:
            True if deleted successfully
        """
        data = self._load_storage()
        
        if name not in data["scenarios"]:
            return False
        
        # Delete
        del data["scenarios"][name]
        self._save_storage(data)
        
        return True
    
    def update_scenario(self,
                       name: str,
                       adjustments: Optional[Dict[str, float]] = None,
                       description: Optional[str] = None) -> bool:
        """
        Update an existing scenario
        
        Args:
            name: Scenario name
            adjustments: Optional new adjustments
            description: Optional new description
            
        Returns:
            True if updated successfully
        """
        data = self._load_storage()
        
        if name not in data["scenarios"]:
            return False
        
        # Update fields
        if adjustments is not None:
            data["scenarios"][name]["adjustments"] = adjustments
        
        if description is not None:
            data["scenarios"][name]["description"] = description
        
        data["scenarios"][name]["updated"] = datetime.now().isoformat()
        
        self._save_storage(data)
        
        return True
    
    def get_scenario_count(self) -> int:
        """
        Get total number of saved scenarios
        
        Returns:
            Number of scenarios
        """
        data = self._load_storage()
        return len(data.get("scenarios", {}))




















