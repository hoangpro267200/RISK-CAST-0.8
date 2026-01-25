"""
Train Fraud Detection Models

Script to train ML models for fraud detection on historical claims data.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.ml.anomaly_detection import fraud_service, FeatureEngineering
from app.core.logging import get_logger
from app.db.session import get_db
import numpy as np


logger = get_logger(__name__)


async def load_sample_data():
    """Load or generate sample claims data for training."""
    # In production, this would load from database
    # For demonstration, generate synthetic data
    
    logger.info("Generating synthetic training data...")
    
    np.random.seed(42)
    n_samples = 500
    
    claims_data = []
    
    for i in range(n_samples):
        # Generate realistic claim/policy pairs
        cargo_value = np.random.lognormal(11, 1)  # ~$50k-$200k
        coverage = cargo_value
        
        # Normal claims (80%)
        if i < n_samples * 0.8:
            claim_ratio = np.random.beta(2, 5)  # Typically lower claims
            days_since_inception = np.random.randint(30, 365)
            days_to_report = np.random.randint(1, 7)
            previous_claims = np.random.poisson(0.5)
        # Suspicious claims (20%)
        else:
            claim_ratio = np.random.beta(5, 2)  # Higher claims
            days_since_inception = np.random.randint(1, 20)  # Quick claims
            days_to_report = np.random.randint(7, 30)  # Delayed reporting
            previous_claims = np.random.poisson(2)  # More history
        
        claimed_amount = claim_ratio * coverage
        premium = cargo_value * 0.008  # ~0.8% rate
        
        from datetime import datetime, timedelta
        
        inception_date = datetime.now() - timedelta(days=days_since_inception)
        loss_date = inception_date + timedelta(days=days_since_inception)
        filed_date = loss_date + timedelta(days=days_to_report)
        
        loss_types = ['CARGO_DAMAGE', 'CARGO_LOSS', 'CONTAMINATION', 'THEFT', 'WATER_DAMAGE', 'DELAY']
        
        claim = {
            'claimed_amount': float(claimed_amount),
            'loss_date': loss_date,
            'filed_at': filed_date,
            'loss_type': np.random.choice(loss_types),
            'customer_previous_claims': int(previous_claims)
        }
        
        policy = {
            'coverage_limit': float(coverage),
            'cargo_value_usd': float(cargo_value),
            'effective_from': inception_date,
            'total_premium_usd': float(premium),
            'total_premium': float(premium)
        }
        
        claims_data.append({
            'claim': claim,
            'policy': policy
        })
    
    logger.info(f"Generated {len(claims_data)} synthetic claims for training")
    
    return claims_data


async def train_models(use_sample_data: bool = False):
    """Train fraud detection models."""
    logger.info("Starting fraud detection model training")
    
    if use_sample_data:
        # Use synthetic data
        claims_data = await load_sample_data()
    else:
        # Load from database
        logger.info("Loading claims data from database...")
        claims_data = None  # Will be loaded by fraud_service.train_models()
    
    # Train models
    success = await fraud_service.train_models(claims_data)
    
    if success:
        logger.info("✓ Fraud detection models trained successfully")
        
        # Print statistics
        logger.info(f"  - Isolation Forest: {'✓ Trained' if fraud_service.isolation_forest.model else '✗ Not trained'}")
        if fraud_service.use_autoencoder:
            logger.info(f"  - Autoencoder: {'✓ Trained' if fraud_service.autoencoder.model else '✗ Not trained'}")
        else:
            logger.info("  - Autoencoder: ✗ Not available (TensorFlow required)")
        
        logger.info(f"  - Features: {len(fraud_service.feature_names)}")
        logger.info(f"  - Feature names: {', '.join(fraud_service.feature_names)}")
        
        return True
    else:
        logger.error("✗ Fraud detection model training failed")
        return False


async def test_prediction(use_sample_data: bool = False):
    """Test fraud detection on sample claims."""
    logger.info("\nTesting fraud detection...")
    
    # Test cases
    test_cases = [
        {
            'name': 'Normal Claim',
            'claim': {
                'claimed_amount': 25000,
                'loss_date': '2026-01-15',
                'filed_at': '2026-01-16T10:00:00Z',
                'loss_type': 'CARGO_DAMAGE',
                'customer_previous_claims': 0
            },
            'policy': {
                'coverage_limit': 100000,
                'cargo_value_usd': 100000,
                'effective_from': '2025-12-01',
                'total_premium_usd': 850
            }
        },
        {
            'name': 'Suspicious Claim (High ratio + Quick)',
            'claim': {
                'claimed_amount': 95000,
                'loss_date': '2026-01-20',
                'filed_at': '2026-01-21T10:00:00Z',
                'loss_type': 'CARGO_LOSS',
                'customer_previous_claims': 3
            },
            'policy': {
                'coverage_limit': 100000,
                'cargo_value_usd': 100000,
                'effective_from': '2026-01-19',
                'total_premium_usd': 850
            }
        },
        {
            'name': 'Suspicious Claim (Delayed reporting)',
            'claim': {
                'claimed_amount': 60000,
                'loss_date': '2026-01-05',
                'filed_at': '2026-01-20T10:00:00Z',
                'loss_type': 'THEFT',
                'customer_previous_claims': 2
            },
            'policy': {
                'coverage_limit': 80000,
                'cargo_value_usd': 80000,
                'effective_from': '2025-12-15',
                'total_premium_usd': 680
            }
        }
    ]
    
    for test_case in test_cases:
        logger.info(f"\n{'='*60}")
        logger.info(f"Test Case: {test_case['name']}")
        logger.info(f"{'='*60}")
        
        result = await fraud_service.detect_fraud(
            test_case['claim'],
            test_case['policy']
        )
        
        logger.info(f"  Is Anomaly: {result.is_anomaly}")
        logger.info(f"  Fraud Score: {result.anomaly_score:.3f}")
        logger.info(f"  Anomaly Type: {result.anomaly_type}")
        logger.info(f"  Confidence: {result.confidence:.3f}")
        logger.info(f"  Contributing Factors: {', '.join(result.features_contributing)}")
        logger.info(f"  Explanation: {result.explanation}")
        
        if result.metadata:
            logger.info(f"  Metadata: {result.metadata}")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Train fraud detection models')
    parser.add_argument(
        '--sample-data',
        action='store_true',
        help='Use synthetic sample data instead of database'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run test predictions after training'
    )
    
    args = parser.parse_args()
    
    try:
        # Train models
        success = await train_models(use_sample_data=args.sample_data)
        
        if not success:
            sys.exit(1)
        
        # Test if requested
        if args.test:
            await test_prediction(use_sample_data=args.sample_data)
        
        logger.info("\n✓ Training complete!")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
