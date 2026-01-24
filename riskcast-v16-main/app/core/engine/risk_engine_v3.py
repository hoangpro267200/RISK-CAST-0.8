"""
V3 Risk Engine Wrapper - deterministic, versioned, auditable.

This wrapper:
1. Selects appropriate model version
2. Ensures deterministic execution with seeded RNG
3. Produces fully auditable outputs with provenance
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
import json

from sqlalchemy.orm import Session

from app.core.utils.rng_contract import create_seeded_rng, derive_seed
from app.core.utils.seed_strategy import SeedStrategy, resolve_seed
from app.core.risk_input.canonicalization import canonicalize_input, compute_input_hash
from app.core.model_versioning.selector import ModelSelector, ModelSelectionContext
from app.core.model_versioning.loader import ModelLoader, ModelPayload
from app.core.engine.risk_engine_v16_adapter import RiskEngineV16Adapter


@dataclass
class EngineConfig:
    """Configuration for engine execution."""
    seed: Optional[int] = None
    seed_strategy: SeedStrategy = SeedStrategy.HASH_BASED
    iterations: int = 10000
    explicit_model_version_id: Optional[str] = None  # ULID string


@dataclass
class EngineProvenance:
    """Full provenance for a risk engine run."""
    # Input
    input_hash: str
    schema_version: str
    
    # Model
    model_version_id: str  # ULID
    model_immutable_hash: Optional[str]
    model_selection_reason: str
    
    # Execution
    seed: int
    seed_strategy: str
    iterations: int
    engine_version: str
    
    # Output
    result_hash: str
    computed_at: datetime


@dataclass
class EngineResult:
    """Complete result from risk engine execution."""
    # Risk scores
    overall_risk_score: float
    risk_factors: Dict[str, float]
    
    # Distribution metrics
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    expected_loss: float
    
    # Explanations
    risk_drivers: Dict[str, Any]
    recommendations: list
    
    # Provenance
    provenance: EngineProvenance
    
    # Raw distribution (optional, for detailed analysis)
    loss_distribution: Optional[list] = None


class RiskEngineV3:
    """
    V3 Risk Engine - production-grade wrapper.
    
    Ensures:
    - Deterministic execution
    - Model version pinning
    - Full provenance tracking
    - Reproducible results
    """
    
    ENGINE_VERSION = "3.0.0"
    
    def __init__(self, db: Session):
        """
        Initialize V3 risk engine.
        
        Args:
            db: Database session
        """
        self.db = db
        self.model_selector = ModelSelector(db)
        self.model_loader = ModelLoader()
        self.v16_adapter = RiskEngineV16Adapter()
    
    def run(
        self,
        input_data: Dict[str, Any],
        config: EngineConfig,
        context: ModelSelectionContext
    ) -> EngineResult:
        """
        Execute risk assessment with full provenance.
        
        Args:
            input_data: Raw input data for risk assessment
            config: Execution configuration
            context: Model selection context
            
        Returns:
            EngineResult with scores and provenance
        """
        # 1. Canonicalize input
        canonical_input = canonicalize_input(input_data)
        input_hash = compute_input_hash(canonical_input)
        
        # 2. Select model
        selection = self.model_selector.select(
            context=context,
            explicit_model_version_id=config.explicit_model_version_id
        )
        model_payload = self.model_loader.load(selection.model_version)
        
        # 3. Resolve seed
        seed = resolve_seed(
            strategy=config.seed_strategy,
            input_hash=int(input_hash, 16) if input_hash else None,  # Convert hex to int
            explicit_seed=config.seed
        )
        
        # 4. Create seeded RNG
        rng = create_seeded_rng(seed)
        
        # 5. Execute engine with model payload
        raw_result = self._execute_engine(
            canonical_input=canonical_input,
            model_payload=model_payload,
            iterations=config.iterations,
            rng=rng
        )
        
        # 6. Compute result hash
        result_hash = self._compute_result_hash(raw_result)
        
        # 7. Build provenance
        provenance = EngineProvenance(
            input_hash=input_hash,
            schema_version="1.0",  # TODO: Get from input validation
            model_version_id=model_payload.model_version_id,
            model_immutable_hash=model_payload.immutable_hash,
            model_selection_reason=selection.selection_reason,
            seed=seed,
            seed_strategy=config.seed_strategy.value,
            iterations=config.iterations,
            engine_version=self.ENGINE_VERSION,
            result_hash=result_hash,
            computed_at=datetime.utcnow()
        )
        
        # 8. Build and return result
        return EngineResult(
            overall_risk_score=raw_result['overall_risk_score'],
            risk_factors=raw_result['risk_factors'],
            var_95=raw_result['var_95'],
            var_99=raw_result['var_99'],
            cvar_95=raw_result['cvar_95'],
            cvar_99=raw_result['cvar_99'],
            expected_loss=raw_result['expected_loss'],
            risk_drivers=raw_result.get('risk_drivers', {}),
            recommendations=raw_result.get('recommendations', []),
            provenance=provenance,
            loss_distribution=raw_result.get('loss_distribution')
        )
    
    def _execute_engine(
        self,
        canonical_input: dict,
        model_payload: ModelPayload,
        iterations: int,
        rng
    ) -> dict:
        """
        Execute the underlying V16 engine with model payload.
        
        This is where we inject the versioned model parameters.
        
        Args:
            canonical_input: Canonicalized input data
            model_payload: Model parameters from versioned model
            iterations: Number of Monte Carlo iterations
            rng: Seeded numpy random generator
            
        Returns:
            Dict with risk scores and metrics
        """
        # Pass model payload to v16 adapter
        return self.v16_adapter.run_monte_carlo(
            input_data=canonical_input,
            model_payload=model_payload,
            iterations=iterations,
            rng=rng
        )
    
    def _compute_result_hash(self, result: dict) -> str:
        """
        Compute deterministic hash of result.
        
        Excludes non-deterministic fields like timestamps.
        
        Args:
            result: Engine result dictionary
            
        Returns:
            SHA256 hash as hex string
        """
        # Fields to include in hash
        hashable = {
            'overall_risk_score': result['overall_risk_score'],
            'risk_factors': result['risk_factors'],
            'var_95': result['var_95'],
            'var_99': result['var_99'],
            'cvar_95': result['cvar_95'],
            'cvar_99': result['cvar_99'],
            'expected_loss': result['expected_loss']
        }
        
        # Canonical serialization
        canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def verify_result(self, result: EngineResult) -> bool:
        """
        Verify that result hash matches computed values.
        
        Returns True if result is valid and untampered.
        
        Args:
            result: EngineResult to verify
            
        Returns:
            True if hash matches, False otherwise
        """
        recomputed = self._compute_result_hash({
            'overall_risk_score': result.overall_risk_score,
            'risk_factors': result.risk_factors,
            'var_95': result.var_95,
            'var_99': result.var_99,
            'cvar_95': result.cvar_95,
            'cvar_99': result.cvar_99,
            'expected_loss': result.expected_loss
        })
        return recomputed == result.provenance.result_hash
