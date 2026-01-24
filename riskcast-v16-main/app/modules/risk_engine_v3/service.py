"""
Risk Engine V3 Service
Deterministic wrapper for risk engine execution
RISKCAST V3 - Modular Monolith
"""
import hashlib
import json
import os
from typing import Optional, Tuple
import logging

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("numpy not available - deterministic seed computation may be limited")

from app.modules.risk_engine_v3.schemas import (
    RiskEngineInputV3,
    RiskEngineRunConfig,
    RiskEngineResultV3,
    LayerContribution,
    DistributionSummary
)

logger = logging.getLogger(__name__)


class RiskEngineV3:
    """
    Risk Engine V3 with deterministic execution.
    
    Features:
    - Deterministic seed computation from input parameters
    - Canonical result hashing for reproducibility
    - Structured input/output DTOs
    - Provenance tracking
    """
    
    RESULT_SCHEMA_VERSION = "risk_result_v3.0"
    
    def __init__(self):
        """Initialize risk engine"""
        self.engine_version = self._get_engine_version()
        logger.info(f"RiskEngineV3 initialized with version: {self.engine_version}")
    
    def _get_engine_version(self) -> str:
        """
        Get engine version (git SHA or configured version).
        
        Returns:
            Engine version string
        """
        # Try environment variable first
        version = os.getenv('ENGINE_VERSION')
        if version:
            return version
        
        # Try reading from git (if available)
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return f"git-{result.stdout.strip()}"
        except Exception:
            pass
        
        # Fallback to configured version or default
        return os.getenv('ENGINE_VERSION_FALLBACK', 'dev-local')
    
    def compute_deterministic_seed(
        self,
        input_hash: str,
        model_version_id: Optional[str],
        iterations: int,
        result_schema_version: str
    ) -> int:
        """
        Compute deterministic seed from input parameters.
        
        Formula:
        seed = uint64(sha256(input_hash + model_version_id + iterations + result_schema_version)[0:8])
        
        This ensures the same input parameters always produce the same seed,
        enabling reproducible risk calculations.
        
        Args:
            input_hash: SHA256 hash of input data
            model_version_id: Model version ID (or None)
            iterations: Number of Monte Carlo iterations
            result_schema_version: Result schema version
            
        Returns:
            Deterministic seed (64-bit integer)
        """
        # Build seed input string
        seed_input = f"{input_hash}|{model_version_id or 'default'}|{iterations}|{result_schema_version}"
        
        # Compute SHA256 hash
        hash_bytes = hashlib.sha256(seed_input.encode('utf-8')).digest()
        
        # Extract first 8 bytes (64 bits) and convert to integer
        seed = int.from_bytes(hash_bytes[:8], 'big')
        
        logger.debug(
            f"Computed deterministic seed: {seed} from "
            f"input_hash={input_hash[:16]}..., model_version_id={model_version_id}, "
            f"iterations={iterations}, result_schema_version={result_schema_version}"
        )
        
        return seed
    
    def _canonicalize_result(self, result: dict) -> str:
        """
        Canonicalize result for hashing.
        
        Rounds floats to fixed precision to ensure consistent hashing
        even with minor floating-point differences.
        
        Args:
            result: Result dictionary
            
        Returns:
            Canonical JSON string
        """
        def round_floats(obj, precision=8):
            """Recursively round floats to fixed precision"""
            if isinstance(obj, float):
                return round(obj, precision)
            elif isinstance(obj, dict):
                return {k: round_floats(v, precision) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [round_floats(i, precision) for i in obj]
            return obj
        
        # Round all floats to 8 decimal places
        rounded = round_floats(result, precision=8)
        
        # Canonical JSON (sorted keys, no whitespace)
        return json.dumps(rounded, sort_keys=True, separators=(',', ':'))
    
    def _compute_result_hash(self, canonical_result: str) -> str:
        """
        Compute SHA256 hash of canonical result.
        
        Args:
            canonical_result: Canonical JSON string
            
        Returns:
            SHA256 hex digest
        """
        return hashlib.sha256(canonical_result.encode('utf-8')).hexdigest()
    
    async def run(
        self,
        input_dto: RiskEngineInputV3,
        config: RiskEngineRunConfig
    ) -> Tuple[RiskEngineResultV3, str]:
        """
        Execute risk engine with deterministic settings.
        
        Args:
            input_dto: Input DTO with assessment data
            config: Run configuration
            
        Returns:
            Tuple of (result_dto, result_hash)
            
        Raises:
            ValueError: If numpy is not available and required
            RuntimeError: If engine execution fails
        """
        logger.info(
            f"Executing risk engine for assessment {input_dto.risk_assessment_id} "
            f"with seed={config.seed}, iterations={config.iterations}"
        )
        
        # Initialize RNG with seed for deterministic execution
        if not NUMPY_AVAILABLE:
            raise ValueError("numpy is required for deterministic execution")
        
        rng = np.random.default_rng(config.seed)
        
        # Execute engine internals
        try:
            result = await self._execute_engine_internal(
                input_dto.input_snapshot,
                config.model_payload,
                config.iterations,
                rng
            )
        except Exception as e:
            logger.error(f"Engine execution failed: {e}", exc_info=True)
            raise RuntimeError(f"Engine execution failed: {str(e)}") from e
        
        # Build v3 result DTO
        result_v3 = RiskEngineResultV3(
            result_schema_version=self.RESULT_SCHEMA_VERSION,
            overall_risk_score=result['overall_score'],
            layer_contributions=[
                LayerContribution(**layer) if isinstance(layer, dict) else layer
                for layer in result['layers']
            ],
            distribution_summary=DistributionSummary(**result['distribution']),
            explainability_graph=result.get('explainability'),
            provenance={
                'engine_version': config.engine_version,
                'model_version_id': str(config.model_version_id) if config.model_version_id else None,
                'seed': config.seed,
                'iterations': config.iterations,
                'input_hash': input_dto.input_hash
            }
        )
        
        # Compute result hash
        result_dict = result_v3.model_dump(exclude_none=True, mode='json')
        canonical = self._canonicalize_result(result_dict)
        result_hash = self._compute_result_hash(canonical)
        
        logger.info(
            f"Engine execution completed for assessment {input_dto.risk_assessment_id}. "
            f"Result hash: {result_hash[:16]}..."
        )
        
        return result_v3, result_hash
    
    async def _execute_engine_internal(
        self,
        input_snapshot: dict,
        model_payload: Optional[dict],
        iterations: int,
        rng: 'np.random.Generator'
    ) -> dict:
        """
        Internal engine execution.
        
        TODO: Replace with actual V16 engine call.
        This is a placeholder implementation that should be replaced with
        the actual risk engine logic from the existing codebase.
        
        Args:
            input_snapshot: Canonical normalized input data
            model_payload: Model payload (weights, parameters, etc.)
            iterations: Number of Monte Carlo iterations
            rng: NumPy random number generator (seeded)
            
        Returns:
            Dictionary with engine results:
            {
                'overall_score': float,
                'layers': List[dict],
                'distribution': dict,
                'explainability': dict (optional)
            }
        """
        # Placeholder implementation
        # TODO: Integrate with actual V16 engine
        
        logger.warning("Using placeholder engine implementation - replace with actual engine")
        
        # Example placeholder logic
        # In production, this should call the actual risk engine
        overall_score = 0.75  # Placeholder
        
        layers = [
            {
                'layer_name': 'route',
                'contribution': 0.45,
                'details': {'distance_km': 12000}
            },
            {
                'layer_name': 'cargo',
                'contribution': 0.30,
                'details': {'value_usd': 100000}
            },
            {
                'layer_name': 'climate',
                'contribution': 0.25,
                'details': {}
            }
        ]
        
        # Generate distribution using RNG (deterministic)
        samples = rng.normal(overall_score, 0.15, iterations)
        samples = np.clip(samples, 0.0, 1.0)  # Clip to [0, 1]
        
        distribution = {
            'mean': float(np.mean(samples)),
            'std': float(np.std(samples)),
            'var_95': float(np.percentile(samples, 95)),
            'var_99': float(np.percentile(samples, 99)),
            'cvar_95': float(np.mean(samples[samples >= np.percentile(samples, 95)])),
            'cvar_99': float(np.mean(samples[samples >= np.percentile(samples, 99)]))
        }
        
        return {
            'overall_score': overall_score,
            'layers': layers,
            'distribution': distribution,
            'explainability': None  # Placeholder
        }
