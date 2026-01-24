"""
Network benchmarking service.

Compares tenant performance against network/market benchmarks.
(Anonymized and aggregated data)
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.loss_experience import LossExperienceRecord
from app.models.corridor import CorridorBenchmark

logger = logging.getLogger(__name__)


class NetworkBenchmarkingService:
    """Service for network benchmarking."""
    
    def __init__(self, db: Session):
        """
        Initialize network benchmarking service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def generate_tenant_benchmark_report(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate benchmark report comparing tenant to network.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dictionary with benchmark report
        """
        # Get tenant metrics
        tenant_metrics = self._get_tenant_metrics(tenant_id, start_date, end_date)
        
        # Get network metrics (anonymized aggregate)
        network_metrics = self._get_network_metrics(start_date, end_date, exclude_tenant=tenant_id)
        
        # Compare
        comparison = self._compare_metrics(tenant_metrics, network_metrics)
        
        # Calculate percentiles
        percentiles = self._calculate_percentiles(tenant_id, start_date, end_date)
        
        return {
            "report_type": "NETWORK_BENCHMARK",
            "tenant_id": tenant_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "tenant_metrics": tenant_metrics,
            "network_metrics": network_metrics,
            "comparison": comparison,
            "percentile_rankings": percentiles,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _get_tenant_metrics(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Get metrics for a specific tenant.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with tenant metrics
        """
        records = self.db.query(LossExperienceRecord).filter(
            LossExperienceRecord.tenant_id == tenant_id,
            LossExperienceRecord.policy_effective_date >= start_date,
            LossExperienceRecord.policy_effective_date <= end_date
        ).all()
        
        if not records:
            return {"error": "No data"}
        
        total_premium = sum(r.premium_cents for r in records)
        total_exposure = sum(r.exposure_cents for r in records)
        total_actual_loss = sum(r.actual_loss_cents or 0 for r in records)
        total_expected_loss = sum(r.expected_loss_cents or 0 for r in records)
        
        # Calculate claim frequency
        claims_count = sum(1 for r in records if r.claim_id is not None)
        claim_frequency = claims_count / len(records) if records else 0
        
        return {
            "policy_count": len(records),
            "total_premium_cents": total_premium,
            "total_exposure_cents": total_exposure,
            "loss_ratio": round((total_actual_loss / total_premium), 4) if total_premium > 0 else 0.0,
            "expected_loss_ratio": round((total_expected_loss / total_premium), 4) if total_premium > 0 else 0.0,
            "avg_premium_cents": total_premium // len(records) if records else 0,
            "claim_frequency": round(claim_frequency, 4),
            "claims_count": claims_count
        }
    
    def _get_network_metrics(
        self,
        start_date: date,
        end_date: date,
        exclude_tenant: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get anonymized network-wide metrics.
        
        These are aggregate metrics that don't expose individual tenant data.
        
        Args:
            start_date: Start date
            end_date: End date
            exclude_tenant: Optional tenant ID to exclude from network metrics
            
        Returns:
            Dictionary with network metrics
        """
        query = self.db.query(
            func.count(LossExperienceRecord.id).label('count'),
            func.sum(LossExperienceRecord.premium_cents).label('premium'),
            func.sum(LossExperienceRecord.exposure_cents).label('exposure'),
            func.sum(LossExperienceRecord.actual_loss_cents).label('actual_loss'),
            func.sum(LossExperienceRecord.expected_loss_cents).label('expected_loss'),
            func.sum(
                case((LossExperienceRecord.claim_id.isnot(None), 1), else_=0)
            ).label('claims_count')
        ).filter(
            LossExperienceRecord.policy_effective_date >= start_date,
            LossExperienceRecord.policy_effective_date <= end_date
        )
        
        if exclude_tenant:
            query = query.filter(LossExperienceRecord.tenant_id != exclude_tenant)
        
        result = query.first()
        
        if not result or not result.count or result.count == 0:
            return {"error": "Insufficient network data"}
        
        total_premium = result.premium or 0
        total_actual_loss = result.actual_loss or 0
        total_expected_loss = result.expected_loss or 0
        claims_count = result.claims_count or 0
        
        return {
            "sample_size": result.count,
            "avg_loss_ratio": round((total_actual_loss / total_premium), 4) if total_premium > 0 else 0.0,
            "avg_expected_loss_ratio": round((total_expected_loss / total_premium), 4) if total_premium > 0 else 0.0,
            "avg_premium_cents": total_premium // result.count if result.count > 0 else 0,
            "avg_claim_frequency": round((claims_count / result.count), 4) if result.count > 0 else 0.0
        }
    
    def _compare_metrics(
        self,
        tenant: Dict[str, Any],
        network: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare tenant metrics to network.
        
        Args:
            tenant: Tenant metrics dictionary
            network: Network metrics dictionary
            
        Returns:
            Dictionary with comparison results
        """
        if "error" in tenant or "error" in network:
            return {"error": "Cannot compare due to missing data"}
        
        tenant_lr = tenant.get('loss_ratio', 0)
        network_lr = network.get('avg_loss_ratio', 0)
        
        tenant_cf = tenant.get('claim_frequency', 0)
        network_cf = network.get('avg_claim_frequency', 0)
        
        comparison = {
            "loss_ratio": {
                "tenant": tenant_lr,
                "network": network_lr,
                "difference": round(tenant_lr - network_lr, 4),
                "difference_pct": round(((tenant_lr - network_lr) / network_lr * 100), 2) if network_lr > 0 else 0.0,
                "better_than_network": tenant_lr < network_lr
            },
            "claim_frequency": {
                "tenant": tenant_cf,
                "network": network_cf,
                "difference": round(tenant_cf - network_cf, 4),
                "better_than_network": tenant_cf < network_cf
            }
        }
        
        # Overall assessment based on loss ratio
        if network_lr > 0:
            if tenant_lr < network_lr * 0.9:
                comparison["overall_assessment"] = "OUTPERFORMING"
                comparison["performance_tier"] = "TOP_QUARTILE"
            elif tenant_lr < network_lr * 1.1:
                comparison["overall_assessment"] = "ON_PAR"
                comparison["performance_tier"] = "MIDDLE_QUARTILES"
            else:
                comparison["overall_assessment"] = "UNDERPERFORMING"
                comparison["performance_tier"] = "BOTTOM_QUARTILE"
        else:
            comparison["overall_assessment"] = "INSUFFICIENT_DATA"
            comparison["performance_tier"] = "UNKNOWN"
        
        return comparison
    
    def _calculate_percentiles(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Calculate tenant's percentile ranking in the network.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with percentile rankings
        """
        # Get all tenants' loss ratios
        tenant_loss_ratios = self.db.query(
            LossExperienceRecord.tenant_id,
            func.sum(LossExperienceRecord.actual_loss_cents).label('loss'),
            func.sum(LossExperienceRecord.premium_cents).label('premium')
        ).filter(
            LossExperienceRecord.policy_effective_date >= start_date,
            LossExperienceRecord.policy_effective_date <= end_date
        ).group_by(
            LossExperienceRecord.tenant_id
        ).having(
            func.sum(LossExperienceRecord.premium_cents) > 0
        ).all()
        
        if len(tenant_loss_ratios) < 3:
            return {"error": "Insufficient data for percentile calculation (need at least 3 tenants)"}
        
        # Calculate loss ratios
        loss_ratios = []
        tenant_lr = None
        for t in tenant_loss_ratios:
            lr = (t.loss / t.premium) if t.premium and t.premium > 0 else 0.0
            loss_ratios.append((t.tenant_id, lr))
            if t.tenant_id == tenant_id:
                tenant_lr = lr
        
        if tenant_lr is None:
            return {"error": "Tenant not found in network data"}
        
        # Calculate percentile (lower loss ratio = better = higher percentile)
        sorted_lrs = sorted(loss_ratios, key=lambda x: x[1])
        
        # Find position (0-indexed)
        position = next((i for i, (tid, lr) in enumerate(sorted_lrs) if tid == tenant_id), None)
        
        if position is None:
            return {"error": "Tenant position not found"}
        
        # Percentile: percentage of tenants with worse (higher) loss ratio
        # If position is 0 (best), percentile is 100
        # If position is last (worst), percentile is 0
        percentile = ((len(sorted_lrs) - position - 1) / len(sorted_lrs)) * 100
        
        # Determine quartile
        if percentile >= 75:
            quartile = "TOP_QUARTILE"
        elif percentile >= 50:
            quartile = "UPPER_MIDDLE"
        elif percentile >= 25:
            quartile = "LOWER_MIDDLE"
        else:
            quartile = "BOTTOM_QUARTILE"
        
        return {
            "loss_ratio_percentile": round(percentile, 1),
            "interpretation": f"Better than {percentile:.0f}% of network",
            "total_tenants_compared": len(sorted_lrs),
            "quartile": quartile,
            "position": position + 1,  # 1-indexed
            "total_tenants": len(sorted_lrs)
        }
    
    def get_corridor_comparison(
        self,
        tenant_id: str,
        corridor_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Compare tenant performance on a specific corridor to benchmark.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            corridor_id: Corridor ID (ULID string)
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with corridor comparison
        """
        # Get tenant's corridor performance
        tenant_records = self.db.query(LossExperienceRecord).filter(
            LossExperienceRecord.tenant_id == tenant_id,
            LossExperienceRecord.corridor_id == corridor_id,
            LossExperienceRecord.policy_effective_date >= start_date,
            LossExperienceRecord.policy_effective_date <= end_date
        ).all()
        
        if not tenant_records:
            return {"error": "No tenant data for this corridor"}
        
        # Get corridor benchmark
        benchmark = self.db.query(CorridorBenchmark).filter(
            CorridorBenchmark.corridor_id == corridor_id,
            CorridorBenchmark.is_current == True
        ).first()
        
        if not benchmark:
            return {"error": "No benchmark available for this corridor"}
        
        # Calculate tenant metrics
        total_premium = sum(r.premium_cents for r in tenant_records)
        total_loss = sum(r.actual_loss_cents or 0 for r in tenant_records)
        tenant_loss_ratio = (total_loss / total_premium) if total_premium > 0 else 0.0
        
        # Get benchmark metrics
        risk_metrics = benchmark.risk_metrics_json or {}
        delay_metrics = benchmark.delay_metrics_json or {}
        
        benchmark_loss_rate = risk_metrics.get('loss_rate_historical', 0)
        on_time_rate = delay_metrics.get('on_time_rate', 0)
        corridor_risk_score = risk_metrics.get('corridor_risk_score', 0)
        
        # Calculate comparison
        vs_benchmark = tenant_loss_ratio - benchmark_loss_rate
        
        return {
            "corridor_id": corridor_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "tenant_performance": {
                "policy_count": len(tenant_records),
                "total_premium_cents": total_premium,
                "total_loss_cents": total_loss,
                "loss_ratio": round(tenant_loss_ratio, 4)
            },
            "corridor_benchmark": {
                "historical_loss_rate": benchmark_loss_rate,
                "on_time_rate": round(on_time_rate, 4) if on_time_rate else None,
                "risk_score": round(corridor_risk_score, 4) if corridor_risk_score else None,
                "benchmark_version": benchmark.version,
                "effective_from": benchmark.effective_from.isoformat() if benchmark.effective_from else None
            },
            "comparison": {
                "vs_benchmark": round(vs_benchmark, 4),
                "vs_benchmark_pct": round((vs_benchmark / benchmark_loss_rate * 100), 2) if benchmark_loss_rate > 0 else None,
                "better_than_benchmark": tenant_loss_ratio < benchmark_loss_rate,
                "performance_assessment": (
                    "OUTPERFORMING" if tenant_loss_ratio < benchmark_loss_rate * 0.9
                    else "ON_PAR" if tenant_loss_ratio < benchmark_loss_rate * 1.1
                    else "UNDERPERFORMING"
                ) if benchmark_loss_rate > 0 else "INSUFFICIENT_DATA"
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_network_summary(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Get anonymized network summary statistics.
        
        Provides aggregate insights without exposing individual tenant data.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with network summary
        """
        # Overall network metrics
        network_metrics = self._get_network_metrics(start_date, end_date, exclude_tenant=None)
        
        if "error" in network_metrics:
            return network_metrics
        
        # Get distribution statistics
        tenant_stats = self.db.query(
            LossExperienceRecord.tenant_id,
            func.sum(LossExperienceRecord.actual_loss_cents).label('loss'),
            func.sum(LossExperienceRecord.premium_cents).label('premium')
        ).filter(
            LossExperienceRecord.policy_effective_date >= start_date,
            LossExperienceRecord.policy_effective_date <= end_date
        ).group_by(
            LossExperienceRecord.tenant_id
        ).having(
            func.sum(LossExperienceRecord.premium_cents) > 0
        ).all()
        
        if len(tenant_stats) < 3:
            return {
                "error": "Insufficient data for network summary",
                "network_metrics": network_metrics
            }
        
        # Calculate loss ratios
        loss_ratios = [
            (t.loss / t.premium) if t.premium and t.premium > 0 else 0.0
            for t in tenant_stats
        ]
        
        sorted_lrs = sorted(loss_ratios)
        n = len(sorted_lrs)
        
        # Calculate percentiles
        def get_percentile(data: List[float], p: int) -> float:
            """Get percentile value from sorted data."""
            if not data:
                return 0.0
            k = (n - 1) * p / 100
            f = int(k)
            c = f + 1 if f + 1 < n else f
            if f == c:
                return data[f]
            return data[f] + (k - f) * (data[c] - data[f])
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "network_metrics": network_metrics,
            "distribution": {
                "total_tenants": n,
                "p25_loss_ratio": round(get_percentile(sorted_lrs, 25), 4),
                "p50_loss_ratio": round(get_percentile(sorted_lrs, 50), 4),
                "p75_loss_ratio": round(get_percentile(sorted_lrs, 75), 4),
                "p90_loss_ratio": round(get_percentile(sorted_lrs, 90), 4),
                "min_loss_ratio": round(sorted_lrs[0], 4) if sorted_lrs else 0.0,
                "max_loss_ratio": round(sorted_lrs[-1], 4) if sorted_lrs else 0.0
            },
            "generated_at": datetime.utcnow().isoformat()
        }
