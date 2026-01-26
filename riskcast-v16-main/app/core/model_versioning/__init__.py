"""
Model versioning core utilities.
Selection and loading logic for model versions.
"""
from app.core.model_versioning.selector import (
    ModelSelector,
    ModelSelectionContext,
    ModelSelectionResult,
    ModelNotFoundError,
    ModelNotPublishedError,
    NoActiveModelError
)
from app.core.model_versioning.loader import (
    ModelLoader,
    ModelPayload
)

# Import standalone functions from the legacy module
try:
    from app.core.model_versioning_standalone import (
        get_current_model_version,
        get_model_version,
        list_model_versions,
        get_version_for_audit
    )
except ImportError:
    # Fallback implementations
    from typing import Dict, List, Optional
    
    def get_current_model_version() -> Dict:
        """Get current model version info."""
        return {
            "version": "v16.0.0",
            "name": "RiskCast V16",
            "status": "active",
            "description": "Production risk assessment model"
        }
    
    def get_model_version(version: str) -> Optional[Dict]:
        """Get specific model version."""
        return get_current_model_version() if version == "v16.0.0" else None
    
    def list_model_versions(include_deprecated: bool = False) -> List[Dict]:
        """List all model versions."""
        return [get_current_model_version()]
    
    def get_version_for_audit() -> Dict:
        """Get version info for audit."""
        return get_current_model_version()

__all__ = [
    'ModelSelector',
    'ModelSelectionContext',
    'ModelSelectionResult',
    'ModelNotFoundError',
    'ModelNotPublishedError',
    'NoActiveModelError',
    'ModelLoader',
    'ModelPayload',
    'get_current_model_version',
    'get_model_version',
    'list_model_versions',
    'get_version_for_audit',
]
