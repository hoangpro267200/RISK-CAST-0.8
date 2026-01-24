"""
Loss analytics service.

Tracks expected vs actual loss for:
- Model calibration
- Pricing validation
- Reinsurer reporting
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.loss_experience import LossExperienceRecord

logger = logging.getLogger(__name__)


class LossAnalyticsService:
    """Service for loss analytics."""
    
    def __init__(self, db: Session):
        """
        Initialize loss analytics service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_record_from_policy(self, policy_id: str) -> LossExperienceRecord:
        """
        Create loss experience record when policy is bound.
        
        Captures expected loss from underwriting.
        
        Args:
            policy_id: Policy ID (ULID string)
            
        Returns:
            Created LossExperienceRecord instance
        """
        try:
            from app.modules.underwriting.models import Policy
            policy = self.db.query(Policy).filter(Policy.id == policy_id).first()
            if not policy:
                raise PolicyNotFoundError(f"Policy {policy_id} not found")
        except ImportError:
            raise PolicyNotFoundError("Policy model not available")
        
        # Check if record already exists
        existing = self.db.query(LossExperienceRecord).filter(
            LossExperienceRecord.policy_id == policy_id
        ).first()
        if existing:
            logger.warning(f"Loss experience record already exists for policy {policy_id}")
            return existing
        
        # Get risk snapshot
        risk_snapshot = getattr(policy, 'risk_snapshot_json', None) or {}
        
        # Calculate expected loss
        terms_json = getattr(policy, 'terms_json', None) or {}
        exposure = terms_json.get('insured_value_cents', 0)
        expected_loss_rate = risk_snapshot.get('expected_loss', 0.05)  # Default 5%
        expected_loss_cents = int(exposure * expected_loss_rate) if exposure > 0 else 0
        
        # Get premium
        premium_json = getattr(policy, 'premium_json', None) or {}
        premium_cents = premium_json.get('total_premium_cents', 0)
        
        # Get dimensions
        corridor_id = getattr(policy, 'corridor_id', None)
        cargo_type = terms_json.get('cargo_type')
        coverage_type = terms_json.get('coverage_type')
        
        # Get effective date
        effective_from = getattr(policy, 'effective_from', None)
        policy_effective_date = effective_from.date() if effective_from else date.today()
        
        # Get model version
        model_version_id = getattr(policy, 'model_version_id', None)
        
        # Get risk score
        risk_score = risk_snapshot.get('overall_risk_score')
        
        record = LossExperienceRecord(
            id=self._generate_id(),
            tenant_id=policy.tenant_id,
            policy_id=policy_id,
            
            # Dimensions
            corridor_id=corridor_id,
            cargo_type=cargo_type,
            coverage_type=coverage_type,
            
            # Exposure
            exposure_cents=exposure,
            premium_cents=premium_cents,
            currency=terms_json.get('currency', 'USD'),
            
            # Expected loss
            expected_loss_cents=expected_loss_cents,
            expected_loss_rate=expected_loss_rate,
            risk_score_at_bind=risk_score,
            model_version_id=model_version_id,
            
            # Actual loss (starts at 0)
            actual_loss_cents=0,
            actual_loss_rate=0.0,
            paid_loss_cents=0,
            reserved_loss_cents=0,
            
            # Timing
            policy_effective_date=policy_effective_date,
            
            # Status
            record_status='ACTIVE',
            
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(
            f"Created loss experience record for policy {policy_id} "
            f"(expected_loss: {expected_loss_cents}, exposure: {exposure})"
        )
        
        return record
    
    def update_from_claim(self, claim_id: str) -> LossExperienceRecord:
        """
        Update loss record when claim is filed/adjudicated.
        
        Args:
            claim_id: Claim ID (ULID string)
            
        Returns:
            Updated LossExperienceRecord instance
        """
        try:
            from app.modules.claims.models import Claim
            claim = self.db.query(Claim).filter(Claim.id == claim_id).first()
            if not claim:
                raise ClaimNotFoundError(f"Claim {claim_id} not found")
        except ImportError:
            raise ClaimNotFoundError("Claim model not available")
        
        # Find or create record
        record = self.db.query(LossExperienceRecord).filter(
            LossExperienceRecord.policy_id == claim.policy_id
        ).first()
        
        if not record:
            record = self.create_record_from_policy(claim.policy_id)
        
        # Update claim reference
        record.claim_id = claim_id
        
        # Get loss type and dates from FNOL
        fnol_json = getattr(claim, 'fnol_json', None) or {}
        if fnol_json:
            loss_type = fnol_json.get('loss_type')
            if loss_type:
                record.loss_type = loss_type
            
            loss_date_str = fnol_json.get('loss_date')
            if loss_date_str:
                try:
                    if isinstance(loss_date_str, str):
                        record.loss_date = datetime.fromisoformat(loss_date_str.replace('Z', '+00:00')).date()
                    else:
                        record.loss_date = loss_date_str
                except (ValueError, AttributeError):
                    logger.warning(f"Could not parse loss_date: {loss_date_str}")
        
        # Set reported date
        if hasattr(claim, 'created_at') and claim.created_at:
            record.reported_date = claim.created_at.date() if hasattr(claim.created_at, 'date') else None
        
        # Update loss amounts based on claim status
        claim_status = claim.status.value if hasattr(claim.status, 'value') else str(claim.status)
        
        if claim_status in ['APPROVED', 'AUTHORIZED', 'PAID']:
            approved_amount = getattr(claim, 'approved_amount_cents', None) or 0
            record.reserved_loss_cents = approved_amount
            record.actual_loss_cents = approved_amount
        
        # Calculate actual loss rate
        if record.exposure_cents > 0:
            record.actual_loss_rate = record.actual_loss_cents / record.exposure_cents
        
        record.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(
            f"Updated loss experience record from claim {claim_id} "
            f"(actual_loss: {record.actual_loss_cents})"
        )
        
        return record
    
    def update_from_payout(self, payout_id: str) -> LossExperienceRecord:
        """
        Update loss record when payout is made.
        
        Args:
            payout_id: Payout ID (ULID string)
            
        Returns:
            Updated LossExperienceRecord instance
        """
        try:
            from app.modules.claims.models import Payout
            payout = self.db.query(Payout).filter(Payout.id == payout_id).first()
            if not payout:
                raise PayoutNotFoundError(f"Payout {payout_id} not found")
        except ImportError:
            raise PayoutNotFoundError("Payout model not available")
        
        # Find or create record
        policy_id = getattr(payout, 'policy_id', None)
        if not policy_id:
            raise PayoutNotFoundError("Payout has no policy_id")
        
        record = self.db.query(LossExperienceRecord).filter(
            LossExperienceRecord.policy_id == policy_id
        ).first()
        
        if not record:
            record = self.create_record_from_policy(policy_id)
        
        # Update payout reference
        record.payout_id = payout_id
        
        # Update paid amounts
        payout_status = payout.status.value if hasattr(payout.status, 'value') else str(payout.status)
        
        if payout_status == 'PAID':
            payout_amount = getattr(payout, 'amount_cents', None) or 0
            record.paid_loss_cents = (record.paid_loss_cents or 0) + payout_amount
            record.actual_loss_cents = record.paid_loss_cents + (record.reserved_loss_cents or 0)
            
            # Set settled date
            paid_at = getattr(payout, 'paid_at', None)
            if paid_at:
                record.settled_date = paid_at.date() if hasattr(paid_at, 'date') else None
            
            # Update status
            record.record_status = 'SETTLED'
        
        # Calculate actual loss rate
        if record.exposure_cents > 0:
            record.actual_loss_rate = record.actual_loss_cents / record.exposure_cents
        
        record.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(
            f"Updated loss experience record from payout {payout_id} "
            f"(paid_loss: {record.paid_loss_cents})"
        )
        
        return record
    
    def get_loss_ratio(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date,
        corridor_id: Optional[str] = None,
        carrier_id: Optional[str] = None,
        cargo_type: Optional[str] = None,
        model_version_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate loss ratio for given filters.
        
        Loss Ratio = Actual Loss / Premium
        
        Args:
            tenant_id: Tenant ID (ULID string)
            start_date: Start date for period
            end_date: End date for period
            corridor_id: Optional corridor filter
            carrier_id: Optional carrier filter
            cargo_type: Optional cargo type filter
            model_version_id: Optional model version filter
            
        Returns:
            Dictionary with loss ratio metrics
        """
        query = self.db.query(
            func.sum(LossExperienceRecord.premium_cents).label('total_premium'),
            func.sum(LossExperienceRecord.actual_loss_cents).label('total_actual_loss'),
            func.sum(LossExperienceRecord.expected_loss_cents).label('total_expected_loss'),
            func.sum(LossExperienceRecord.exposure_cents).label('total_exposure'),
            func.count(LossExperienceRecord.id).label('policy_count')
        ).filter(
            LossExperienceRecord.tenant_id == tenant_id,
            LossExperienceRecord.policy_effective_date.between(start_date, end_date)
        )
        
        if corridor_id:
            query = query.filter(LossExperienceRecord.corridor_id == corridor_id)
        if carrier_id:
            query = query.filter(LossExperienceRecord.carrier_id == carrier_id)
        if cargo_type:
            query = query.filter(LossExperienceRecord.cargo_type == cargo_type)
        if model_version_id:
            query = query.filter(LossExperienceRecord.model_version_id == model_version_id)
        
        result = query.first()
        
        total_premium = result.total_premium or 0
        total_actual = result.total_actual_loss or 0
        total_expected = result.total_expected_loss or 0
        total_exposure = result.total_exposure or 0
        policy_count = result.policy_count or 0
        
        loss_ratio = total_actual / total_premium if total_premium > 0 else 0.0
        expected_loss_ratio = total_expected / total_premium if total_premium > 0 else 0.0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "filters": {
                "corridor_id": corridor_id,
                "carrier_id": carrier_id,
                "cargo_type": cargo_type,
                "model_version_id": model_version_id
            },
            "metrics": {
                "total_premium_cents": total_premium,
                "total_actual_loss_cents": total_actual,
                "total_expected_loss_cents": total_expected,
                "total_exposure_cents": total_exposure,
                "policy_count": policy_count,
                
                "loss_ratio": round(loss_ratio, 4),
                "expected_loss_ratio": round(expected_loss_ratio, 4),
                "loss_ratio_vs_expected": round(loss_ratio / expected_loss_ratio, 4) if expected_loss_ratio > 0 else None,
                
                "actual_loss_rate": round(total_actual / total_exposure, 6) if total_exposure > 0 else 0.0,
                "expected_loss_rate": round(total_expected / total_exposure, 6) if total_exposure > 0 else 0.0
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_loss_development(
        self,
        tenant_id: str,
        policy_id: str
    ) -> Dict[str, Any]:
        """
        Get loss development for a specific policy.
        
        Shows how loss estimate evolved over time.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            policy_id: Policy ID (ULID string)
            
        Returns:
            Dictionary with loss development data
        """
        record = self.db.query(LossExperienceRecord).filter(
            LossExperienceRecord.tenant_id == tenant_id,
            LossExperienceRecord.policy_id == policy_id
        ).first()
        
        if not record:
            raise RecordNotFoundError(f"No loss record for policy {policy_id}")
        
        # Get claim events if any
        claim_events = []
        if record.claim_id:
            try:
                from app.modules.claims.models import ClaimEvent
                events = self.db.query(ClaimEvent).filter(
                    ClaimEvent.claim_id == record.claim_id
                ).order_by(ClaimEvent.created_at).all()
                
                claim_events = [
                    {
                        "event_type": getattr(e, 'event_type', None),
                        "created_at": e.created_at.isoformat() if hasattr(e, 'created_at') and e.created_at else None,
                        "payload": getattr(e, 'payload_json', None) or {}
                    }
                    for e in events
                ]
            except (ImportError, AttributeError) as e:
                logger.warning(f"Could not fetch claim events: {e}")
        
        # Calculate variance
        expected_loss = record.expected_loss_cents or 0
        actual_loss = record.actual_loss_cents or 0
        expected_rate = record.expected_loss_rate or 0.0
        actual_rate = record.actual_loss_rate or 0.0
        
        return {
            "policy_id": policy_id,
            "exposure_cents": record.exposure_cents,
            "premium_cents": record.premium_cents,
            
            "expected": {
                "loss_cents": expected_loss,
                "loss_rate": expected_rate,
                "risk_score": record.risk_score_at_bind,
                "model_version_id": record.model_version_id
            },
            
            "actual": {
                "loss_cents": actual_loss,
                "loss_rate": actual_rate,
                "paid_cents": record.paid_loss_cents or 0,
                "reserved_cents": record.reserved_loss_cents or 0
            },
            
            "variance": {
                "loss_cents": actual_loss - expected_loss,
                "loss_rate": actual_rate - expected_rate,
                "variance_pct": ((actual_loss - expected_loss) / expected_loss * 100) if expected_loss > 0 else None
            },
            
            "timeline": {
                "policy_effective": record.policy_effective_date.isoformat() if record.policy_effective_date else None,
                "loss_date": record.loss_date.isoformat() if record.loss_date else None,
                "reported_date": record.reported_date.isoformat() if record.reported_date else None,
                "settled_date": record.settled_date.isoformat() if record.settled_date else None
            },
            
            "claim_events": claim_events,
            "record_status": record.record_status
        }
    
    def get_loss_ratio_by_dimension(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date,
        dimension: str  # 'corridor', 'carrier', 'cargo_type', 'coverage_type', 'model_version'
    ) -> List[Dict[str, Any]]:
        """
        Get loss ratios broken down by dimension.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            start_date: Start date for period
            end_date: End date for period
            dimension: Dimension to group by
            
        Returns:
            List of dictionaries with loss ratio metrics by dimension value
        """
        dimension_map = {
            'corridor': LossExperienceRecord.corridor_id,
            'carrier': LossExperienceRecord.carrier_id,
            'cargo_type': LossExperienceRecord.cargo_type,
            'coverage_type': LossExperienceRecord.coverage_type,
            'model_version': LossExperienceRecord.model_version_id
        }
        
        dimension_column = dimension_map.get(dimension)
        
        if not dimension_column:
            raise ValueError(f"Invalid dimension: {dimension}. Must be one of: {list(dimension_map.keys())}")
        
        results = self.db.query(
            dimension_column.label('dimension_value'),
            func.sum(LossExperienceRecord.premium_cents).label('premium'),
            func.sum(LossExperienceRecord.actual_loss_cents).label('actual_loss'),
            func.sum(LossExperienceRecord.expected_loss_cents).label('expected_loss'),
            func.sum(LossExperienceRecord.exposure_cents).label('exposure'),
            func.count(LossExperienceRecord.id).label('count')
        ).filter(
            LossExperienceRecord.tenant_id == tenant_id,
            LossExperienceRecord.policy_effective_date.between(start_date, end_date)
        ).group_by(dimension_column).all()
        
        return [
            {
                "dimension": dimension,
                "value": str(r.dimension_value) if r.dimension_value else "Unknown",
                "premium_cents": r.premium or 0,
                "actual_loss_cents": r.actual_loss or 0,
                "expected_loss_cents": r.expected_loss or 0,
                "exposure_cents": r.exposure or 0,
                "policy_count": r.count,
                "loss_ratio": round((r.actual_loss or 0) / r.premium, 4) if r.premium and r.premium > 0 else 0.0,
                "expected_loss_ratio": round((r.expected_loss or 0) / r.premium, 4) if r.premium and r.premium > 0 else 0.0,
                "actual_loss_rate": round((r.actual_loss or 0) / r.exposure, 6) if r.exposure and r.exposure > 0 else 0.0,
                "expected_loss_rate": round((r.expected_loss or 0) / r.exposure, 6) if r.exposure and r.exposure > 0 else 0.0
            }
            for r in results
        ]
    
    def get_model_performance_report(
        self,
        tenant_id: str,
        model_version_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate model performance report for calibration.
        
        Compares expected vs actual loss to evaluate model accuracy.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            model_version_id: Model version ID (ULID string)
            start_date: Start date for period
            end_date: End date for period
            
        Returns:
            Dictionary with model performance metrics and recommendations
        """
        records = self.db.query(LossExperienceRecord).filter(
            LossExperienceRecord.tenant_id == tenant_id,
            LossExperienceRecord.model_version_id == model_version_id,
            LossExperienceRecord.policy_effective_date.between(start_date, end_date)
        ).all()
        
        if not records:
            return {
                "model_version_id": model_version_id,
                "error": "No data for this model version in date range",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
        
        # Calculate metrics
        total_expected = sum(r.expected_loss_cents or 0 for r in records)
        total_actual = sum(r.actual_loss_cents or 0 for r in records)
        total_exposure = sum(r.exposure_cents or 0 for r in records)
        total_premium = sum(r.premium_cents or 0 for r in records)
        
        # Risk score distribution
        risk_scores = [r.risk_score_at_bind for r in records if r.risk_score_at_bind is not None]
        
        # Calculate prediction error
        prediction_errors = []
        for r in records:
            if r.expected_loss_cents and r.actual_loss_cents is not None and r.expected_loss_cents > 0:
                error = (r.actual_loss_cents - r.expected_loss_cents) / r.expected_loss_cents
                prediction_errors.append(error)
        
        # Binned analysis by risk score
        bins = self._bin_by_risk_score(records)
        
        return {
            "model_version_id": model_version_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_policies": len(records),
                "total_exposure_cents": total_exposure,
                "total_premium_cents": total_premium,
                "total_expected_loss_cents": total_expected,
                "total_actual_loss_cents": total_actual
            },
            "accuracy_metrics": {
                "expected_vs_actual_ratio": round(total_expected / total_actual, 4) if total_actual > 0 else None,
                "mean_prediction_error": round(sum(prediction_errors) / len(prediction_errors), 4) if prediction_errors else None,
                "prediction_error_std": self._std(prediction_errors) if prediction_errors else None,
                "loss_ratio": round(total_actual / total_premium, 4) if total_premium > 0 else 0.0,
                "expected_loss_ratio": round(total_expected / total_premium, 4) if total_premium > 0 else 0.0,
                "actual_loss_rate": round(total_actual / total_exposure, 6) if total_exposure > 0 else 0.0,
                "expected_loss_rate": round(total_expected / total_exposure, 6) if total_exposure > 0 else 0.0
            },
            "risk_score_distribution": {
                "min": min(risk_scores) if risk_scores else None,
                "max": max(risk_scores) if risk_scores else None,
                "mean": round(sum(risk_scores) / len(risk_scores), 4) if risk_scores else None,
                "std": self._std(risk_scores) if risk_scores else None,
                "count": len(risk_scores)
            },
            "binned_analysis": bins,
            "calibration_recommendation": self._get_calibration_recommendation(
                total_expected, total_actual, prediction_errors
            ),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _bin_by_risk_score(self, records: List[LossExperienceRecord]) -> List[Dict[str, Any]]:
        """
        Bin records by risk score ranges.
        
        Args:
            records: List of LossExperienceRecord instances
            
        Returns:
            List of dictionaries with binned analysis
        """
        bins = [
            (0.0, 0.2, "Very Low"),
            (0.2, 0.4, "Low"),
            (0.4, 0.6, "Medium"),
            (0.6, 0.8, "High"),
            (0.8, 1.0, "Very High")
        ]
        
        results = []
        for low, high, label in bins:
            bin_records = [
                r for r in records
                if r.risk_score_at_bind is not None and low <= r.risk_score_at_bind < high
            ]
            
            if bin_records:
                expected = sum(r.expected_loss_cents or 0 for r in bin_records)
                actual = sum(r.actual_loss_cents or 0 for r in bin_records)
                exposure = sum(r.exposure_cents or 0 for r in bin_records)
                
                results.append({
                    "bin": label,
                    "range": f"{low}-{high}",
                    "count": len(bin_records),
                    "expected_loss_cents": expected,
                    "actual_loss_cents": actual,
                    "exposure_cents": exposure,
                    "accuracy_ratio": round(expected / actual, 4) if actual > 0 else None,
                    "expected_loss_rate": round(expected / exposure, 6) if exposure > 0 else 0.0,
                    "actual_loss_rate": round(actual / exposure, 6) if exposure > 0 else 0.0
                })
        
        return results
    
    def _get_calibration_recommendation(
        self,
        expected: int,
        actual: int,
        errors: List[float]
    ) -> Dict[str, Any]:
        """
        Generate calibration recommendation based on model performance.
        
        Args:
            expected: Total expected loss in cents
            actual: Total actual loss in cents
            errors: List of prediction errors (relative)
            
        Returns:
            Dictionary with calibration recommendation
        """
        if not actual or actual == 0:
            return {
                "recommendation": "INSUFFICIENT_DATA",
                "reason": "No actual losses recorded"
            }
        
        ratio = expected / actual if actual > 0 else 0
        mean_error = sum(errors) / len(errors) if errors else 0
        
        if 0.9 <= ratio <= 1.1 and abs(mean_error) < 0.1:
            return {
                "recommendation": "NO_ACTION",
                "reason": "Model is well calibrated",
                "expected_actual_ratio": round(ratio, 4),
                "mean_error": round(mean_error, 4)
            }
        elif ratio > 1.1:
            return {
                "recommendation": "REDUCE_ESTIMATES",
                "reason": "Model overestimates losses",
                "suggested_adjustment": round(1 - ratio, 4),
                "expected_actual_ratio": round(ratio, 4),
                "mean_error": round(mean_error, 4)
            }
        else:
            return {
                "recommendation": "INCREASE_ESTIMATES",
                "reason": "Model underestimates losses",
                "suggested_adjustment": round(ratio - 1, 4),
                "expected_actual_ratio": round(ratio, 4),
                "mean_error": round(mean_error, 4)
            }
    
    def _std(self, values: List[float]) -> float:
        """
        Calculate standard deviation.
        
        Args:
            values: List of numeric values
            
        Returns:
            Standard deviation
        """
        if not values or len(values) == 0:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return round(variance ** 0.5, 4)
    
    def generate_loss_ratio_report(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date,
        include_dimensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive loss ratio report.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            start_date: Start date for period
            end_date: End date for period
            include_dimensions: List of dimensions to include (default: ['corridor', 'cargo_type', 'model_version'])
            
        Returns:
            Dictionary with comprehensive loss ratio report
        """
        include_dimensions = include_dimensions or ['corridor', 'cargo_type', 'model_version']
        
        report = {
            "report_type": "LOSS_RATIO",
            "tenant_id": tenant_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Overall metrics
        report["overall"] = self.get_loss_ratio(tenant_id, start_date, end_date)
        
        # Dimensional breakdowns
        report["by_dimension"] = {}
        for dim in include_dimensions:
            try:
                report["by_dimension"][dim] = self.get_loss_ratio_by_dimension(
                    tenant_id, start_date, end_date, dim
                )
            except ValueError as e:
                logger.warning(f"Could not generate breakdown for dimension {dim}: {e}")
        
        return report
    
    def _generate_id(self) -> str:
        """
        Generate ULID for record ID.
        
        Returns:
            ULID string
        """
        from app.shared.utils import generate_ulid
        return generate_ulid()


# Exception classes
class PolicyNotFoundError(Exception):
    """Policy not found"""
    pass


class ClaimNotFoundError(Exception):
    """Claim not found"""
    pass


class PayoutNotFoundError(Exception):
    """Payout not found"""
    pass


class RecordNotFoundError(Exception):
    """Loss experience record not found"""
    pass
