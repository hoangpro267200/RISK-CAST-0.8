"""
Train Predictive Analytics Models

Script to train loss prediction, claim probability, and market trend models.
"""

import asyncio
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.ml.predictive_models import (
    LossPredictionModel,
    ClaimProbabilityModel,
    MarketTrendPredictor,
    loss_model,
    claim_model,
    market_predictor
)
from app.core.logging import get_logger


logger = get_logger(__name__)


def generate_loss_training_data(n_samples: int = 1000) -> pd.DataFrame:
    """Generate synthetic data for loss prediction training."""
    logger.info(f"Generating {n_samples} synthetic loss samples...")
    
    np.random.seed(42)
    
    data = []
    for i in range(n_samples):
        # Base features
        cargo_value = np.random.lognormal(11, 0.8)  # ~$50k-$200k
        container_count = np.random.randint(1, 10)
        transit_days = np.random.randint(7, 45)
        risk_score = np.random.beta(2, 3)  # Skewed toward lower risk
        weather_risk = np.random.beta(2, 5)
        port_congestion = np.random.beta(2, 4)
        carrier_reliability = np.random.beta(8, 2)  # Skewed toward high reliability
        historical_loss_rate = np.random.beta(1, 30) * 0.1  # Small losses typical
        
        # Categorical
        cargo_types = ['GENERAL', 'ELECTRONICS', 'MACHINERY', 'FOOD', 'CHEMICALS']
        regions = ['ASIA', 'EUROPE', 'AMERICAS', 'AFRICA', 'OCEANIA']
        
        cargo_type = np.random.choice(cargo_types)
        origin_region = np.random.choice(regions)
        destination_region = np.random.choice(regions)
        coverage_type = np.random.choice(['STANDARD', 'ENHANCED', 'COMPREHENSIVE'])
        
        # Calculate actual loss (with noise)
        base_loss = (
            risk_score * 0.03 +
            weather_risk * 0.02 +
            port_congestion * 0.01 +
            (1 - carrier_reliability) * 0.02 +
            historical_loss_rate * 0.5 +
            (transit_days / 100) * 0.01
        )
        
        # Add noise and ensure bounds
        actual_loss_pct = max(0, min(0.15, base_loss + np.random.normal(0, 0.005)))
        
        data.append({
            'cargo_value_usd': cargo_value,
            'container_count': container_count,
            'transit_days': transit_days,
            'risk_score': risk_score,
            'weather_risk': weather_risk,
            'port_congestion_risk': port_congestion,
            'carrier_reliability_score': carrier_reliability,
            'historical_loss_rate': historical_loss_rate,
            'cargo_type': cargo_type,
            'origin_region': origin_region,
            'destination_region': destination_region,
            'coverage_type': coverage_type,
            'actual_loss_pct': actual_loss_pct
        })
    
    df = pd.DataFrame(data)
    logger.info(f"Generated loss data: {len(df)} samples")
    logger.info(f"  Avg loss: {df['actual_loss_pct'].mean():.2%}")
    logger.info(f"  Loss range: {df['actual_loss_pct'].min():.2%} - {df['actual_loss_pct'].max():.2%}")
    
    return df


