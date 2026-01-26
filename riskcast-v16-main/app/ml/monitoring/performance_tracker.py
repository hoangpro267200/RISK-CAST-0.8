"""
Model Performance Tracking

Tracks:
1. Prediction latency
2. Throughput
3. Error rates
4. Accuracy metrics over time
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
import asyncio
import json

import numpy as np

from app.core.logging import get_logger


logger = get_logger(__name__)

# Optional Redis import
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


@dataclass
class PredictionRecord:
    """Record of a single prediction."""
    prediction_id: str
    model_name: str
    model_version: str
    
    # Timing
    timestamp: datetime
    latency_ms: float
    
    # Input/Output
    input_hash: str  # Hash of input for deduplication
    prediction: float
    confidence: Optional[float] = None
    
    # Ground truth (when available)
    actual: Optional[float] = None
    actual_recorded_at: Optional[datetime] = None
    
    # Error
    error: Optional[float] = None
    
    # Metadata
    tenant_id: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class PerformanceSnapshot:
    """Performance snapshot for a time window."""
    model_name: str
    model_version: str
    
    window_start: datetime
    window_end: datetime
    
    # Volume
    total_predictions: int
    
    # Latency
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    
    # Throughput
    predictions_per_second: float
    
    # Accuracy (if actuals available)
    mae: Optional[float] = None
    rmse: Optional[float] = None
    mape: Optional[float] = None
    
    # Errors
    error_count: int = 0
    error_rate: float = 0.0


class PerformanceTracker:
    """
    Tracks model performance metrics over time.
    """
    
    def __init__(
        self,
        model_name: str,
        model_version: str,
        redis_client: Optional[Any] = None,  # redis.Redis type
        window_size: int = 10000
    ):
        self.model_name = model_name
        self.model_version = model_version
        self.redis = redis_client
        self.window_size = window_size
        
        # In-memory buffers
        self._latencies: deque = deque(maxlen=window_size)
        self._predictions: deque = deque(maxlen=window_size)
        self._actuals: deque = deque(maxlen=window_size)
        self._errors: deque = deque(maxlen=window_size)
        self._timestamps: deque = deque(maxlen=window_size)
        
        # Counters
        self._total_predictions = 0
        self._total_errors = 0
        
        # Start time for throughput
        self._start_time = datetime.utcnow()
    
    def record_prediction(
        self,
        prediction: float,
        latency_ms: float,
        actual: Optional[float] = None,
        error: bool = False,
        metadata: Optional[Dict] = None
    ):
        """Record a prediction."""
        self._latencies.append(latency_ms)
        self._predictions.append(prediction)
        self._timestamps.append(datetime.utcnow())
        self._total_predictions += 1
        
        if actual is not None:
            self._actuals.append(actual)
        
        if error:
            self._errors.append(datetime.utcnow())
            self._total_errors += 1
    
    def record_actual(self, prediction_id: str, actual: float):
        """Record ground truth for a prediction."""
        # Would need to look up prediction and update
        self._actuals.append(actual)
    
    def get_current_snapshot(self) -> PerformanceSnapshot:
        """Get current performance snapshot."""
        latencies = np.array(list(self._latencies)) if self._latencies else np.array([0])
        predictions = np.array(list(self._predictions)) if self._predictions else np.array([])
        actuals = np.array(list(self._actuals)) if self._actuals else np.array([])
        
        # Calculate metrics
        avg_latency = float(np.mean(latencies)) if len(latencies) > 0 else 0.0
        p50_latency = float(np.percentile(latencies, 50)) if len(latencies) > 0 else 0.0
        p95_latency = float(np.percentile(latencies, 95)) if len(latencies) > 0 else 0.0
        p99_latency = float(np.percentile(latencies, 99)) if len(latencies) > 0 else 0.0
        max_latency = float(np.max(latencies)) if len(latencies) > 0 else 0.0
        
        # Throughput
        elapsed = (datetime.utcnow() - self._start_time).total_seconds()
        throughput = self._total_predictions / elapsed if elapsed > 0 else 0
        
        # Accuracy metrics
        mae = rmse = mape = None
        if len(actuals) > 0 and len(predictions) >= len(actuals):
            preds = predictions[-len(actuals):]
            mae = float(np.mean(np.abs(actuals - preds)))
            rmse = float(np.sqrt(np.mean((actuals - preds) ** 2)))
            with np.errstate(divide='ignore', invalid='ignore'):
                mape = np.mean(np.abs((actuals - preds) / actuals)) * 100
                if np.isnan(mape) or np.isinf(mape):
                    mape = None
        
        # Error rate
        error_rate = self._total_errors / self._total_predictions if self._total_predictions > 0 else 0
        
        # Window times
        window_start = self._timestamps[0] if self._timestamps else datetime.utcnow()
        window_end = self._timestamps[-1] if self._timestamps else datetime.utcnow()
        
        return PerformanceSnapshot(
            model_name=self.model_name,
            model_version=self.model_version,
            window_start=window_start,
            window_end=window_end,
            total_predictions=len(predictions),
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            max_latency_ms=max_latency,
            predictions_per_second=throughput,
            mae=mae,
            rmse=rmse,
            mape=mape,
            error_count=self._total_errors,
            error_rate=error_rate
        )
    
    async def store_snapshot(self, snapshot: PerformanceSnapshot):
        """Store snapshot to Redis."""
        if not self.redis:
            return
        
        try:
            key = f"perf:{self.model_name}:{snapshot.window_end.strftime('%Y%m%d%H%M')}"
            data = {
                "model_name": snapshot.model_name,
                "model_version": snapshot.model_version,
                "window_start": snapshot.window_start.isoformat(),
                "window_end": snapshot.window_end.isoformat(),
                "total_predictions": snapshot.total_predictions,
                "avg_latency_ms": snapshot.avg_latency_ms,
                "p95_latency_ms": snapshot.p95_latency_ms,
                "predictions_per_second": snapshot.predictions_per_second,
                "mae": snapshot.mae,
                "error_rate": snapshot.error_rate
            }
            
            await self.redis.setex(key, 86400 * 7, json.dumps(data))
        except Exception as e:
            logger.warning(f"Failed to store performance snapshot: {e}")
    
    async def get_historical_snapshots(
        self,
        hours: int = 24
    ) -> List[Dict]:
        """Get historical snapshots."""
        if not self.redis:
            return []
        
        try:
            snapshots = []
            pattern = f"perf:{self.model_name}:*"
            
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor=cursor, match=pattern, count=100)
                for key in keys:
                    data = await self.redis.get(key)
                    if data:
                        snapshots.append(json.loads(data))
                if cursor == 0:
                    break
            
            return snapshots
        except Exception as e:
            logger.warning(f"Failed to get historical snapshots: {e}")
            return []
    
    def reset(self):
        """Reset all counters."""
        self._latencies.clear()
        self._predictions.clear()
        self._actuals.clear()
        self._errors.clear()
        self._timestamps.clear()
        self._total_predictions = 0
        self._total_errors = 0
        self._start_time = datetime.utcnow()
