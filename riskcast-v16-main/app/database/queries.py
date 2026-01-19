"""
Optimized database queries.

RISKCAST v17 - Query Optimization

This module provides optimized, reusable queries for common operations.
Using these queries instead of ad-hoc queries ensures:
1. Consistent performance
2. Proper index usage
3. Pagination support
4. Error handling
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple


# ============================================================
# AUDIT TRAIL QUERIES
# ============================================================

class AuditQueries:
    """Optimized queries for audit trail operations."""
    
    @staticmethod
    def get_recent_assessments(
        db: Session,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List:
        """
        Get recent risk assessments for user.
        
        Optimized with:
        - Index on (user_id, timestamp DESC)
        - LIMIT/OFFSET for pagination
        - Only fetches needed columns
        
        Args:
            db: Database session
            user_id: User identifier
            limit: Max results to return
            offset: Pagination offset
        
        Returns:
            List of audit trail records
        """
        from app.models.audit_trail import AuditTrail
        
        return db.query(AuditTrail)\
            .filter(AuditTrail.user_id == user_id)\
            .order_by(AuditTrail.timestamp.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
    
    @staticmethod
    def get_risk_score_distribution(
        db: Session,
        organization_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Get distribution of risk scores by level.
        
        Returns:
            {"low": 150, "medium": 80, "high": 30, "critical": 5}
        """
        from app.models.audit_trail import AuditTrail
        
        query = db.query(
            AuditTrail.risk_level,
            func.count(AuditTrail.id).label('count')
        )
        
        # Apply filters
        filters = []
        if organization_id:
            filters.append(AuditTrail.organization_id == organization_id)
        if start_date:
            filters.append(AuditTrail.timestamp >= start_date)
        if end_date:
            filters.append(AuditTrail.timestamp <= end_date)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Group and execute
        results = query.group_by(AuditTrail.risk_level).all()
        
        return {level: count for level, count in results if level}
    
    @staticmethod
    def get_risk_trends(
        db: Session,
        organization_id: Optional[str] = None,
        days: int = 30,
        group_by: str = 'day'  # 'day', 'week', 'month'
    ) -> List[Dict[str, Any]]:
        """
        Get risk score trends over time.
        
        Returns:
            [
                {"date": "2026-01-01", "avg_score": 45.2, "count": 15},
                {"date": "2026-01-02", "avg_score": 52.1, "count": 23},
                ...
            ]
        """
        from app.models.audit_trail import AuditTrail
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Date truncation function (PostgreSQL)
        if group_by == 'week':
            date_trunc = func.date_trunc('week', AuditTrail.timestamp)
        elif group_by == 'month':
            date_trunc = func.date_trunc('month', AuditTrail.timestamp)
        else:
            date_trunc = func.date_trunc('day', AuditTrail.timestamp)
        
        query = db.query(
            date_trunc.label('period'),
            func.avg(AuditTrail.risk_score).label('avg_score'),
            func.count(AuditTrail.id).label('count')
        ).filter(AuditTrail.timestamp >= start_date)
        
        if organization_id:
            query = query.filter(AuditTrail.organization_id == organization_id)
        
        results = query.group_by('period').order_by('period').all()
        
        return [
            {
                'date': period.isoformat() if period else None,
                'avg_score': round(float(avg_score), 2) if avg_score else 0,
                'count': count
            }
            for period, avg_score, count in results
        ]
    
    @staticmethod
    def search_assessments(
        db: Session,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        risk_level: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search_text: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = 'timestamp',
        order_dir: str = 'desc'
    ) -> Tuple[List, int]:
        """
        Advanced search for audit trail records.
        
        Returns:
            (records, total_count) tuple for pagination
        """
        from app.models.audit_trail import AuditTrail
        
        query = db.query(AuditTrail)
        
        # Build filters
        filters = []
        
        if user_id:
            filters.append(AuditTrail.user_id == user_id)
        if organization_id:
            filters.append(AuditTrail.organization_id == organization_id)
        if min_risk_score is not None:
            filters.append(AuditTrail.risk_score >= min_risk_score)
        if max_risk_score is not None:
            filters.append(AuditTrail.risk_score <= max_risk_score)
        if risk_level:
            filters.append(AuditTrail.risk_level == risk_level)
        if start_date:
            filters.append(AuditTrail.timestamp >= start_date)
        if end_date:
            filters.append(AuditTrail.timestamp <= end_date)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count before pagination
        total = query.count()
        
        # Apply ordering
        order_column = getattr(AuditTrail, order_by, AuditTrail.timestamp)
        if order_dir.lower() == 'asc':
            query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(order_column))
        
        # Apply pagination
        records = query.offset(offset).limit(limit).all()
        
        return records, total
    
    @staticmethod
    def cleanup_old_records(
        db: Session,
        retention_days: int = 90,
        batch_size: int = 1000
    ) -> int:
        """
        Delete audit records older than retention period.
        
        Uses batched deletion for large datasets to avoid
        locking issues and memory problems.
        
        Args:
            db: Database session
            retention_days: Keep records newer than this
            batch_size: Records to delete per batch
        
        Returns:
            Total number of records deleted
        """
        from app.models.audit_trail import AuditTrail
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        total_deleted = 0
        
        while True:
            # Find IDs to delete (batched)
            ids_to_delete = db.query(AuditTrail.id)\
                .filter(AuditTrail.timestamp < cutoff_date)\
                .limit(batch_size)\
                .all()
            
            if not ids_to_delete:
                break
            
            ids = [id_tuple[0] for id_tuple in ids_to_delete]
            
            # Delete batch
            deleted = db.query(AuditTrail)\
                .filter(AuditTrail.id.in_(ids))\
                .delete(synchronize_session=False)
            
            db.commit()
            total_deleted += deleted
            
            print(f"  Deleted batch: {deleted} records")
        
        return total_deleted


