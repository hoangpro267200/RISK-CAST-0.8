"""
API Dependencies
FastAPI dependencies for API routes.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.audit import create_immutable_audit_ledger, ImmutableAuditLedger


def get_audit(db: Session = Depends(get_db)) -> ImmutableAuditLedger:
    """Get immutable audit ledger instance."""
    return create_immutable_audit_ledger(db)
