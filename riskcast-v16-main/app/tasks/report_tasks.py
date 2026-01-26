"""
Report Generation Background Tasks
"""

from datetime import datetime, date, timedelta
from typing import Dict, Optional
import asyncio

from celery.utils.log import get_task_logger

from app.tasks.celery_app import celery_app


logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.report_tasks.generate_daily_risk_report",
    time_limit=1800
)
def generate_daily_risk_report(self, tenant_id: Optional[str] = None) -> Dict:
    """
    Generate daily risk report for tenant(s).
    """
    logger.info(f"Generating daily risk report for tenant: {tenant_id or 'ALL'}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _async_generate_daily_report(tenant_id)
        )
        return result
    finally:
        loop.close()


async def _async_generate_daily_report(tenant_id: Optional[str]) -> Dict:
    """Async report generation."""
    from app.database import SessionLocal
    from sqlalchemy import select, func
    from app.models.quote import Quote
    from app.models.policy import Policy
    from app.models.claim import Claim
    
    db = SessionLocal()
    try:
        yesterday = date.today() - timedelta(days=1)
        
        # Build query base
        quote_query = select(func.count(Quote.id))
        policy_query = select(func.count(Policy.id))
        claim_query = select(func.count(Claim.id))
        
        if tenant_id:
            quote_query = quote_query.where(Quote.tenant_id == tenant_id)
            policy_query = policy_query.where(Policy.tenant_id == tenant_id)
            claim_query = claim_query.where(Claim.tenant_id == tenant_id)
        
        # Quotes created yesterday
        result = db.execute(
            quote_query.where(func.date(Quote.created_at) == yesterday)
        )
        quotes_created = result.scalar() or 0
        
        # Policies issued yesterday
        result = db.execute(
            policy_query.where(func.date(Policy.created_at) == yesterday)
        )
        policies_issued = result.scalar() or 0
        
        # Claims filed yesterday
        result = db.execute(
            claim_query.where(func.date(Claim.filed_at) == yesterday)
        )
        claims_filed = result.scalar() or 0
        
        report = {
            "report_type": "daily_risk",
            "report_date": yesterday.isoformat(),
            "tenant_id": tenant_id or "ALL",
            "metrics": {
                "quotes_created": quotes_created,
                "policies_issued": policies_issued,
                "claims_filed": claims_filed,
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Store report
        # ... save to database or S3 ...
        
        logger.info(f"Daily report generated: {report['report_date']}")
        return report
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.report_tasks.generate_portfolio_report",
    time_limit=3600
)
def generate_portfolio_report(
    self,
    tenant_id: str,
    report_type: str = "summary",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict:
    """
    Generate comprehensive portfolio report.
    """
    logger.info(f"Generating portfolio report for tenant {tenant_id}")
    
    # Implementation would generate detailed PDF report
    return {
        "report_type": report_type,
        "tenant_id": tenant_id,
        "start_date": start_date,
        "end_date": end_date,
        "status": "generated",
        "download_url": f"/api/v3/reports/{tenant_id}/portfolio-{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    }


@celery_app.task(name="app.tasks.report_tasks.generate_claims_report")
def generate_claims_report(
    tenant_id: str,
    period: str = "monthly"
) -> Dict:
    """Generate claims report."""
    logger.info(f"Generating {period} claims report for {tenant_id}")
    
    return {
        "report_type": "claims",
        "period": period,
        "tenant_id": tenant_id,
        "generated_at": datetime.utcnow().isoformat()
    }
