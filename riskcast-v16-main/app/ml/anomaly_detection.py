"""
ML-Powered Anomaly Detection

Features:
1. Isolation Forest for outlier detection
2. Autoencoder for pattern learning
3. Time-series anomaly detection
4. Feature engineering
5. Model training pipeline
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import joblib
import json
from pathlib import Path

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import DBSCAN

try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    tf = None
    keras = None

from app.core.logging import get_logger


logger = get_logger(__name__)


class AnomalyType(str, Enum):
    """Types of anomalies detected."""
    FRAUD_SUSPECT = "fraud_suspect"
    UNUSUAL_PATTERN = "unusual_pattern"
    OUTLIER_VALUE = "outlier_value"
    BEHAVIOR_CHANGE = "behavior_change"
    DATA_QUALITY = "data_quality"


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    is_anomaly: bool
    anomaly_score: float  # 0-1, higher = more anomalous
    anomaly_type: Optional[AnomalyType]
    confidence: float
    features_contributing: List[str]
    explanation: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeatureEngineering:
    """
    Feature engineering for anomaly detection.
    
    Extracts relevant features from quotes, claims, and customer behavior
    for machine learning models.
    """
    
    @staticmethod
    def extract_quote_features(quote: dict) -> np.ndarray:
        """
        Extract features from a quote for anomaly detection.
        
        Args:
            quote: Quote dictionary
            
        Returns:
            numpy array of features
        """
        features = []
        
        # Value features
        cargo_value = float(quote.get('cargo_value_usd', 0))
        premium = float(quote.get('total_premium_usd', 0))
        
        features.append(cargo_value)
        features.append(premium)
        
        # Calculate rate per mille
        rate_per_mille = (premium / cargo_value * 1000) if cargo_value > 0 else 0
        features.append(rate_per_mille)
        
        # Risk features
        features.append(float(quote.get('risk_score', 0.5)))
        
        # Container count
        features.append(int(quote.get('container_count', 1)))
        
        # Transit time
        features.append(int(quote.get('transit_days', 21)))
        
        # Time-based features
        created_at = quote.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                created_at = None
        
        if created_at and isinstance(created_at, datetime):
            features.append(created_at.hour)
            features.append(created_at.weekday())
        else:
            features.extend([12, 3])  # Default values (noon, Wednesday)
        
        return np.array(features, dtype=float)
    
    @staticmethod
    def extract_claim_features(claim: dict, policy: dict) -> np.ndarray:
        """
        Extract features from a claim for fraud detection.
        
        Args:
            claim: Claim dictionary
            policy: Policy dictionary
            
        Returns:
            numpy array of features
        """
        features = []
        
        # Claim amount relative to coverage
        coverage = float(policy.get('coverage_limit', policy.get('cargo_value_usd', 1)))
        claimed = float(claim.get('claimed_amount', 0))
        claim_ratio = claimed / coverage if coverage > 0 else 0
        features.append(claim_ratio)
        
        # Time since policy inception
        policy_start = policy.get('effective_from')
        loss_date = claim.get('loss_date')
        
        if policy_start and loss_date:
            if isinstance(policy_start, str):
                try:
                    policy_start = datetime.fromisoformat(policy_start.replace('Z', '+00:00'))
                except:
                    policy_start = None
            if isinstance(loss_date, str):
                try:
                    loss_date = datetime.fromisoformat(loss_date.replace('Z', '+00:00'))
                except:
                    loss_date = None
            
            if policy_start and loss_date and isinstance(policy_start, datetime) and isinstance(loss_date, datetime):
                days_since_inception = (loss_date - policy_start).days
                features.append(days_since_inception)
            else:
                features.append(30)  # Default
        else:
            features.append(30)  # Default
        
        # Time to report
        filed_at = claim.get('filed_at')
        if loss_date and filed_at:
            if isinstance(filed_at, str):
                try:
                    filed_at = datetime.fromisoformat(filed_at.replace('Z', '+00:00'))
                except:
                    filed_at = None
            if isinstance(loss_date, str):
                try:
                    loss_date = datetime.fromisoformat(loss_date.replace('Z', '+00:00'))
                except:
                    loss_date = None
            
            if filed_at and loss_date and isinstance(filed_at, datetime) and isinstance(loss_date, datetime):
                days_to_report = (filed_at - loss_date).days
                features.append(max(0, days_to_report))  # Ensure non-negative
            else:
                features.append(3)  # Default
        else:
            features.append(3)  # Default
        
        # Loss type encoding
        loss_types = ['CARGO_DAMAGE', 'CARGO_LOSS', 'CONTAMINATION', 'THEFT', 'WATER_DAMAGE', 'DELAY']
        loss_type = claim.get('loss_type', 'OTHER')
        loss_type_encoded = loss_types.index(loss_type) if loss_type in loss_types else len(loss_types)
        features.append(float(loss_type_encoded))
        
        # Premium paid
        features.append(float(policy.get('total_premium', policy.get('total_premium_usd', 0))))
        
        # Number of previous claims by same customer
        features.append(int(claim.get('customer_previous_claims', 0)))
        
        return np.array(features, dtype=float)
    
    @staticmethod
    def extract_customer_behavior_features(customer: dict, transactions: List[dict]) -> np.ndarray:
        """
        Extract customer behavior features.
        
        Args:
            customer: Customer dictionary
            transactions: List of transaction dictionaries
            
        Returns:
            numpy array of features
        """
        features = []
        
        if not transactions:
            return np.zeros(10, dtype=float)  # Return default features
        
        # Transaction frequency
        features.append(float(len(transactions)))
        
        # Average transaction value
        values = [float(t.get('cargo_value_usd', 0)) for t in transactions]
        features.append(np.mean(values) if values else 0.0)
        features.append(np.std(values) if len(values) > 1 else 0.0)
        
        # Time between transactions
        dates = []
        for t in transactions:
            created_at = t.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        dates.append(created_at)
                    except:
                        pass
                elif isinstance(created_at, datetime):
                    dates.append(created_at)
        
        dates = sorted(dates)
        
        if len(dates) > 1:
            intervals = []
            for i in range(1, len(dates)):
                interval_days = (dates[i] - dates[i-1]).days
                intervals.append(interval_days)
            features.append(np.mean(intervals))
            features.append(np.std(intervals) if len(intervals) > 1 else 0.0)
        else:
            features.extend([30.0, 10.0])  # Default
        
        # Route diversity
        routes = set(
            f"{t.get('origin_port')}-{t.get('destination_port')}" 
            for t in transactions 
            if t.get('origin_port') and t.get('destination_port')
        )
        features.append(float(len(routes)))
        
        # Cargo type diversity
        cargo_types = set(t.get('cargo_type') for t in transactions if t.get('cargo_type'))
        features.append(float(len(cargo_types)))
        
        # Quote acceptance rate
        accepted = sum(1 for t in transactions if t.get('status') == 'ACCEPTED')
        acceptance_rate = accepted / len(transactions) if transactions else 0.0
        features.append(acceptance_rate)
        
        # Claim ratio
        claims = sum(1 for t in transactions if t.get('has_claim'))
        claim_ratio = claims / len(transactions) if transactions else 0.0
        features.append(claim_ratio)
        
        return np.array(features, dtype=float)


class IsolationForestDetector:
    """
    Isolation Forest based anomaly detector.
    
    Uses scikit-learn's Isolation Forest algorithm to detect outliers
    in multi-dimensional feature space.
    """
    
    def __init__(self, contamination: float = 0.05, n_estimators: int = 100):
        """
        Initialize Isolation Forest detector.
        
        Args:
            contamination: Expected proportion of outliers (0.0 to 0.5)
            n_estimators: Number of trees in the forest
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
    
    def train(self, X: np.ndarray, feature_names: List[str] = None):
        """
        Train the Isolation Forest model.
        
        Args:
            X: Training data (n_samples, n_features)
            feature_names: Names of features
        """
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_scaled)
        
        logger.info(
            "Isolation Forest trained",
            n_samples=X.shape[0],
            n_features=X.shape[1],
            contamination=self.contamination
        )
    
    def predict(self, X: np.ndarray) -> List[AnomalyResult]:
        """
        Predict anomalies.
        
        Args:
            X: Input data (n_samples, n_features)
            
        Returns:
            List of AnomalyResult objects
        """
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained. Call train() first.")
        
        X_scaled = self.scaler.transform(X)
        
        # Get predictions (-1 = anomaly, 1 = normal)
        predictions = self.model.predict(X_scaled)
        
        # Get anomaly scores (more negative = more anomalous)
        scores = self.model.decision_function(X_scaled)
        
        # Normalize scores to 0-1 (higher = more anomalous)
        min_score = scores.min()
        max_score = scores.max()
        score_range = max_score - min_score + 1e-10
        normalized_scores = 1 - (scores - min_score) / score_range
        
        results = []
        for i, (pred, score, norm_score) in enumerate(zip(predictions, scores, normalized_scores)):
            is_anomaly = pred == -1
            
            # Find contributing features
            contributing = self._find_contributing_features(X_scaled[i])
            
            results.append(AnomalyResult(
                is_anomaly=is_anomaly,
                anomaly_score=float(norm_score),
                anomaly_type=AnomalyType.OUTLIER_VALUE if is_anomaly else None,
                confidence=float(abs(score)),
                features_contributing=contributing,
                explanation=self._generate_explanation(is_anomaly, contributing, X[i]),
                metadata={
                    "raw_score": float(score),
                    "normalized_score": float(norm_score),
                    "method": "isolation_forest"
                }
            ))
        
        return results
    
    def _find_contributing_features(self, x: np.ndarray, top_k: int = 3) -> List[str]:
        """
        Find features that contribute most to anomaly score.
        
        Args:
            x: Scaled feature vector
            top_k: Number of top features to return
            
        Returns:
            List of feature names
        """
        # Simple approach: features furthest from mean (which is 0 after scaling)
        deviations = np.abs(x)
        top_indices = np.argsort(deviations)[-top_k:][::-1]
        
        return [self.feature_names[i] for i in top_indices if i < len(self.feature_names)]
    
    def _generate_explanation(
        self,
        is_anomaly: bool,
        contributing_features: List[str],
        original_values: np.ndarray
    ) -> str:
        """
        Generate human-readable explanation.
        
        Args:
            is_anomaly: Whether sample is anomaly
            contributing_features: List of contributing feature names
            original_values: Original (unscaled) feature values
            
        Returns:
            Explanation string
        """
        if not is_anomaly:
            return "No anomaly detected"
        
        feature_details = []
        for feat in contributing_features[:3]:
            if feat in self.feature_names:
                idx = self.feature_names.index(feat)
                if idx < len(original_values):
                    value = original_values[idx]
                    feature_details.append(f"{feat}={value:.2f}")
        
        if feature_details:
            return f"Anomaly detected. Contributing factors: {', '.join(feature_details)}"
        else:
            return "Anomaly detected based on statistical outliers"
    
    def save(self, path: str):
        """
        Save model to disk.
        
        Args:
            path: Path to save model
        """
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "contamination": self.contamination,
            "n_estimators": self.n_estimators
        }
        joblib.dump(model_data, path)
        
        logger.info("Isolation Forest model saved", path=path)
    
    def load(self, path: str):
        """
        Load model from disk.
        
        Args:
            path: Path to load model from
        """
        model_data = joblib.load(path)
        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.feature_names = model_data["feature_names"]
        self.contamination = model_data["contamination"]
        self.n_estimators = model_data.get("n_estimators", 100)
        
        logger.info("Isolation Forest model loaded", path=path)


