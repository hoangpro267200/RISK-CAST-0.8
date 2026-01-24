"""
ROI reporting service.

Tracks and reports on:
- Premium vs loss performance
- Model accuracy ROI
- Operational efficiency
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
import calendar
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.loss_experience import LossExperienceRecord
from app.services.loss_analytics_service import LossAnalyticsService

logger = logging.getLogger(__name__)


class ROIReportingService:
    """Service for ROI reporting and analytics."""
    
    def __init__(self, db: Session, loss_analytics: Optional[LossAnalyticsService] = None):
        """
        Initialize ROI reporting service.
        
        Args:
            db: Database session
            loss_analytics: Optional loss analytics service
        """
        self.db = db
        self.loss_analytics = loss_analytics or LossAnalyticsService(db)
    
    def generate_portfolio_roi_report(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate portfolio-level ROI report.
        
        Shows overall financial performance.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dictionary with portfolio ROI report
        """
        # Get loss experience records in period
        loss_records = self.db.query(LossExperienceRecord).filter(
            LossExperienceRecord.tenant_id == tenant_id,
            LossExperienceRecord.policy_effective_date >= start_date,
            LossExperienceRecord.policy_effective_date <= end_date
        ).all()
        
        if not loss_records:
            return {
                "report_type": "PORTFOLIO_ROI",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "error": "No data for this period"
            }
        
        # Calculate aggregates
        total_premium = sum(r.premium_cents for r in loss_records)
        total_exposure = sum(r.exposure_cents for r in loss_records)
        
        total_expected_loss = sum(r.expected_loss_cents or 0 for r in loss_records)
        total_actual_loss = sum(r.actual_loss_cents or 0 for r in loss_records)
        total_paid_loss = sum(r.paid_loss_cents or 0 for r in loss_records)
        total_reserved_loss = sum(r.reserved_loss_cents or 0 for r in loss_records)
        
        # Calculate metrics
        loss_ratio = (total_actual_loss / total_premium) if total_premium > 0 else 0.0
        expected_loss_ratio = (total_expected_loss / total_premium) if total_premium > 0 else 0.0
        
        # Gross margin
        gross_margin_cents = total_premium - total_actual_loss
        gross_margin_pct = (gross_margin_cents / total_premium) if total_premium > 0 else 0.0
        
        # Model accuracy
        if total_expected_loss > 0:
            prediction_accuracy = 1.0 - (abs(total_actual_loss - total_expected_loss) / total_expected_loss)
        else:
            prediction_accuracy = None
        
        return {
            "report_type": "PORTFOLIO_ROI",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "portfolio_summary": {
                "policy_count": len(loss_records),
                "total_exposure_cents": total_exposure,
                "total_premium_cents": total_premium,
                "currency": "USD"
            },
            "loss_performance": {
                "expected_loss_cents": total_expected_loss,
                "actual_loss_cents": total_actual_loss,
                "paid_loss_cents": total_paid_loss,
                "reserved_loss_cents": total_reserved_loss,
                "loss_ratio": round(loss_ratio, 4),
                "expected_loss_ratio": round(expected_loss_ratio, 4)
            },
            "profitability": {
                "gross_margin_cents": gross_margin_cents,
                "gross_margin_pct": round(gross_margin_pct * 100, 2),
                "target_loss_ratio": 0.60,  # Industry benchmark
                "vs_target": round((0.60 - loss_ratio) * 100, 2)
            },
            "model_performance": {
                "prediction_accuracy": round(prediction_accuracy, 4) if prediction_accuracy is not None else None,
                "expected_vs_actual_ratio": round(total_expected_loss / total_actual_loss, 4) if total_actual_loss > 0 else None
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def generate_corridor_roi_report(
        self,
        tenant_id: str,
        corridor_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate ROI report for a specific corridor.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            corridor_id: Corridor ID (ULID string)
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dictionary with corridor ROI report
        """
        loss_records = self.db.query(LossExperienceRecord).filter(
            LossExperienceRecord.tenant_id == tenant_id,
            LossExperienceRecord.corridor_id == corridor_id,
            LossExperienceRecord.policy_effective_date >= start_date,
            LossExperienceRecord.policy_effective_date <= end_date
        ).all()
        
        if not loss_records:
            return {
                "corridor_id": corridor_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "error": "No data for this corridor in period"
            }
        
        total_premium = sum(r.premium_cents for r in loss_records)
        total_expected = sum(r.expected_loss_cents or 0 for r in loss_records)
        total_actual = sum(r.actual_loss_cents or 0 for r in loss_records)
        total_paid = sum(r.paid_loss_cents or 0 for r in loss_records)
        
        loss_ratio = (total_actual / total_premium) if total_premium > 0 else 0.0
        
        return {
            "corridor_id": corridor_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "policy_count": len(loss_records),
            "total_premium_cents": total_premium,
            "total_exposure_cents": sum(r.exposure_cents for r in loss_records),
            "expected_loss_cents": total_expected,
            "actual_loss_cents": total_actual,
            "paid_loss_cents": total_paid,
            "reserved_loss_cents": total_actual - total_paid,
            "loss_ratio": round(loss_ratio, 4),
            "expected_loss_ratio": round((total_expected / total_premium), 4) if total_premium > 0 else 0.0,
            "margin_cents": total_premium - total_actual,
            "margin_pct": round(((total_premium - total_actual) / total_premium * 100), 2) if total_premium > 0 else 0.0,
            "profitable": total_actual < total_premium,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def generate_model_roi_report(
        self,
        tenant_id: str,
        model_version_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate ROI report for a specific model version.
        
        Shows how much value the model has provided.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            model_version_id: Model version ID (ULID string)
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dictionary with model ROI report
        """
        loss_records = self.db.query(LossExperienceRecord).filter(
            LossExperienceRecord.tenant_id == tenant_id,
            LossExperienceRecord.model_version_id == model_version_id,
            LossExperienceRecord.policy_effective_date >= start_date,
            LossExperienceRecord.policy_effective_date <= end_date
        ).all()
        
        if not loss_records:
            return {
                "model_version_id": model_version_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "error": "No data for this model version"
            }
        
        # Calculate prediction accuracy metrics
        errors = []
        for r in loss_records:
            if r.expected_loss_cents and r.actual_loss_cents is not None:
                if r.expected_loss_cents > 0:
                    error = (r.actual_loss_cents - r.expected_loss_cents) / r.expected_loss_cents
                else:
                    error = 0.0
                errors.append(error)
        
        mean_error = (sum(errors) / len(errors)) if errors else 0.0
        
        # Calculate value added
        # If we had used a naive model (e.g., flat 5% loss rate)
        naive_loss_rate = 0.05
        total_exposure = sum(r.exposure_cents for r in loss_records)
        naive_expected_loss = int(total_exposure * naive_loss_rate)
        model_expected_loss = sum(r.expected_loss_cents or 0 for r in loss_records)
        actual_loss = sum(r.actual_loss_cents or 0 for r in loss_records)
        
        # Value added = how much better is model vs naive
        naive_error = abs(naive_expected_loss - actual_loss)
        model_error = abs(model_expected_loss - actual_loss)
        value_added_cents = naive_error - model_error
        
        improvement_pct = None
        if naive_error > 0:
            improvement_pct = round((value_added_cents / naive_error) * 100, 2)
        
        return {
            "model_version_id": model_version_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "usage": {
                "policy_count": len(loss_records),
                "total_exposure_cents": total_exposure,
                "total_premium_cents": sum(r.premium_cents for r in loss_records)
            },
            "prediction_accuracy": {
                "mean_prediction_error": round(mean_error, 4),
                "model_expected_loss_cents": model_expected_loss,
                "actual_loss_cents": actual_loss,
                "error_rate": round(abs(model_expected_loss - actual_loss) / actual_loss, 4) if actual_loss > 0 else None,
                "prediction_accuracy": round(1.0 - abs(mean_error), 4) if mean_error else None
            },
            "value_added": {
                "vs_naive_model": {
                    "naive_expected_loss_cents": naive_expected_loss,
                    "model_expected_loss_cents": model_expected_loss,
                    "actual_loss_cents": actual_loss
                },
                "improvement_cents": value_added_cents,
                "improvement_pct": improvement_pct
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def generate_trend_report(
        self,
        tenant_id: str,
        months: int = 12
    ) -> Dict[str, Any]:
        """
        Generate trend report over time.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            months: Number of months to analyze (default: 12)
            
        Returns:
            Dictionary with trend report
        """
        end_date = date.today()
        
        # Calculate start date (months ago)
        start_year = end_date.year
        start_month = end_date.month - months
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        
        start_date = date(start_year, start_month, 1)
        
        # Group by month
        monthly_data = []
        current = start_date
        
        while current <= end_date:
            # Calculate month end
            if current.month == 12:
                month_end = date(current.year + 1, 1, 1) - timedelta(days=1)
            else:
                # Get last day of current month
                last_day = calendar.monthrange(current.year, current.month)[1]
                month_end = date(current.year, current.month, last_day)
            
            # Don't go past end_date
            if month_end > end_date:
                month_end = end_date
            
            records = self.db.query(LossExperienceRecord).filter(
                LossExperienceRecord.tenant_id == tenant_id,
                LossExperienceRecord.policy_effective_date >= current,
                LossExperienceRecord.policy_effective_date <= month_end
            ).all()
            
            if records:
                premium = sum(r.premium_cents for r in records)
                actual_loss = sum(r.actual_loss_cents or 0 for r in records)
                expected_loss = sum(r.expected_loss_cents or 0 for r in records)
                
                monthly_data.append({
                    "month": current.strftime("%Y-%m"),
                    "policy_count": len(records),
                    "premium_cents": premium,
                    "expected_loss_cents": expected_loss,
                    "actual_loss_cents": actual_loss,
                    "loss_ratio": round((actual_loss / premium), 4) if premium > 0 else 0.0,
                    "expected_loss_ratio": round((expected_loss / premium), 4) if premium > 0 else 0.0,
                    "margin_cents": premium - actual_loss
                })
            
            # Move to next month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        
        trend = self._calculate_trend(monthly_data)
        
        return {
            "report_type": "TREND",
            "tenant_id": tenant_id,
            "period_months": months,
            "monthly_data": monthly_data,
            "trend": trend,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_trend(self, monthly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate trend from monthly data.
        
        Args:
            monthly_data: List of monthly data dictionaries
            
        Returns:
            Dictionary with trend analysis
        """
        if len(monthly_data) < 2:
            return {"direction": "INSUFFICIENT_DATA", "message": "Need at least 2 months of data"}
        
        loss_ratios = [m['loss_ratio'] for m in monthly_data]
        
        # Simple trend: compare first half to second half
        mid = len(loss_ratios) // 2
        first_half_avg = (sum(loss_ratios[:mid]) / mid) if mid > 0 else 0.0
        second_half_avg = (sum(loss_ratios[mid:]) / (len(loss_ratios) - mid)) if (len(loss_ratios) - mid) > 0 else 0.0
        
        change = second_half_avg - first_half_avg
        
        if change < -0.05:
            direction = "IMPROVING"
        elif change > 0.05:
            direction = "DETERIORATING"
        else:
            direction = "STABLE"
        
        return {
            "direction": direction,
            "first_half_avg_loss_ratio": round(first_half_avg, 4),
            "second_half_avg_loss_ratio": round(second_half_avg, 4),
            "change": round(change, 4),
            "change_pct": round((change / first_half_avg * 100), 2) if first_half_avg > 0 else 0.0
        }
    
    def generate_comparative_roi_report(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date,
        compare_dimensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comparative ROI report across dimensions.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            start_date: Report start date
            end_date: Report end date
            compare_dimensions: List of dimensions to compare (corridor, cargo_type, model_version)
            
        Returns:
            Dictionary with comparative ROI report
        """
        compare_dimensions = compare_dimensions or ['corridor', 'cargo_type']
        
        report = {
            "report_type": "COMPARATIVE_ROI",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "dimensions": {},
            "generated_at": datetime.utcnow().isoformat()
        }
        
        loss_records = self.db.query(LossExperienceRecord).filter(
            LossExperienceRecord.tenant_id == tenant_id,
            LossExperienceRecord.policy_effective_date >= start_date,
            LossExperienceRecord.policy_effective_date <= end_date
        ).all()
        
        for dimension in compare_dimensions:
            dimension_data = {}
            
            if dimension == 'corridor':
                # Group by corridor_id
                corridors = set(r.corridor_id for r in loss_records if r.corridor_id)
                for corridor_id in corridors:
                    corridor_records = [r for r in loss_records if r.corridor_id == corridor_id]
                    dimension_data[corridor_id] = self._calculate_dimension_roi(corridor_records)
            
            elif dimension == 'cargo_type':
                # Group by cargo_type
                cargo_types = set(r.cargo_type for r in loss_records if r.cargo_type)
                for cargo_type in cargo_types:
                    cargo_records = [r for r in loss_records if r.cargo_type == cargo_type]
                    dimension_data[cargo_type] = self._calculate_dimension_roi(cargo_records)
            
            elif dimension == 'model_version':
                # Group by model_version_id
                model_versions = set(r.model_version_id for r in loss_records if r.model_version_id)
                for model_version_id in model_versions:
                    model_records = [r for r in loss_records if r.model_version_id == model_version_id]
                    dimension_data[model_version_id] = self._calculate_dimension_roi(model_records)
            
            report["dimensions"][dimension] = dimension_data
        
        return report
    
    def _calculate_dimension_roi(self, records: List[LossExperienceRecord]) -> Dict[str, Any]:
        """
        Calculate ROI metrics for a set of records.
        
        Args:
            records: List of LossExperienceRecord instances
            
        Returns:
            Dictionary with ROI metrics
        """
        if not records:
            return {"error": "No records"}
        
        total_premium = sum(r.premium_cents for r in records)
        total_exposure = sum(r.exposure_cents for r in records)
        total_expected = sum(r.expected_loss_cents or 0 for r in records)
        total_actual = sum(r.actual_loss_cents or 0 for r in records)
        total_paid = sum(r.paid_loss_cents or 0 for r in records)
        
        loss_ratio = (total_actual / total_premium) if total_premium > 0 else 0.0
        margin_cents = total_premium - total_actual
        margin_pct = (margin_cents / total_premium * 100) if total_premium > 0 else 0.0
        
        return {
            "policy_count": len(records),
            "total_premium_cents": total_premium,
            "total_exposure_cents": total_exposure,
            "expected_loss_cents": total_expected,
            "actual_loss_cents": total_actual,
            "paid_loss_cents": total_paid,
            "loss_ratio": round(loss_ratio, 4),
            "margin_cents": margin_cents,
            "margin_pct": round(margin_pct, 2),
            "profitable": total_actual < total_premium
        }
