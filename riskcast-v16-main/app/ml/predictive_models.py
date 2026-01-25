"""
Predictive Analytics Models

Features:
1. Loss prediction model
2. Claim probability forecasting
3. Market trend prediction
4. Premium optimization
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import json

from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, roc_auc_score

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    xgb = None

import joblib

from app.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class PredictionResult:
    """Prediction result with confidence intervals."""
    prediction: float
    confidence: float
    lower_bound: float
    upper_bound: float
    feature_importance: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class LossPredictionModel:
    """
    Predicts expected loss for a shipment/policy.
    
    Uses gradient boosting with quantile regression for confidence intervals.
    Provides point estimates and uncertainty quantification.
    """
    
    def __init__(self):
        """Initialize loss prediction model."""
        if XGBOOST_AVAILABLE:
            self.model_mean: Optional[xgb.XGBRegressor] = None
            self.model_lower: Optional[xgb.XGBRegressor] = None
            self.model_upper: Optional[xgb.XGBRegressor] = None
        else:
            self.model_mean: Optional[GradientBoostingRegressor] = None
            self.model_lower: Optional[GradientBoostingRegressor] = None
            self.model_upper: Optional[GradientBoostingRegressor] = None
        
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.use_xgboost = XGBOOST_AVAILABLE
    
    def _prepare_features(self, data: pd.DataFrame, training: bool = False) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare features for training/prediction.
        
        Args:
            data: Input DataFrame
            training: Whether in training mode (fit encoders)
            
        Returns:
            Feature array and feature names
        """
        # Numerical features
        feature_columns = [
            'cargo_value_usd', 'container_count', 'transit_days',
            'risk_score', 'weather_risk', 'port_congestion_risk',
            'carrier_reliability_score', 'historical_loss_rate'
        ]
        
        # Categorical features
        categorical_columns = [
            'cargo_type', 'origin_region', 'destination_region', 'coverage_type'
        ]
        
        # Handle categorical features
        for col in categorical_columns:
            if col in data.columns:
                if training and col not in self.label_encoders:
                    # Fit encoder during training
                    self.label_encoders[col] = LabelEncoder()
                    data[f'{col}_encoded'] = self.label_encoders[col].fit_transform(
                        data[col].fillna('UNKNOWN')
                    )
                elif col in self.label_encoders:
                    # Transform using existing encoder
                    def safe_transform(x):
                        if pd.isna(x) or x not in self.label_encoders[col].classes_:
                            return -1  # Unknown category
                        return self.label_encoders[col].transform([x])[0]
                    
                    data[f'{col}_encoded'] = data[col].apply(safe_transform)
                
                feature_columns.append(f'{col}_encoded')
        
        # Select available features
        available_features = [c for c in feature_columns if c in data.columns]
        
        if not available_features:
            raise ValueError("No features available in data")
        
        X = data[available_features].fillna(0).values
        
        return X, available_features
    
    def train(self, data: pd.DataFrame, target_column: str = 'actual_loss_pct'):
        """
        Train the loss prediction model.
        
        Args:
            data: Training data with features and actual losses
            target_column: Column containing actual loss percentage (0-1)
        """
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        # Prepare features
        X, self.feature_names = self._prepare_features(data, training=True)
        y = data[target_column].values
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Split for validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        if self.use_xgboost and XGBOOST_AVAILABLE:
            # Train XGBoost models
            # Mean prediction
            self.model_mean = xgb.XGBRegressor(
                objective='reg:squarederror',
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.model_mean.fit(X_train, y_train)
            
            # Lower quantile (10th percentile)
            self.model_lower = xgb.XGBRegressor(
                objective='reg:quantileerror',
                quantile_alpha=0.1,
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.model_lower.fit(X_train, y_train)
            
            # Upper quantile (90th percentile)
            self.model_upper = xgb.XGBRegressor(
                objective='reg:quantileerror',
                quantile_alpha=0.9,
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.model_upper.fit(X_train, y_train)
        else:
            # Fallback to scikit-learn GradientBoosting
            logger.warning("XGBoost not available, using GradientBoostingRegressor")
            
            self.model_mean = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.model_mean.fit(X_train, y_train)
            
            # Approximate quantiles with loss='quantile'
            self.model_lower = GradientBoostingRegressor(
                loss='quantile',
                alpha=0.1,
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.model_lower.fit(X_train, y_train)
            
            self.model_upper = GradientBoostingRegressor(
                loss='quantile',
                alpha=0.9,
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.model_upper.fit(X_train, y_train)
        
        # Evaluate on validation set
        y_pred = self.model_mean.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model_mean, X_scaled, y, 
            cv=5, scoring='neg_mean_absolute_error'
        )
        
        logger.info(
            "Loss prediction model trained",
            val_mae=f"{mae:.4f}",
            cv_mae=f"{-cv_scores.mean():.4f}",
            cv_std=f"{cv_scores.std():.4f}",
            n_features=len(self.feature_names),
            use_xgboost=self.use_xgboost
        )
    
    def predict(self, data: pd.DataFrame) -> List[PredictionResult]:
        """
        Predict expected loss with confidence intervals.
        
        Args:
            data: Input data with features
            
        Returns:
            List of PredictionResult objects
        """
        if self.model_mean is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Prepare features
        X, _ = self._prepare_features(data, training=False)
        X_scaled = self.scaler.transform(X)
        
        # Get predictions
        mean_pred = self.model_mean.predict(X_scaled)
        lower_pred = self.model_lower.predict(X_scaled)
        upper_pred = self.model_upper.predict(X_scaled)
        
        # Get feature importance
        if hasattr(self.model_mean, 'feature_importances_'):
            importance = dict(zip(
                self.feature_names,
                self.model_mean.feature_importances_
            ))
        else:
            importance = {}
        
        results = []
        for i in range(len(mean_pred)):
            # Calculate confidence based on interval width
            interval_width = upper_pred[i] - lower_pred[i]
            confidence = max(0, min(1, 1 - (interval_width * 10)))  # Narrower = higher confidence
            
            # Generate explanation
            explanation = self._generate_explanation(
                mean_pred[i], 
                importance, 
                data.iloc[i] if hasattr(data, 'iloc') else {}
            )
            
            results.append(PredictionResult(
                prediction=float(np.clip(mean_pred[i], 0, 1)),  # Ensure 0-1 range
                confidence=float(confidence),
                lower_bound=float(max(0, lower_pred[i])),
                upper_bound=float(min(1, upper_pred[i])),
                feature_importance=importance,
                explanation=explanation,
                metadata={
                    "model_type": "xgboost" if self.use_xgboost else "gradient_boosting",
                    "interval_width": float(interval_width)
                }
            ))
        
        return results
    
    def _generate_explanation(
        self, 
        prediction: float, 
        importance: Dict[str, float], 
        row: Any
    ) -> str:
        """Generate human-readable explanation."""
        # Determine risk level
        if prediction < 0.02:
            risk_level = "LOW"
        elif prediction < 0.05:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Top contributing factors
        if importance:
            top_factors = sorted(
                importance.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            factors_str = ", ".join([k for k, v in top_factors])
        else:
            factors_str = "multiple factors"
        
        return f"Expected loss: {prediction:.2%} ({risk_level} risk). Key factors: {factors_str}"
    
    def save(self, path: str):
        """Save model to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "model_mean": self.model_mean,
            "model_lower": self.model_lower,
            "model_upper": self.model_upper,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "label_encoders": self.label_encoders,
            "use_xgboost": self.use_xgboost
        }
        joblib.dump(model_data, path)
        
        logger.info("Loss prediction model saved", path=path)
    
    def load(self, path: str):
        """Load model from disk."""
        model_data = joblib.load(path)
        self.model_mean = model_data["model_mean"]
        self.model_lower = model_data["model_lower"]
        self.model_upper = model_data["model_upper"]
        self.scaler = model_data["scaler"]
        self.feature_names = model_data["feature_names"]
        self.label_encoders = model_data["label_encoders"]
        self.use_xgboost = model_data.get("use_xgboost", False)
        
        logger.info("Loss prediction model loaded", path=path)


class ClaimProbabilityModel:
    """
    Predicts probability of claim being filed for a policy.
    
    Uses Random Forest classifier with calibrated probabilities.
    """
    
    def __init__(self):
        """Initialize claim probability model."""
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
    
    def train(self, data: pd.DataFrame, target_column: str = 'had_claim'):
        """
        Train claim probability model.
        
        Args:
            data: Training data
            target_column: Binary target (0/1) indicating if claim was filed
        """
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found")
        
        # Prepare features
        feature_columns = [
            'cargo_value_usd', 'container_count', 'transit_days',
            'risk_score', 'weather_risk', 'carrier_reliability_score',
            'customer_claim_history', 'route_historical_claims'
        ]
        
        available_features = [c for c in feature_columns if c in data.columns]
        
        if not available_features:
            raise ValueError("No features available")
        
        X = data[available_features].fillna(0).values
        y = data[target_column].values
        
        self.feature_names = available_features
        
        # Scale
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Split for validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred_proba = self.model.predict_proba(X_val)[:, 1]
        try:
            auc = roc_auc_score(y_val, y_pred_proba)
        except:
            auc = 0.5
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_scaled, y, 
            cv=5, scoring='roc_auc'
        )
        
        logger.info(
            "Claim probability model trained",
            val_auc=f"{auc:.4f}",
            cv_auc=f"{cv_scores.mean():.4f}",
            cv_std=f"{cv_scores.std():.4f}",
            n_features=len(self.feature_names)
        )
    
    def predict(self, data: pd.DataFrame) -> List[Tuple[float, float]]:
        """
        Predict claim probability.
        
        Args:
            data: Input data
            
        Returns:
            List of (probability, confidence) tuples
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        available_features = [c for c in self.feature_names if c in data.columns]
        X = data[available_features].fillna(0).values
        X_scaled = self.scaler.transform(X)
        
        # Get probabilities
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        
        # Estimate confidence from tree agreement
        tree_predictions = np.array([
            tree.predict_proba(X_scaled)[:, 1] 
            for tree in self.model.estimators_
        ])
        
        # High agreement = high confidence
        confidence = 1 - tree_predictions.std(axis=0)
        confidence = np.clip(confidence, 0, 1)
        
        return list(zip(probabilities.tolist(), confidence.tolist()))
    
    def save(self, path: str):
        """Save model to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_names": self.feature_names
        }
        joblib.dump(model_data, path)
        
        logger.info("Claim probability model saved", path=path)
    
    def load(self, path: str):
        """Load model from disk."""
        model_data = joblib.load(path)
        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.feature_names = model_data["feature_names"]
        
        logger.info("Claim probability model loaded", path=path)


class MarketTrendPredictor:
    """
    Predicts market trends for pricing and demand.
    
    Uses time series features and gradient boosting for trend forecasting.
    """
    
    def __init__(self):
        """Initialize market trend predictor."""
        if XGBOOST_AVAILABLE:
            self.rate_model: Optional[xgb.XGBRegressor] = None
            self.demand_model: Optional[xgb.XGBRegressor] = None
        else:
            self.rate_model: Optional[GradientBoostingRegressor] = None
            self.demand_model: Optional[GradientBoostingRegressor] = None
        
        self.use_xgboost = XGBOOST_AVAILABLE
    
    def train_rate_trend(self, historical_rates: pd.DataFrame):
        """
        Train model to predict rate trends.
        
        Args:
            historical_rates: DataFrame with 'date' and 'avg_rate' columns
        """
        if 'date' not in historical_rates.columns or 'avg_rate' not in historical_rates.columns:
            raise ValueError("historical_rates must have 'date' and 'avg_rate' columns")
        
        # Create time-based features
        historical_rates['date'] = pd.to_datetime(historical_rates['date'])
        historical_rates['month'] = historical_rates['date'].dt.month
        historical_rates['quarter'] = historical_rates['date'].dt.quarter
        historical_rates['year'] = historical_rates['date'].dt.year
        historical_rates['day_of_year'] = historical_rates['date'].dt.dayofyear
        
        # Lag features
        for lag in [1, 3, 6, 12]:
            historical_rates[f'rate_lag_{lag}'] = historical_rates['avg_rate'].shift(lag)
        
        # Rolling statistics
        historical_rates['rate_ma_3'] = historical_rates['avg_rate'].rolling(3, min_periods=1).mean()
        historical_rates['rate_ma_12'] = historical_rates['avg_rate'].rolling(12, min_periods=1).mean()
        historical_rates['rate_std_6'] = historical_rates['avg_rate'].rolling(6, min_periods=1).std().fillna(0)
        
        # Drop initial NaN rows from lags
        historical_rates = historical_rates.dropna(subset=['rate_lag_1'])
        
        if len(historical_rates) < 20:
            raise ValueError("Insufficient data for training (need at least 20 rows)")
        
        feature_columns = [
            'month', 'quarter', 'year', 'day_of_year',
            'rate_lag_1', 'rate_lag_3', 'rate_lag_6', 'rate_lag_12',
            'rate_ma_3', 'rate_ma_12', 'rate_std_6'
        ]
        
        X = historical_rates[feature_columns].values
        y = historical_rates['avg_rate'].values
        
        if self.use_xgboost and XGBOOST_AVAILABLE:
            self.rate_model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:
            self.rate_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        
        self.rate_model.fit(X, y)
        
        logger.info("Market rate trend model trained", n_samples=len(X))
    
    def predict_rate_trend(
        self,
        current_data: pd.DataFrame,
        months_ahead: int = 6
    ) -> List[Dict]:
        """
        Predict rate trends for upcoming months.
        
        Args:
            current_data: Recent historical data with 'date' and 'avg_rate'
            months_ahead: Number of months to forecast
            
        Returns:
            List of predictions with dates, rates, and confidence
        """
        if self.rate_model is None:
            raise ValueError("Rate model not trained. Call train_rate_trend() first.")
        
        predictions = []
        current_date = datetime.utcnow()
        
        # Use last known values for lag features
        if 'avg_rate' in current_data.columns:
            last_rate = current_data['avg_rate'].iloc[-1]
            rates_history = current_data['avg_rate'].tolist()[-12:]
        else:
            last_rate = 0.008  # Default 0.8% rate
            rates_history = [last_rate]
        
        for i in range(months_ahead):
            future_date = current_date + timedelta(days=30 * (i + 1))
            
            # Build feature vector
            features = [
                future_date.month,
                (future_date.month - 1) // 3 + 1,  # quarter
                future_date.year,
                future_date.timetuple().tm_yday,   # day of year
                rates_history[-1] if len(rates_history) >= 1 else last_rate,
                rates_history[-3] if len(rates_history) >= 3 else last_rate,
                rates_history[-6] if len(rates_history) >= 6 else last_rate,
                rates_history[-12] if len(rates_history) >= 12 else last_rate,
                np.mean(rates_history[-3:]) if len(rates_history) >= 3 else last_rate,
                np.mean(rates_history[-12:]) if len(rates_history) >= 12 else last_rate,
                np.std(rates_history[-6:]) if len(rates_history) >= 6 else 0
            ]
            
            predicted_rate = self.rate_model.predict([features])[0]
            predicted_rate = float(np.clip(predicted_rate, 0.001, 0.05))  # Reasonable bounds
            
            # Calculate change
            change_pct = (predicted_rate - last_rate) / last_rate if last_rate > 0 else 0
            
            # Confidence decreases with forecast horizon
            confidence = max(0.5, 0.9 - (i * 0.05))
            
            predictions.append({
                'date': future_date.isoformat(),
                'month': future_date.strftime('%Y-%m'),
                'predicted_rate': predicted_rate,
                'change_from_current': float(change_pct),
                'confidence': confidence,
                'forecast_horizon_months': i + 1
            })
            
            # Add to history for next prediction
            rates_history.append(predicted_rate)
            if len(rates_history) > 12:
                rates_history.pop(0)
        
        return predictions
    
    def save(self, path: str):
        """Save model to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "rate_model": self.rate_model,
            "demand_model": self.demand_model,
            "use_xgboost": self.use_xgboost
        }
        joblib.dump(model_data, path)
        
        logger.info("Market trend predictor saved", path=path)
    
    def load(self, path: str):
        """Load model from disk."""
        model_data = joblib.load(path)
        self.rate_model = model_data["rate_model"]
        self.demand_model = model_data.get("demand_model")
        self.use_xgboost = model_data.get("use_xgboost", False)
        
        logger.info("Market trend predictor loaded", path=path)


class PremiumOptimizer:
    """
    Optimizes premium pricing based on market conditions and risk.
    
    Combines loss predictions, claim probabilities, and market trends
    to recommend optimal premium pricing.
    """
    
    def __init__(
        self,
        loss_model: LossPredictionModel,
        claim_model: ClaimProbabilityModel
    ):
        """
        Initialize premium optimizer.
        
        Args:
            loss_model: Trained loss prediction model
            claim_model: Trained claim probability model
        """
        self.loss_model = loss_model
        self.claim_model = claim_model
        
        # Pricing parameters (industry standards)
        self.target_loss_ratio = 0.65  # Premium should cover 65% loss ratio
        self.expense_ratio = 0.25       # 25% for expenses
        self.profit_margin = 0.10       # 10% profit margin
    
    def optimize_premium(
        self,
        policy_data: pd.DataFrame,
        market_rate: float,
        competitive_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal premium considering risk, market, and competition.
        
        Args:
            policy_data: Policy/shipment features
            market_rate: Current market rate (per mille)
            competitive_rate: Optional competitor rate (per mille)
            
        Returns:
            Dict with pricing recommendations and components
        """
        # Get risk-based predictions
        loss_predictions = self.loss_model.predict(policy_data)
        claim_probs = self.claim_model.predict(policy_data)
        
        results = []
        
        for i, (loss_pred, (claim_prob, claim_conf)) in enumerate(zip(loss_predictions, claim_probs)):
            # Extract cargo value
            if 'cargo_value_usd' in policy_data.columns:
                cargo_value = float(policy_data.iloc[i]['cargo_value_usd'])
            else:
                cargo_value = 100000.0  # Default
            
            # Calculate actuarial premium
            expected_loss = loss_pred.prediction * cargo_value * claim_prob
            
            # Apply loss ratio to get premium needed to cover losses
            actuarial_premium = expected_loss / self.target_loss_ratio if self.target_loss_ratio > 0 else expected_loss
            
            # Add expense and profit loading
            gross_premium = actuarial_premium / (1 - self.expense_ratio - self.profit_margin)
            
            # Calculate rate per mille
            actuarial_rate = gross_premium / cargo_value * 1000 if cargo_value > 0 else 0
            
            # Adjust for market conditions (70% risk-based, 30% market)
            market_adjusted_rate = actuarial_rate * 0.7 + market_rate * 0.3
            
            # Consider competition if available
            if competitive_rate:
                # 60% market-adjusted, 40% competitive
                competitive_adjusted_rate = market_adjusted_rate * 0.6 + competitive_rate * 0.4
            else:
                competitive_adjusted_rate = market_adjusted_rate
            
            # Apply bounds to stay profitable and competitive
            min_rate = actuarial_rate * 0.8  # Don't go below 80% of actuarial
            max_rate = market_rate * 1.5     # Don't exceed 150% of market
            
            final_rate = max(min_rate, min(competitive_adjusted_rate, max_rate))
            final_premium = final_rate * cargo_value / 1000
            
            # Calculate overall confidence
            overall_confidence = (loss_pred.confidence + claim_conf) / 2
            
            results.append({
                'cargo_value_usd': cargo_value,
                'expected_loss_pct': loss_pred.prediction,
                'expected_loss_amount': expected_loss,
                'claim_probability': claim_prob,
                'actuarial_rate': actuarial_rate,
                'market_rate': market_rate,
                'competitive_rate': competitive_rate,
                'recommended_rate': final_rate,
                'recommended_premium': final_premium,
                'confidence': overall_confidence,
                'rate_components': {
                    'risk_based': actuarial_rate,
                    'market_adjusted': market_adjusted_rate,
                    'competitive_adjusted': competitive_adjusted_rate if competitive_rate else None,
                    'final': final_rate
                },
                'pricing_factors': {
                    'target_loss_ratio': self.target_loss_ratio,
                    'expense_ratio': self.expense_ratio,
                    'profit_margin': self.profit_margin
                }
            })
        
        return results[0] if len(results) == 1 else results
    
    def save_parameters(self, path: str):
        """Save pricing parameters."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        params = {
            "target_loss_ratio": self.target_loss_ratio,
            "expense_ratio": self.expense_ratio,
            "profit_margin": self.profit_margin
        }
        
        with open(path, 'w') as f:
            json.dump(params, f, indent=2)
        
        logger.info("Premium optimizer parameters saved", path=path)
    
    def load_parameters(self, path: str):
        """Load pricing parameters."""
        with open(path, 'r') as f:
            params = json.load(f)
        
        self.target_loss_ratio = params["target_loss_ratio"]
        self.expense_ratio = params["expense_ratio"]
        self.profit_margin = params["profit_margin"]
        
        logger.info("Premium optimizer parameters loaded", path=path)


# Global instances (to be initialized after training)
loss_model = LossPredictionModel()
claim_model = ClaimProbabilityModel()
market_predictor = MarketTrendPredictor()
