"""
Notification Background Tasks
"""

from datetime import datetime, timedelta
from typing import Dict, List
import asyncio

from celery import shared_task
from celery.utils.log import get_task_logger

from app.tasks.celery_app import celery_app


logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.notification_tasks.send_email"
)
def send_email(
    self,
    to_email: str,
    subject: str,
    body: str,
    template: str = None,
    template_data: Dict = None
) -> Dict:
    """
    Send email notification.
    """
    logger.info(f"Sending email to {to_email}: {subject}")
    
    try:
        # Import email service
        # from app.services.email_service import EmailService
        # email_service = EmailService()
        # result = email_service.send(to_email, subject, body, template, template_data)
        
        # Mock for now
        result = {
            "status": "sent",
            "to": to_email,
            "subject": subject,
            "sent_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Email sent to {to_email}")
        return result
        
    except Exception as e:
        logger.error(f"Email failed: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(
    bind=True,
    name="app.tasks.notification_tasks.send_webhook"
)
def send_webhook(
    self,
    webhook_url: str,
    event_type: str,
    payload: Dict
) -> Dict:
    """
    Send webhook notification.
    """
    import aiohttp
    
    logger.info(f"Sending webhook to {webhook_url}: {event_type}")
    
    async def _send():
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json={
                    "event_type": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload": payload
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                return {
                    "status": response.status,
                    "success": response.status < 400
                }
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_send())
        finally:
            loop.close()
        
        if not result["success"]:
            raise Exception(f"Webhook failed with status {result['status']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Webhook failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=5)


@celery_app.task(name="app.tasks.notification_tasks.process_expiring_quotes")
def process_expiring_quotes() -> Dict:
    """
    Process quotes expiring soon and send notifications.
    """
    logger.info("Processing expiring quotes")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_async_process_expiring())
        return result
    finally:
        loop.close()


async def _async_process_expiring() -> Dict:
    """Find and notify about expiring quotes."""
    from app.database import SessionLocal
    from sqlalchemy import select
    from app.models.quote import Quote
    
    expiring_soon = datetime.utcnow() + timedelta(hours=24)
    
    db = SessionLocal()
    try:
        result = db.execute(
            select(Quote)
            .where(Quote.status == "PENDING")
            .where(Quote.valid_until <= expiring_soon)
            .where(Quote.valid_until > datetime.utcnow())
        )
        quotes = result.scalars().all()
        
        notifications_sent = 0
        for quote in quotes:
            # Send notification
            customer_email = getattr(quote, 'customer_email', None) or "customer@example.com"
            send_email.delay(
                to_email=customer_email,
                subject=f"Quote {getattr(quote, 'quote_number', quote.id)} Expiring Soon",
                body=f"Your quote expires at {getattr(quote, 'valid_until', 'soon')}",
                template="quote_expiring"
            )
            notifications_sent += 1
        
        return {
            "expiring_quotes": len(quotes),
            "notifications_sent": notifications_sent,
            "processed_at": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.notification_tasks.send_risk_alert")
def send_risk_alert(
    tenant_id: str,
    alert_type: str,
    alert_data: Dict
) -> Dict:
    """
    Send risk alert to tenant.
    """
    logger.info(f"Sending risk alert to tenant {tenant_id}: {alert_type}")
    
    # Would send via multiple channels based on tenant preferences
    # - Email
    # - Webhook
    # - WebSocket
    # - SMS
    
    return {
        "tenant_id": tenant_id,
        "alert_type": alert_type,
        "sent_at": datetime.utcnow().isoformat()
    }