def generate_claim_training_data(n_samples: int = 1000) -> pd.DataFrame:
    """Generate synthetic data for claim probability training."""
    logger.info(f"Generating {n_samples} synthetic claim samples...")
    
    np.random.seed(42)
    
    data = []
    for i in range(n_samples):
        cargo_value = np.random.lognormal(11, 0.8)
        container_count = np.random.randint(1, 10)
        transit_days = np.random.randint(7, 45)
        risk_score = np.random.beta(2, 3)
        weather_risk = np.random.beta(2, 5)
        carrier_reliability = np.random.beta(8, 2)
        customer_claim_history = np.random.poisson(1)
        route_historical_claims = np.random.beta(1, 20) * 0.3
        
        # Calculate claim probability
        claim_prob = (
            risk_score * 0.2 +
            weather_risk * 0.15 +
            (1 - carrier_reliability) * 0.2 +
            (customer_claim_history / 10) * 0.3 +
            route_historical_claims * 0.15
        )
        
        # Binary outcome
        had_claim = 1 if np.random.random() < claim_prob else 0
        
        data.append({
            'cargo_value_usd': cargo_value,
            'container_count': container_count,
            'transit_days': transit_days,
            'risk_score': risk_score,
            'weather_risk': weather_risk,
            'carrier_reliability_score': carrier_reliability,
            'customer_claim_history': customer_claim_history,
            'route_historical_claims': route_historical_claims,
            'had_claim': had_claim
        })
    
    df = pd.DataFrame(data)
    claim_rate = df['had_claim'].mean()
    logger.info(f"Generated claim data: {len(df)} samples")
    logger.info(f"  Claim rate: {claim_rate:.1%}")
    
    return df


def generate_market_trend_data(n_months: int = 36) -> pd.DataFrame:
    """Generate synthetic market rate data."""
    logger.info(f"Generating {n_months} months of market data...")
    
    np.random.seed(42)
    
    # Generate dates
    current_date = datetime.utcnow()
    dates = [current_date - timedelta(days=30 * i) for i in range(n_months, 0, -1)]
    
    # Generate rates with trend and seasonality
    base_rate = 0.008  # 0.8%
    trend = np.linspace(0, 0.002, n_months)  # Slight upward trend
    seasonality = 0.001 * np.sin(np.linspace(0, 6 * np.pi, n_months))  # 3-year cycle
    noise = np.random.normal(0, 0.0005, n_months)
    
    rates = base_rate + trend + seasonality + noise
    rates = np.clip(rates, 0.005, 0.015)  # Reasonable bounds
    
    df = pd.DataFrame({
        'date': dates,
        'avg_rate': rates
    })
    
    logger.info(f"Generated market data: {len(df)} months")
    logger.info(f"  Rate range: {rates.min():.4f} - {rates.max():.4f}")
    logger.info(f"  Current rate: {rates[-1]:.4f}")
    
    return df


async def train_loss_model(use_sample_data: bool = False):
    """Train loss prediction model."""
    logger.info("\n{'='*60}")
    logger.info("Training Loss Prediction Model")
    logger.info("="*60)
    
    if use_sample_data:
        data = generate_loss_training_data(n_samples=1000)
    else:
        # In production, load from database
        logger.warning("Loading from database not implemented, using sample data")
        data = generate_loss_training_data(n_samples=1000)
    
    # Train model
    loss_model.train(data, target_column='actual_loss_pct')
    
    # Save model
    models_dir = Path("models/predictive")
    models_dir.mkdir(parents=True, exist_ok=True)
    loss_model.save(str(models_dir / "loss_prediction.pkl"))
    
    logger.info("✓ Loss prediction model trained and saved")
    
    return True


async def train_claim_model(use_sample_data: bool = False):
    """Train claim probability model."""
    logger.info("\n" + "="*60)
    logger.info("Training Claim Probability Model")
    logger.info("="*60)
    
    if use_sample_data:
        data = generate_claim_training_data(n_samples=1000)
    else:
        logger.warning("Loading from database not implemented, using sample data")
        data = generate_claim_training_data(n_samples=1000)
    
    # Train model
    claim_model.train(data, target_column='had_claim')
    
    # Save model
    models_dir = Path("models/predictive")
    models_dir.mkdir(parents=True, exist_ok=True)
    claim_model.save(str(models_dir / "claim_probability.pkl"))
    
    logger.info("✓ Claim probability model trained and saved")
    
    return True


