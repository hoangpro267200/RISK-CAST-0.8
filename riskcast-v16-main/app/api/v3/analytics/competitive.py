"""
Competitive Analysis API

Provides data for competitive analysis:
- Market positioning
- Rate comparisons
- Win/loss analysis
- Market trends
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, case, and_
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_audit
from app.shared.dependencies import get_current_user
from app.core.audit.immutable_ledger import ImmutableAuditLedger
from sqlalchemy import func, case, and_


router = APIRouter(prefix="/analytics/competitive", tags=["Competitive Analytics"])


# ============================================================================
# Schemas
# ============================================================================

class MarketPosition(BaseModel):
    """Market positioning analysis."""
    period: str
    our_avg_rate_per_mille: float
    market_avg_rate_per_mille: float
    position: str  # BELOW_MARKET, AT_MARKET, ABOVE_MARKET
    rate_index: float  # Our rate / Market rate
    
    by_cargo_type: Dict[str, Dict[str, float]]
    by_route: Dict[str, Dict[str, float]]


class WinLossAnalysis(BaseModel):
    """Quote win/loss analysis."""
    period: str
    total_quotes: int
    accepted: int
    declined: int
    expired: int
    conversion_rate: float
    
    decline_reasons: Dict[str, int]
    win_characteristics: Dict[str, Any]
    loss_characteristics: Dict[str, Any]


class MarketTrend(BaseModel):
    """Market trend data point."""
    date: str
    avg_rate: float
    quote_volume: int
    conversion_rate: float
    avg_cargo_value: float


class CompetitorInsight(BaseModel):
    """Competitor insight (aggregated/anonymized)."""
    competitor_id: str  # Anonymized
    estimated_market_share: float
    avg_rate_index: float  # vs market
    primary_segments: List[str]
    strengths: List[str]
    weaknesses: List[str]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/market-position", response_model=MarketPosition)
async def get_market_position(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get market positioning analysis.
    
    Compares our rates to market averages.
    """
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()
    
    from app.models.quote import Quote
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Extract rate_per_mille from pricing_snapshot_json
    # Our average rate
    quotes = db.query(Quote).filter(
        Quote.created_at >= start_datetime,
        Quote.created_at <= end_datetime
    ).all()
    
    rates = []
    for q in quotes:
        if q.pricing_snapshot_json and isinstance(q.pricing_snapshot_json, dict):
            rate = q.pricing_snapshot_json.get("rate_per_mille")
            if rate:
                rates.append(float(rate))
    
    our_avg_rate = sum(rates) / len(rates) if rates else 0
    
    # Market average (would come from market data service)
    # Placeholder - in production would use real market data
    market_avg = 2.0
    
    rate_index = our_avg_rate / market_avg if market_avg > 0 else 1.0
    
    if rate_index < 0.9:
        position = "BELOW_MARKET"
    elif rate_index <= 1.1:
        position = "AT_MARKET"
    else:
        position = "ABOVE_MARKET"
    
    # By cargo type
    by_cargo_dict = {}
    cargo_groups = {}
    for q in quotes:
        if q.coverage_terms_json and isinstance(q.coverage_terms_json, dict):
            cargo_type = q.coverage_terms_json.get("cargo_type", "UNKNOWN")
            if cargo_type not in cargo_groups:
                cargo_groups[cargo_type] = []
            if q.pricing_snapshot_json and isinstance(q.pricing_snapshot_json, dict):
                rate = q.pricing_snapshot_json.get("rate_per_mille")
                if rate:
                    cargo_groups[cargo_type].append(float(rate))
    
    for cargo_type, rates_list in cargo_groups.items():
        if rates_list:
            avg_rate = sum(rates_list) / len(rates_list)
            by_cargo_dict[cargo_type] = {
                "our_rate": avg_rate,
                "market_rate": market_avg,
                "index": avg_rate / market_avg if market_avg > 0 else 1.0,
                "quote_count": len(rates_list)
            }
    
    # By route (top routes)
    route_groups = {}
    for q in quotes:
        if q.coverage_terms_json and isinstance(q.coverage_terms_json, dict):
            origin = q.coverage_terms_json.get("origin_port", "UNKNOWN")
            dest = q.coverage_terms_json.get("destination_port", "UNKNOWN")
            route_key = f"{origin}-{dest}"
            if route_key not in route_groups:
                route_groups[route_key] = []
            if q.pricing_snapshot_json and isinstance(q.pricing_snapshot_json, dict):
                rate = q.pricing_snapshot_json.get("rate_per_mille")
                if rate:
                    route_groups[route_key].append(float(rate))
    
    # Sort by count and take top 10
    route_list = [(k, v) for k, v in route_groups.items()]
    route_list.sort(key=lambda x: len(x[1]), reverse=True)
    top_routes = route_list[:10]
    
    by_route_dict = {}
    for route_key, rates_list in top_routes:
        if rates_list:
            avg_rate = sum(rates_list) / len(rates_list)
            by_route_dict[route_key] = {
                "our_rate": avg_rate,
                "market_rate": market_avg,
                "index": avg_rate / market_avg if market_avg > 0 else 1.0,
                "quote_count": len(rates_list)
            }
    
    return MarketPosition(
        period=f"{start_date} to {end_date}",
        our_avg_rate_per_mille=our_avg_rate,
        market_avg_rate_per_mille=market_avg,
        position=position,
        rate_index=rate_index,
        by_cargo_type=by_cargo_dict,
        by_route=by_route_dict
    )