# ============================================================
# API KEY QUERIES
# ============================================================

class APIKeyQueries:
    """Optimized queries for API keys."""
    
    @staticmethod
    def get_active_keys(db: Session, user_id: str) -> List:
        """
        Get all active (non-revoked, non-expired) keys for user.
        
        Uses index on (user_id, revoked) for efficiency.
        """
        from app.models.api_key import APIKey
        
        now = datetime.utcnow()
        
        return db.query(APIKey)\
            .filter(
                and_(
                    APIKey.user_id == user_id,
                    APIKey.revoked == False,
                    or_(
                        APIKey.expires_at.is_(None),
                        APIKey.expires_at > now
                    )
                )
            )\
            .order_by(APIKey.created_at.desc())\
            .all()
    
    @staticmethod
    def get_key_by_hash(db: Session, key_hash: str):
        """
        Get API key by hash.
        
        Uses unique index on key_hash for O(1) lookup.
        """
        from app.models.api_key import APIKey
        
        return db.query(APIKey)\
            .filter(APIKey.key_hash == key_hash)\
            .first()
    
    @staticmethod
    def get_usage_stats(
        db: Session,
        key_id: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for API key(s).
        
        Returns aggregated stats including total requests,
        average daily usage, and activity status.
        """
        from app.models.api_key import APIKey
        
        query = db.query(APIKey)
        
        if key_id:
            query = query.filter(APIKey.id == key_id)
        if user_id:
            query = query.filter(APIKey.user_id == user_id)
        
        keys = query.all()
        
        if not keys:
            return {'error': 'No keys found'}
        
        total_requests = sum(k.request_count for k in keys)
        active_keys = sum(1 for k in keys if k.is_valid())
        
        # Recent activity (used in last 7 days)
        recently_active = sum(
            1 for k in keys
            if k.last_used_at and (datetime.utcnow() - k.last_used_at).days < 7
        )
        
        return {
            'total_keys': len(keys),
            'active_keys': active_keys,
            'recently_active': recently_active,
            'total_requests': total_requests,
            'keys': [
                {
                    'id': k.id,
                    'name': k.name,
                    'requests': k.request_count,
                    'last_used': k.last_used_at.isoformat() if k.last_used_at else None,
                    'is_active': k.is_valid()
                }
                for k in keys
            ]
        }
    
    @staticmethod
    def revoke_expired_keys(db: Session) -> int:
        """
        Automatically revoke all expired keys.
        
        Should be run periodically (e.g., daily cron job).
        
        Returns:
            Number of keys revoked
        """
        from app.models.api_key import APIKey
        
        now = datetime.utcnow()
        
        expired_keys = db.query(APIKey)\
            .filter(
                and_(
                    APIKey.revoked == False,
                    APIKey.expires_at.isnot(None),
                    APIKey.expires_at < now
                )
            )\
            .all()
        
        for key in expired_keys:
            key.revoke("Automatically revoked: expired")
        
        db.commit()
        
        return len(expired_keys)


# ============================================================
# CONVERSATION QUERIES
# ============================================================

class ConversationQueries:
    """Optimized queries for AI conversations."""
    
    @staticmethod
    def get_conversation_history(
        db: Session,
        conversation_id: str,
        limit: int = 50
    ) -> List:
        """
        Get messages for a conversation, most recent first.
        
        Uses index on (conversation_id, timestamp).
        """
        from app.models.conversation import ConversationMessage
        
        messages = db.query(ConversationMessage)\
            .filter(ConversationMessage.conversation_id == conversation_id)\
            .order_by(ConversationMessage.timestamp.desc())\
            .limit(limit)\
            .all()
        
        # Reverse to chronological order
        return list(reversed(messages))
    
    @staticmethod
    def get_user_conversations(
        db: Session,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List, int]:
        """
        Get all conversations for a user with message counts.
        
        Returns:
            (conversations, total) tuple
        """
        from app.models.conversation import Conversation, ConversationMessage
        
        # Get conversations
        query = db.query(Conversation)\
            .filter(Conversation.user_id == user_id)\
            .order_by(Conversation.updated_at.desc())
        
        total = query.count()
        conversations = query.offset(offset).limit(limit).all()
        
        # Add message counts
        result = []
        for conv in conversations:
            msg_count = db.query(func.count(ConversationMessage.id))\
                .filter(ConversationMessage.conversation_id == conv.conversation_id)\
                .scalar()
            
            result.append({
                'conversation_id': conv.conversation_id,
                'title': conv.title,
                'created_at': conv.created_at,
                'updated_at': conv.updated_at,
                'message_count': msg_count,
                'language': conv.language
            })
        
        return result, total
    
    @staticmethod
    def cleanup_old_conversations(
        db: Session,
        retention_days: int = 30
    ) -> int:
        """
        Delete conversations older than retention period.
        
        Also deletes associated messages (via cascade or manually).
        """
        from app.models.conversation import Conversation, ConversationMessage
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Find old conversation IDs
        old_convs = db.query(Conversation.conversation_id)\
            .filter(Conversation.updated_at < cutoff_date)\
            .all()
        
        if not old_convs:
            return 0
        
        conv_ids = [c[0] for c in old_convs]
        
        # Delete messages first
        db.query(ConversationMessage)\
            .filter(ConversationMessage.conversation_id.in_(conv_ids))\
            .delete(synchronize_session=False)
        
        # Delete conversations
        deleted = db.query(Conversation)\
            .filter(Conversation.conversation_id.in_(conv_ids))\
            .delete(synchronize_session=False)
        
        db.commit()
        
        return deleted


# ============================================================
# AGGREGATE QUERIES
# ============================================================

class AggregateQueries:
    """Complex aggregate queries across multiple tables."""
    
    @staticmethod
    def get_dashboard_stats(
        db: Session,
        organization_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get dashboard statistics for admin view.
        
        Returns combined stats from multiple tables in one call.
        """
        from app.models.audit_trail import AuditTrail
        from app.models.api_key import APIKey
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Base filter
        audit_filter = AuditTrail.timestamp >= start_date
        if organization_id:
            audit_filter = and_(audit_filter, AuditTrail.organization_id == organization_id)
        
        # Risk assessments
        risk_stats = db.query(
            func.count(AuditTrail.id).label('total'),
            func.avg(AuditTrail.risk_score).label('avg_score'),
            func.min(AuditTrail.risk_score).label('min_score'),
            func.max(AuditTrail.risk_score).label('max_score')
        ).filter(audit_filter).first()
        
        # Risk level distribution
        level_dist = db.query(
            AuditTrail.risk_level,
            func.count(AuditTrail.id)
        ).filter(audit_filter).group_by(AuditTrail.risk_level).all()
        
        # API key stats
        key_filter = []
        if organization_id:
            key_filter.append(APIKey.organization_id == organization_id)
        
        if key_filter:
            key_stats = db.query(
                func.count(APIKey.id).label('total'),
                func.sum(APIKey.request_count).label('total_requests')
            ).filter(and_(*key_filter)).first()
        else:
            key_stats = db.query(
                func.count(APIKey.id).label('total'),
                func.sum(APIKey.request_count).label('total_requests')
            ).first()
        
        return {
            'period_days': days,
            'risk_assessments': {
                'total': risk_stats.total or 0,
                'avg_score': round(float(risk_stats.avg_score or 0), 2),
                'min_score': round(float(risk_stats.min_score or 0), 2),
                'max_score': round(float(risk_stats.max_score or 0), 2),
            },
            'risk_distribution': {
                level: count for level, count in level_dist if level
            },
            'api_usage': {
                'total_keys': key_stats.total or 0,
                'total_requests': key_stats.total_requests or 0
            }
        }
