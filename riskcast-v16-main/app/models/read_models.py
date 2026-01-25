"""
Read Models for CQRS Projections

These are optimized read models built from events.
"""

from sqlalchemy import Column, String, DateTime, Float, Integer, Text, Date, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date

from app.database import Base


class QuoteSummary(Base):
    """Read model for quote summaries."""
    __tablename__ = "quote_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(String(36), unique=True, nullable=False, index=True)
    customer_id = Column(String(36), nullable=False, index=True)
    cargo_type = Column(String(100), nullable=True)
    cargo_value_usd = Column(Float, nullable=True)
    origin_port = Column(String(50), nullable=True)
    destination_port = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, index=True)
    risk_score = Column(Float, nullable=True)
    total_premium_usd = Column(Float, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    decline_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_quote_summary_customer_status', 'customer_id', 'status'),
        Index('ix_quote_summary_created', 'created_at'),
    )


class DailyMetrics(Base):
    """Read model for daily business metrics."""
    __tablename__ = "daily_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    
    # Quote metrics
    quotes_requested = Column(Integer, default=0, nullable=False)
    quotes_accepted = Column(Integer, default=0, nullable=False)
    total_quote_value = Column(Float, default=0.0, nullable=False)
    
    # Policy metrics
    policies_created = Column(Integer, default=0, nullable=False)
    total_premium = Column(Float, default=0.0, nullable=False)
    
    # Claim metrics
    claims_filed = Column(Integer, default=0, nullable=False)
    claims_paid = Column(Integer, default=0, nullable=False)
    total_claimed = Column(Float, default=0.0, nullable=False)
    total_paid = Column(Float, default=0.0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('ix_daily_metrics_date', 'date'),
    )