@router.get("/win-loss", response_model=WinLossAnalysis)
async def get_win_loss_analysis(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get quote win/loss analysis.
    
    Analyzes quote conversion and decline patterns.
    """
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()
    
    from app.models.quote import Quote
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Get quote counts by status
    quotes = db.query(Quote).filter(
        Quote.created_at >= start_datetime,
        Quote.created_at <= end_datetime
    ).all()
    
    counts = {}
    for q in quotes:
        status = q.status
        counts[status] = counts.get(status, 0) + 1
    
    total = len(quotes)
    accepted = counts.get("ACCEPTED", 0) + counts.get("BOUND", 0)
    declined = counts.get("DECLINED", 0)
    expired = counts.get("EXPIRED", 0)
    
    conversion_rate = accepted / total if total > 0 else 0
    
    # Decline reasons (stored in coverage_terms_json)
    decline_reasons_dict = {}
    for q in quotes:
        if q.status == "DECLINED" and q.coverage_terms_json:
            reason = q.coverage_terms_json.get("decline_reason")
            if reason:
                decline_reasons_dict[reason] = decline_reasons_dict.get(reason, 0) + 1
    
    # Win characteristics (accepted quotes)
    win_rates = []
    win_values = []
    win_risks = []
    for q in quotes:
        if q.status in ["ACCEPTED", "BOUND"]:
            if q.pricing_snapshot_json and isinstance(q.pricing_snapshot_json, dict):
                rate = q.pricing_snapshot_json.get("rate_per_mille")
                value = q.pricing_snapshot_json.get("cargo_value")
                if rate:
                    win_rates.append(float(rate))
                if value:
                    win_values.append(float(value))
            if q.risk_summary_json and isinstance(q.risk_summary_json, dict):
                risk = q.risk_summary_json.get("overall_risk_score")
                if risk:
                    win_risks.append(float(risk))
    
    # Loss characteristics (declined quotes)
    loss_rates = []
    loss_values = []
    loss_risks = []
    for q in quotes:
        if q.status == "DECLINED":
            if q.pricing_snapshot_json and isinstance(q.pricing_snapshot_json, dict):
                rate = q.pricing_snapshot_json.get("rate_per_mille")
                value = q.pricing_snapshot_json.get("cargo_value")
                if rate:
                    loss_rates.append(float(rate))
                if value:
                    loss_values.append(float(value))
            if q.risk_summary_json and isinstance(q.risk_summary_json, dict):
                risk = q.risk_summary_json.get("overall_risk_score")
                if risk:
                    loss_risks.append(float(risk))
    
    return WinLossAnalysis(
        period=f"{start_date} to {end_date}",
        total_quotes=total,
        accepted=accepted,
        declined=declined,
        expired=expired,
        conversion_rate=conversion_rate,
        decline_reasons=decline_reasons_dict,
        win_characteristics={
            "avg_rate_per_mille": sum(win_rates) / len(win_rates) if win_rates else 0,
            "avg_cargo_value": sum(win_values) / len(win_values) if win_values else 0,
            "avg_risk_score": sum(win_risks) / len(win_risks) if win_risks else 0
        },
        loss_characteristics={
            "avg_rate_per_mille": sum(loss_rates) / len(loss_rates) if loss_rates else 0,
            "avg_cargo_value": sum(loss_values) / len(loss_values) if loss_values else 0,
            "avg_risk_score": sum(loss_risks) / len(loss_risks) if loss_risks else 0
        }
    )


@router.get("/trends", response_model=List[MarketTrend])
async def get_market_trends(
    days: int = Query(default=90, le=365),
    granularity: str = Query(default="WEEKLY", description="DAILY, WEEKLY, MONTHLY"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get market trends over time.
    """
    from app.models.quote import Quote
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    quotes = db.query(Quote).filter(
        Quote.created_at >= start_datetime,
        Quote.created_at <= end_datetime
    ).all()
    
    # Group by period
    if granularity == "DAILY":
        def get_period(q):
            return q.created_at.date()
    elif granularity == "MONTHLY":
        def get_period(q):
            return q.created_at.replace(day=1).date()
    else:  # WEEKLY
        def get_period(q):
            # Get Monday of the week
            days_since_monday = q.created_at.weekday()
            return (q.created_at.date() - timedelta(days=days_since_monday))
    
    period_groups = {}
    for q in quotes:
        period = get_period(q)
        if period not in period_groups:
            period_groups[period] = {
                "rates": [],
                "values": [],
                "quotes": [],
                "accepted": 0
            }
        
        if q.pricing_snapshot_json and isinstance(q.pricing_snapshot_json, dict):
            rate = q.pricing_snapshot_json.get("rate_per_mille")
            value = q.pricing_snapshot_json.get("cargo_value")
            if rate:
                period_groups[period]["rates"].append(float(rate))
            if value:
                period_groups[period]["values"].append(float(value))
        
        period_groups[period]["quotes"].append(q)
        if q.status in ["ACCEPTED", "BOUND"]:
            period_groups[period]["accepted"] += 1
    
    trends = []
    for period_date in sorted(period_groups.keys()):
        group = period_groups[period_date]
        avg_rate = sum(group["rates"]) / len(group["rates"]) if group["rates"] else 0
        avg_value = sum(group["values"]) / len(group["values"]) if group["values"] else 0
        volume = len(group["quotes"])
        conversion = group["accepted"] / volume if volume > 0 else 0
        
        trends.append(MarketTrend(
            date=str(period_date),
            avg_rate=avg_rate,
            quote_volume=volume,
            conversion_rate=conversion,
            avg_cargo_value=avg_value
        ))
    
    return trends


@router.get("/segment-analysis")
async def get_segment_analysis(
    segment_by: str = Query(default="cargo_type", description="cargo_type, route, customer_tier"),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get segment-level analysis.
    """
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()
    
    from app.models.quote import Quote
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    quotes = db.query(Quote).filter(
        Quote.created_at >= start_datetime,
        Quote.created_at <= end_datetime
    ).all()
    
    # Group by segment
    segment_groups = {}
    for q in quotes:
        if segment_by == "cargo_type":
            segment = q.coverage_terms_json.get("cargo_type", "UNKNOWN") if q.coverage_terms_json else "UNKNOWN"
        elif segment_by == "route":
            origin = q.coverage_terms_json.get("origin_port", "UNKNOWN") if q.coverage_terms_json else "UNKNOWN"
            dest = q.coverage_terms_json.get("destination_port", "UNKNOWN") if q.coverage_terms_json else "UNKNOWN"
            segment = f"{origin}-{dest}"
        else:
            segment = "UNKNOWN"
        
        if segment not in segment_groups:
            segment_groups[segment] = {
                "quotes": [],
                "rates": [],
                "values": [],
                "risks": [],
                "wins": 0,
                "losses": 0
            }
        
        segment_groups[segment]["quotes"].append(q)
        
        if q.pricing_snapshot_json and isinstance(q.pricing_snapshot_json, dict):
            rate = q.pricing_snapshot_json.get("rate_per_mille")
            value = q.pricing_snapshot_json.get("cargo_value")
            if rate:
                segment_groups[segment]["rates"].append(float(rate))
            if value:
                segment_groups[segment]["values"].append(float(value))
        
        if q.risk_summary_json and isinstance(q.risk_summary_json, dict):
            risk = q.risk_summary_json.get("overall_risk_score")
            if risk:
                segment_groups[segment]["risks"].append(float(risk))
        
        if q.status in ["ACCEPTED", "BOUND"]:
            segment_groups[segment]["wins"] += 1
        elif q.status == "DECLINED":
            segment_groups[segment]["losses"] += 1
    
    # Sort by quote count and take top 20
    segment_list = [(k, v) for k, v in segment_groups.items()]
    segment_list.sort(key=lambda x: len(x[1]["quotes"]), reverse=True)
    top_segments = segment_list[:20]
    
    return {
        "segment_by": segment_by,
        "period": f"{start_date} to {end_date}",
        "segments": [
            {
                "segment": seg,
                "quote_count": len(group["quotes"]),
                "total_value": sum(group["values"]),
                "avg_rate_per_mille": sum(group["rates"]) / len(group["rates"]) if group["rates"] else 0,
                "avg_risk_score": sum(group["risks"]) / len(group["risks"]) if group["risks"] else 0,
                "conversion_rate": group["wins"] / len(group["quotes"]) if group["quotes"] else 0,
                "wins": group["wins"],
                "losses": group["losses"]
            }
            for seg, group in top_segments
        ]
    }


@router.get("/pricing-optimization")
async def get_pricing_optimization_insights(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get pricing optimization insights.
    
    Identifies opportunities to improve pricing.
    """
    from app.models.quote import Quote
    
    # Get all quotes
    quotes = db.query(Quote).all()
    
    # Analyze price sensitivity
    # Find segments where we're losing on price
    price_sensitive_segments = {}
    for q in quotes:
        if q.status == "DECLINED" and q.coverage_terms_json:
            reason = q.coverage_terms_json.get("decline_reason")
            if reason == "PRICE_TOO_HIGH":
                cargo_type = q.coverage_terms_json.get("cargo_type", "UNKNOWN")
                if cargo_type not in price_sensitive_segments:
                    price_sensitive_segments[cargo_type] = []
                if q.pricing_snapshot_json and isinstance(q.pricing_snapshot_json, dict):
                    rate = q.pricing_snapshot_json.get("rate_per_mille")
                    if rate:
                        price_sensitive_segments[cargo_type].append(float(rate))
    
    # Filter segments with at least 5 quotes
    price_sensitive = [
        (cargo, rates) for cargo, rates in price_sensitive_segments.items()
        if len(rates) >= 5
    ]
    
    # Find segments where we're winning easily (maybe underpriced)
    easy_win_segments = {}
    for q in quotes:
        if q.status in ["ACCEPTED", "BOUND"]:
            cargo_type = q.coverage_terms_json.get("cargo_type", "UNKNOWN") if q.coverage_terms_json else "UNKNOWN"
            if cargo_type not in easy_win_segments:
                easy_win_segments[cargo_type] = {"wins": 0, "losses": 0}
            easy_win_segments[cargo_type]["wins"] += 1
    
    # Count losses per segment
    for q in quotes:
        if q.status == "DECLINED":
            cargo_type = q.coverage_terms_json.get("cargo_type", "UNKNOWN") if q.coverage_terms_json else "UNKNOWN"
            if cargo_type in easy_win_segments:
                easy_win_segments[cargo_type]["losses"] += 1
    
    # Filter segments with high win rate and at least 10 wins
    easy_wins = [
        cargo for cargo, counts in easy_win_segments.items()
        if counts["wins"] >= 10 and counts["losses"] < counts["wins"] * 0.1
    ]
    
    # Build insights
    insights = []
    
    for cargo_type, rates in price_sensitive:
        avg_rate = sum(rates) / len(rates) if rates else 0
        insights.append({
            "type": "PRICE_SENSITIVITY",
            "segment": cargo_type,
            "message": f"High price sensitivity in {cargo_type}: {len(rates)} quotes lost to pricing",
            "recommendation": f"Consider reducing rates by 5-10% for {cargo_type}",
            "potential_impact": "Could increase conversion by 15-20%",
            "current_avg_rate": avg_rate
        })
    
    for cargo_type in easy_wins:
        counts = easy_win_segments[cargo_type]
        insights.append({
            "type": "POTENTIAL_UNDERPRICING",
            "segment": cargo_type,
            "message": f"Very high conversion in {cargo_type}: may be underpriced (win rate: {counts['wins']/(counts['wins']+counts['losses'])*100:.1f}%)",
            "recommendation": f"Consider increasing rates by 5-10% for {cargo_type}",
            "potential_impact": "Could increase margin without significant volume loss",
            "win_rate": counts["wins"] / (counts["wins"] + counts["losses"]) if (counts["wins"] + counts["losses"]) > 0 else 0
        })
    
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "insights": insights,
        "summary": {
            "price_sensitive_segments": len(price_sensitive),
            "potential_underpriced_segments": len([i for i in insights if i["type"] == "POTENTIAL_UNDERPRICING"])
        }
    }