class AutoencoderAnomalyDetector:
    """
    Autoencoder-based anomaly detection for complex patterns.
    
    Uses a neural network autoencoder to learn normal patterns and detect
    anomalies based on reconstruction error.
    """
    
    def __init__(self, encoding_dim: int = 8, threshold_percentile: float = 95):
        """
        Initialize Autoencoder detector.
        
        Args:
            encoding_dim: Dimension of encoded representation
            threshold_percentile: Percentile for anomaly threshold
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError(
                "TensorFlow is required for AutoencoderAnomalyDetector. "
                "Install with: pip install tensorflow"
            )
        
        self.encoding_dim = encoding_dim
        self.threshold_percentile = threshold_percentile
        self.model = None  # keras.Model when trained
        self.scaler: Optional[StandardScaler] = None
        self.threshold: float = 0.0
        self.feature_names: List[str] = []
    
    def _build_model(self, input_dim: int):
        """
        Build autoencoder architecture.
        
        Args:
            input_dim: Number of input features
            
        Returns:
            Compiled Keras model
        """
        # Encoder
        inputs = keras.Input(shape=(input_dim,))
        x = keras.layers.Dense(32, activation='relu')(inputs)
        x = keras.layers.Dropout(0.2)(x)
        x = keras.layers.Dense(16, activation='relu')(x)
        encoded = keras.layers.Dense(self.encoding_dim, activation='relu', name='encoded')(x)
        
        # Decoder
        x = keras.layers.Dense(16, activation='relu')(encoded)
        x = keras.layers.Dropout(0.2)(x)
        x = keras.layers.Dense(32, activation='relu')(x)
        decoded = keras.layers.Dense(input_dim, activation='linear')(x)
        
        model = keras.Model(inputs, decoded)
        model.compile(optimizer='adam', loss='mse')
        
        return model
    
    def train(
        self,
        X: np.ndarray,
        feature_names: List[str] = None,
        epochs: int = 50,
        validation_split: float = 0.1
    ):
        """
        Train the autoencoder.
        
        Args:
            X: Training data (n_samples, n_features)
            feature_names: Names of features
            epochs: Number of training epochs
            validation_split: Fraction of data for validation
        """
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Build model
        self.model = self._build_model(X.shape[1])
        
        # Train
        history = self.model.fit(
            X_scaled, X_scaled,
            epochs=epochs,
            batch_size=32,
            validation_split=validation_split,
            verbose=0
        )
        
        # Calculate reconstruction errors for threshold
        reconstructed = self.model.predict(X_scaled, verbose=0)
        mse = np.mean(np.square(X_scaled - reconstructed), axis=1)
        
        self.threshold = np.percentile(mse, self.threshold_percentile)
        
        logger.info(
            "Autoencoder trained",
            n_samples=X.shape[0],
            n_features=X.shape[1],
            encoding_dim=self.encoding_dim,
            threshold=f"{self.threshold:.4f}",
            final_loss=f"{history.history['loss'][-1]:.4f}"
        )
    
    def predict(self, X: np.ndarray) -> List[AnomalyResult]:
        """
        Predict anomalies using reconstruction error.
        
        Args:
            X: Input data (n_samples, n_features)
            
        Returns:
            List of AnomalyResult objects
        """
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained. Call train() first.")
        
        X_scaled = self.scaler.transform(X)
        
        # Get reconstructions
        reconstructed = self.model.predict(X_scaled, verbose=0)
        
        # Calculate reconstruction errors
        mse = np.mean(np.square(X_scaled - reconstructed), axis=1)
        
        # Normalize scores
        max_mse = max(mse.max(), self.threshold * 2)
        normalized_scores = np.clip(mse / max_mse, 0, 1)
        
        results = []
        for i, (error, norm_score) in enumerate(zip(mse, normalized_scores)):
            is_anomaly = error > self.threshold
            
            # Find features with highest reconstruction error
            feature_errors = np.square(X_scaled[i] - reconstructed[i])
            top_k = min(3, len(feature_errors))
            top_indices = np.argsort(feature_errors)[-top_k:][::-1]
            
            contributing = [
                self.feature_names[idx] 
                for idx in top_indices 
                if idx < len(self.feature_names)
            ]
            
            # Calculate confidence
            if is_anomaly:
                confidence = float(min(error / self.threshold, 2.0))
            else:
                confidence = float(1 - error / self.threshold)
            
            results.append(AnomalyResult(
                is_anomaly=is_anomaly,
                anomaly_score=float(norm_score),
                anomaly_type=AnomalyType.UNUSUAL_PATTERN if is_anomaly else None,
                confidence=confidence,
                features_contributing=contributing,
                explanation=f"Reconstruction error: {error:.4f} (threshold: {self.threshold:.4f})",
                metadata={
                    "reconstruction_error": float(error),
                    "threshold": float(self.threshold),
                    "method": "autoencoder"
                }
            ))
        
        return results
    
    def save(self, path: str):
        """
        Save model to disk.
        
        Args:
            path: Directory path to save model
        """
        Path(path).mkdir(parents=True, exist_ok=True)
        
        self.model.save(f"{path}/autoencoder.h5")
        
        metadata = {
            "scaler": self.scaler,
            "threshold": self.threshold,
            "encoding_dim": self.encoding_dim,
            "threshold_percentile": self.threshold_percentile,
            "feature_names": self.feature_names
        }
        joblib.dump(metadata, f"{path}/metadata.pkl")
        
        logger.info("Autoencoder model saved", path=path)
    
    def load(self, path: str):
        """
        Load model from disk.
        
        Args:
            path: Directory path to load model from
        """
        self.model = keras.models.load_model(f"{path}/autoencoder.h5")
        
        metadata = joblib.load(f"{path}/metadata.pkl")
        self.scaler = metadata["scaler"]
        self.threshold = metadata["threshold"]
        self.encoding_dim = metadata["encoding_dim"]
        self.threshold_percentile = metadata.get("threshold_percentile", 95)
        self.feature_names = metadata.get("feature_names", [])
        
        logger.info("Autoencoder model loaded", path=path)


class FraudDetectionService:
    """
    Fraud detection service combining multiple detection methods.
    
    Uses ensemble approach with Isolation Forest and Autoencoder
    for robust fraud detection.
    """
    
    def __init__(self, models_dir: str = "models/fraud"):
        """
        Initialize Fraud Detection Service.
        
        Args:
            models_dir: Directory to save/load models
        """
        self.models_dir = Path(models_dir)
        self.isolation_forest = IsolationForestDetector()
        
        # Only initialize autoencoder if TensorFlow is available
        if TENSORFLOW_AVAILABLE:
            self.autoencoder = AutoencoderAnomalyDetector()
            self.use_autoencoder = True
        else:
            self.autoencoder = None
            self.use_autoencoder = False
            logger.warning("TensorFlow not available. Autoencoder will not be used.")
        
        self.is_trained = False
        self.feature_names = [
            'claim_coverage_ratio',
            'days_since_inception',
            'days_to_report',
            'loss_type',
            'premium_paid',
            'previous_claims'
        ]
    
    async def train_models(self, claims_data: List[dict] = None):
        """
        Train fraud detection models on historical data.
        
        Args:
            claims_data: List of claim/policy pairs, or None to load from database
        """
        # If no data provided, load from database
        if claims_data is None:
            from app.db.session import get_db
            async with get_db() as db:
                claims_data = await self._load_claims_data(db)
        
        if len(claims_data) < 100:
            logger.warning(
                "Insufficient data for training fraud detection",
                n_samples=len(claims_data),
                required=100
            )
            return False
        
        # Extract features
        features = []
        for item in claims_data:
            try:
                feat = FeatureEngineering.extract_claim_features(
                    item['claim'],
                    item['policy']
                )
                features.append(feat)
            except Exception as e:
                logger.error(f"Error extracting features: {e}")
                continue
        
        if not features:
            logger.error("No features extracted from claims data")
            return False
        
        features = np.array(features)
        
        # Train Isolation Forest
        self.isolation_forest.train(features, self.feature_names)
        
        # Train Autoencoder if available
        if self.use_autoencoder and self.autoencoder:
            try:
                self.autoencoder.train(features, self.feature_names)
            except Exception as e:
                logger.error(f"Error training autoencoder: {e}")
                self.use_autoencoder = False
        
        self.is_trained = True
        
        # Save models
        try:
            self.save_models()
        except Exception as e:
            logger.error(f"Error saving models: {e}")
        
        logger.info(
            "Fraud detection models trained",
            n_samples=len(features),
            use_autoencoder=self.use_autoencoder
        )
        
        return True
    
    async def _load_claims_data(self, db) -> List[dict]:
        """
        Load claims with policy data for training.
        
        Args:
            db: Database session
            
        Returns:
            List of claim/policy dictionaries
        """
        try:
            # This is a simplified version
            # In production, would use proper SQLAlchemy queries
            from sqlalchemy import text
            
            query = text("""
                SELECT 
                    c.id as claim_id,
                    c.claimed_amount,
                    c.loss_date,
                    c.filed_at,
                    c.loss_type,
                    p.id as policy_id,
                    p.coverage_limit,
                    p.cargo_value_usd,
                    p.effective_from,
                    p.total_premium_usd,
                    COUNT(c2.id) as customer_previous_claims
                FROM claims c
                JOIN policies p ON c.policy_id = p.id
                LEFT JOIN claims c2 ON c2.customer_id = c.customer_id AND c2.id < c.id
                WHERE c.created_at > NOW() - INTERVAL '2 years'
                GROUP BY c.id, p.id
                LIMIT 10000
            """)
            
            result = await db.execute(query)
            rows = result.fetchall()
            
            claims_data = []
            for row in rows:
                row_dict = dict(row._mapping)
                claims_data.append({
                    'claim': {
                        'id': row_dict.get('claim_id'),
                        'claimed_amount': row_dict.get('claimed_amount'),
                        'loss_date': row_dict.get('loss_date'),
                        'filed_at': row_dict.get('filed_at'),
                        'loss_type': row_dict.get('loss_type'),
                        'customer_previous_claims': row_dict.get('customer_previous_claims', 0)
                    },
                    'policy': {
                        'id': row_dict.get('policy_id'),
                        'coverage_limit': row_dict.get('coverage_limit', row_dict.get('cargo_value_usd')),
                        'cargo_value_usd': row_dict.get('cargo_value_usd'),
                        'effective_from': row_dict.get('effective_from'),
                        'total_premium_usd': row_dict.get('total_premium_usd'),
                        'total_premium': row_dict.get('total_premium_usd')
                    }
                })
            
            return claims_data
            
        except Exception as e:
            logger.error(f"Error loading claims data: {e}")
            return []
    
    async def detect_fraud(self, claim: dict, policy: dict) -> AnomalyResult:
        """
        Detect potential fraud in a claim.
        
        Args:
            claim: Claim dictionary
            policy: Policy dictionary
            
        Returns:
            AnomalyResult with fraud assessment
        """
        if not self.is_trained:
            # Try to load models
            try:
                self.load_models()
            except:
                return AnomalyResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    anomaly_type=None,
                    confidence=0.0,
                    features_contributing=[],
                    explanation="Fraud detection model not trained",
                    metadata={"error": "model_not_trained"}
                )
        
        try:
            features = FeatureEngineering.extract_claim_features(claim, policy)
            features = features.reshape(1, -1)
            
            # Get predictions from Isolation Forest
            if_result = self.isolation_forest.predict(features)[0]
            
            # Get predictions from Autoencoder if available
            if self.use_autoencoder and self.autoencoder:
                ae_result = self.autoencoder.predict(features)[0]
                
                # Combine results (ensemble approach)
                combined_score = (if_result.anomaly_score + ae_result.anomaly_score) / 2
                is_anomaly = if_result.is_anomaly or ae_result.is_anomaly
                
                # Combine contributing features
                contributing = list(set(
                    if_result.features_contributing + ae_result.features_contributing
                ))[:5]
                
                confidence = (if_result.confidence + ae_result.confidence) / 2
                
                metadata = {
                    "isolation_forest_score": if_result.anomaly_score,
                    "autoencoder_score": ae_result.anomaly_score,
                    "isolation_forest_anomaly": if_result.is_anomaly,
                    "autoencoder_anomaly": ae_result.is_anomaly,
                    "ensemble": True
                }
            else:
                # Use only Isolation Forest
                combined_score = if_result.anomaly_score
                is_anomaly = if_result.is_anomaly
                contributing = if_result.features_contributing
                confidence = if_result.confidence
                
                metadata = {
                    "isolation_forest_score": if_result.anomaly_score,
                    "isolation_forest_anomaly": if_result.is_anomaly,
                    "ensemble": False
                }
            
            # Determine anomaly type
            anomaly_type = None
            if is_anomaly:
                if combined_score > 0.8:
                    anomaly_type = AnomalyType.FRAUD_SUSPECT
                else:
                    anomaly_type = AnomalyType.UNUSUAL_PATTERN
            
            return AnomalyResult(
                is_anomaly=is_anomaly,
                anomaly_score=combined_score,
                anomaly_type=anomaly_type,
                confidence=confidence,
                features_contributing=contributing,
                explanation=self._generate_fraud_explanation(
                    is_anomaly, combined_score, contributing, claim, policy
                ),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error detecting fraud: {e}")
            return AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_type=None,
                confidence=0.0,
                features_contributing=[],
                explanation=f"Error in fraud detection: {str(e)}",
                metadata={"error": str(e)}
            )
    
    def _generate_fraud_explanation(
        self,
        is_anomaly: bool,
        score: float,
        contributing: List[str],
        claim: dict,
        policy: dict
    ) -> str:
        """
        Generate fraud explanation.
        
        Args:
            is_anomaly: Whether fraud detected
            score: Anomaly score
            contributing: Contributing features
            claim: Claim data
            policy: Policy data
            
        Returns:
            Human-readable explanation
        """
        if not is_anomaly:
            return "No fraud indicators detected"
        
        explanations = []
        
        if 'claim_coverage_ratio' in contributing:
            coverage = float(policy.get('coverage_limit', policy.get('cargo_value_usd', 1)))
            claimed = float(claim.get('claimed_amount', 0))
            ratio = claimed / coverage if coverage > 0 else 0
            if ratio > 0.8:
                explanations.append(f"Claim amount is {ratio:.0%} of coverage (very high)")
            else:
                explanations.append(f"Claim amount pattern is unusual ({ratio:.0%} of coverage)")
        
        if 'days_since_inception' in contributing:
            explanations.append("Claim filed shortly after policy inception")
        
        if 'days_to_report' in contributing:
            explanations.append("Unusual delay in reporting the loss")
        
        if 'previous_claims' in contributing:
            prev_claims = int(claim.get('customer_previous_claims', 0))
            if prev_claims > 3:
                explanations.append(f"Customer has {prev_claims} previous claims (high frequency)")
            else:
                explanations.append("Customer claim history is unusual")
        
        if 'loss_type' in contributing:
            loss_type = claim.get('loss_type', 'UNKNOWN')
            explanations.append(f"Loss type '{loss_type}' in unusual context")
        
        if not explanations:
            explanations.append("Multiple statistical indicators suggest unusual pattern")
        
        severity = "HIGH" if score > 0.8 else "MEDIUM" if score > 0.5 else "LOW"
        
        return f"Fraud risk: {severity}. {'; '.join(explanations[:3])}"
    
    def save_models(self):
        """Save models to disk."""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Save Isolation Forest
        if_path = self.models_dir / "isolation_forest.pkl"
        self.isolation_forest.save(str(if_path))
        
        # Save Autoencoder if available
        if self.use_autoencoder and self.autoencoder:
            ae_path = self.models_dir / "autoencoder"
            self.autoencoder.save(str(ae_path))
        
        # Save metadata
        metadata = {
            "is_trained": self.is_trained,
            "use_autoencoder": self.use_autoencoder,
            "feature_names": self.feature_names
        }
        metadata_path = self.models_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("Fraud detection models saved", path=str(self.models_dir))
    
    def load_models(self):
        """Load models from disk."""
        if not self.models_dir.exists():
            raise FileNotFoundError(f"Models directory not found: {self.models_dir}")
        
        # Load metadata
        metadata_path = self.models_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            self.is_trained = metadata.get("is_trained", False)
            self.use_autoencoder = metadata.get("use_autoencoder", False) and TENSORFLOW_AVAILABLE
            self.feature_names = metadata.get("feature_names", self.feature_names)
        
        # Load Isolation Forest
        if_path = self.models_dir / "isolation_forest.pkl"
        if if_path.exists():
            self.isolation_forest.load(str(if_path))
        else:
            raise FileNotFoundError(f"Isolation Forest model not found: {if_path}")
        
        # Load Autoencoder if available
        if self.use_autoencoder and TENSORFLOW_AVAILABLE:
            ae_path = self.models_dir / "autoencoder"
            if ae_path.exists():
                self.autoencoder = AutoencoderAnomalyDetector()
                self.autoencoder.load(str(ae_path))
            else:
                logger.warning(f"Autoencoder model not found: {ae_path}")
                self.use_autoencoder = False
        
        logger.info(
            "Fraud detection models loaded",
            path=str(self.models_dir),
            use_autoencoder=self.use_autoencoder
        )


# Global instance
fraud_service = FraudDetectionService()