async def train_market_model(use_sample_data: bool = False):
    """Train market trend predictor."""
    logger.info("\n" + "="*60)
    logger.info("Training Market Trend Predictor")
    logger.info("="*60)
    
    if use_sample_data:
        data = generate_market_trend_data(n_months=36)
    else:
        logger.warning("Loading from database not implemented, using sample data")
        data = generate_market_trend_data(n_months=36)
    
    # Train model
    market_predictor.train_rate_trend(data)
    
    # Save model
    models_dir = Path("models/predictive")
    models_dir.mkdir(parents=True, exist_ok=True)
    market_predictor.save(str(models_dir / "market_trend.pkl"))
    
    logger.info("✓ Market trend predictor trained and saved")
    
    return True


async def test_predictions(use_sample_data: bool = False):
    """Test all predictive models."""
    logger.info("\n" + "="*60)
    logger.info("Testing Predictive Models")
    logger.info("="*60)
    
    # Test loss prediction
    logger.info("\n1. Testing Loss Prediction:")
    test_data = pd.DataFrame([{
        'cargo_value_usd': 100000,
        'container_count': 2,
        'transit_days': 21,
        'risk_score': 0.65,
        'weather_risk': 0.6,
        'port_congestion_risk': 0.3,
        'carrier_reliability_score': 0.85,
        'historical_loss_rate': 0.02,
        'cargo_type': 'ELECTRONICS',
        'origin_region': 'ASIA',
        'destination_region': 'EUROPE',
        'coverage_type': 'STANDARD'
    }])
    
    loss_results = loss_model.predict(test_data)
    result = loss_results[0]
    logger.info(f"  Expected Loss: {result.prediction:.2%}")
    logger.info(f"  Confidence: {result.confidence:.2f}")
    logger.info(f"  Range: [{result.lower_bound:.2%}, {result.upper_bound:.2%}]")
    logger.info(f"  Explanation: {result.explanation}")
    
    # Test claim probability
    logger.info("\n2. Testing Claim Probability:")
    claim_data = pd.DataFrame([{
        'cargo_value_usd': 100000,
        'container_count': 2,
        'transit_days': 21,
        'risk_score': 0.65,
        'weather_risk': 0.6,
        'carrier_reliability_score': 0.85,
        'customer_claim_history': 1,
        'route_historical_claims': 0.08
    }])
    
    claim_results = claim_model.predict(claim_data)
    prob, conf = claim_results[0]
    logger.info(f"  Claim Probability: {prob:.1%}")
    logger.info(f"  Confidence: {conf:.2f}")
    
    # Test market trend
    logger.info("\n3. Testing Market Trend Prediction:")
    historical_data = generate_market_trend_data(n_months=24)
    predictions = market_predictor.predict_rate_trend(historical_data, months_ahead=6)
    
    logger.info("  Predictions for next 6 months:")
    for pred in predictions:
        logger.info(f"    {pred['month']}: {pred['predicted_rate']:.4f} "
                   f"({pred['change_from_current']:+.1%}) "
                   f"confidence: {pred['confidence']:.2f}")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Train predictive models')
    parser.add_argument(
        '--sample-data',
        action='store_true',
        help='Use synthetic sample data'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run test predictions after training'
    )
    parser.add_argument(
        '--model',
        choices=['loss', 'claim', 'market', 'all'],
        default='all',
        help='Which model to train'
    )
    
    args = parser.parse_args()
    
    try:
        if args.model in ['loss', 'all']:
            await train_loss_model(use_sample_data=args.sample_data)
        
        if args.model in ['claim', 'all']:
            await train_claim_model(use_sample_data=args.sample_data)
        
        if args.model in ['market', 'all']:
            await train_market_model(use_sample_data=args.sample_data)
        
        # Test if requested
        if args.test:
            await test_predictions(use_sample_data=args.sample_data)
        
        logger.info("\n" + "="*60)
        logger.info("✓ Training Complete!")
        logger.info("="*60)
        logger.info("\nModels saved to: models/predictive/")
        logger.info("  - loss_prediction.pkl")
        logger.info("  - claim_probability.pkl")
        logger.info("  - market_trend.pkl")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
