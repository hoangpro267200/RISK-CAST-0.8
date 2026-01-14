"""
Database index definitions for performance optimization.

RISKCAST v17 - Query Optimization

Indexes are crucial for:
1. Fast lookups on commonly queried columns
2. Efficient JOIN operations
3. Quick sorting and filtering
4. Constraint enforcement
"""

from sqlalchemy import Index, text
from typing import List


# ============================================================
# INDEX DEFINITIONS
# ============================================================

def get_index_definitions() -> List[dict]:
    """
    Get all index definitions for the database.
    
    Returns list of dicts with:
    - name: Index name
    - table: Table name
    - columns: List of column names
    - unique: Whether index is unique
    - where: Optional partial index condition
    """
    return [
        # ====== AUDIT TRAIL INDEXES ======
        {
            'name': 'ix_audit_timestamp',
            'table': 'audit_trail',
            'columns': ['timestamp'],
            'unique': False,
            'description': 'Fast filtering by time range'
        },
        {
            'name': 'ix_audit_user_timestamp',
            'table': 'audit_trail',
            'columns': ['user_id', 'timestamp'],
            'unique': False,
            'description': 'User-specific time queries'
        },
        {
            'name': 'ix_audit_org_timestamp',
            'table': 'audit_trail',
            'columns': ['organization_id', 'timestamp'],
            'unique': False,
            'description': 'Organization-specific time queries'
        },
        {
            'name': 'ix_audit_risk_score',
            'table': 'audit_trail',
            'columns': ['risk_score'],
            'unique': False,
            'description': 'Risk score range queries'
        },
        {
            'name': 'ix_audit_risk_level',
            'table': 'audit_trail',
            'columns': ['risk_level'],
            'unique': False,
            'description': 'Filter by risk level (low/medium/high/critical)'
        },
        
        # ====== API KEY INDEXES ======
        {
            'name': 'ix_apikey_hash',
            'table': 'api_keys',
            'columns': ['key_hash'],
            'unique': True,
            'description': 'Fast API key lookup by hash'
        },
        {
            'name': 'ix_apikey_user',
            'table': 'api_keys',
            'columns': ['user_id'],
            'unique': False,
            'description': 'List keys by user'
        },
        {
            'name': 'ix_apikey_org',
            'table': 'api_keys',
            'columns': ['organization_id'],
            'unique': False,
            'description': 'List keys by organization'
        },
        {
            'name': 'ix_apikey_active',
            'table': 'api_keys',
            'columns': ['user_id', 'revoked'],
            'unique': False,
            'description': 'Active keys for user',
            'where': 'revoked = FALSE'  # Partial index (PostgreSQL only)
        },
        
        # ====== CONVERSATION INDEXES ======
        {
            'name': 'ix_conv_user_updated',
            'table': 'conversations',
            'columns': ['user_id', 'updated_at'],
            'unique': False,
            'description': 'Recent conversations for user'
        },
        {
            'name': 'ix_conv_messages_conv',
            'table': 'conversation_messages',
            'columns': ['conversation_id', 'timestamp'],
            'unique': False,
            'description': 'Messages in conversation order'
        },
        
        # ====== SHIPMENT INDEXES ======
        {
            'name': 'ix_shipment_user',
            'table': 'shipments',
            'columns': ['user_id'],
            'unique': False,
            'description': 'Shipments by user'
        },
        {
            'name': 'ix_shipment_status',
            'table': 'shipments',
            'columns': ['status', 'created_at'],
            'unique': False,
            'description': 'Shipments by status'
        },
        
        # ====== STATE STORAGE INDEXES ======
        {
            'name': 'ix_state_key',
            'table': 'state_storage',
            'columns': ['key'],
            'unique': True,
            'description': 'Fast state lookup by key'
        },
        {
            'name': 'ix_state_user_type',
            'table': 'state_storage',
            'columns': ['user_id', 'type'],
            'unique': False,
            'description': 'States by user and type'
        },
    ]


def create_indexes(engine, dialect: str = 'postgresql'):
    """
    Create all defined indexes in the database.
    
    Args:
        engine: SQLAlchemy engine
        dialect: Database dialect ('postgresql', 'mysql', 'sqlite')
    """
    from sqlalchemy import text
    
    indexes = get_index_definitions()
    created = 0
    skipped = 0
    
    for idx in indexes:
        try:
            # Build column list
            columns = ', '.join(idx['columns'])
            
            # Build CREATE INDEX statement
            unique = 'UNIQUE' if idx.get('unique') else ''
            
            # Handle partial indexes (PostgreSQL only)
            where_clause = ''
            if idx.get('where') and dialect == 'postgresql':
                where_clause = f"WHERE {idx['where']}"
            
            sql = f"""
                CREATE {unique} INDEX IF NOT EXISTS {idx['name']}
                ON {idx['table']} ({columns})
                {where_clause}
            """
            
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            
            print(f"  ✅ Created index: {idx['name']} on {idx['table']}")
            created += 1
            
        except Exception as e:
            if 'already exists' in str(e).lower():
                print(f"  ⏭️ Index exists: {idx['name']}")
                skipped += 1
            else:
                print(f"  ❌ Error creating {idx['name']}: {e}")
    
    print(f"\n[Indexes] Created: {created}, Skipped: {skipped}")
    return created, skipped


def drop_indexes(engine):
    """Drop all custom indexes."""
    indexes = get_index_definitions()
    
    for idx in indexes:
        try:
            sql = f"DROP INDEX IF EXISTS {idx['name']}"
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            print(f"  🗑️ Dropped index: {idx['name']}")
        except Exception as e:
            print(f"  ⚠️ Error dropping {idx['name']}: {e}")


def analyze_index_usage(engine):
    """
    Analyze index usage (PostgreSQL only).
    
    Returns statistics on how indexes are being used.
    """
    sql = """
        SELECT
            schemaname,
            tablename,
            indexname,
            idx_scan as index_scans,
            idx_tup_read as tuples_read,
            idx_tup_fetch as tuples_fetched
        FROM pg_stat_user_indexes
        ORDER BY idx_scan DESC
    """
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            return [dict(row) for row in result]
    except Exception as e:
        print(f"[analyze_index_usage] Error: {e}")
        return []


def suggest_missing_indexes(engine):
    """
    Suggest potentially missing indexes based on query patterns.
    
    Note: This is a simplified heuristic. For production,
    use proper query analysis tools like pg_stat_statements.
    """
    suggestions = []
    
    # Check for tables without indexes on foreign keys
    # This would require schema introspection
    
    return suggestions


# ============================================================
# CLI SCRIPT
# ============================================================

if __name__ == "__main__":
    import sys
    from app.database import engine
    
    print("=" * 60)
    print("RISKCAST Database Index Manager")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'create':
            print("\n[Creating indexes...]")
            create_indexes(engine)
            
        elif command == 'drop':
            print("\n[Dropping indexes...]")
            drop_indexes(engine)
            
        elif command == 'analyze':
            print("\n[Analyzing index usage...]")
            stats = analyze_index_usage(engine)
            for stat in stats:
                print(f"  {stat['indexname']}: {stat['index_scans']} scans")
                
        elif command == 'list':
            print("\n[Index definitions:]")
            for idx in get_index_definitions():
                print(f"  {idx['name']}: {idx['table']}({', '.join(idx['columns'])})")
                print(f"    └─ {idx['description']}")
        else:
            print(f"Unknown command: {command}")
            print("Usage: python indexes.py [create|drop|analyze|list]")
    else:
        print("\nUsage: python indexes.py [create|drop|analyze|list]")
        print("\nCommands:")
        print("  create  - Create all indexes")
        print("  drop    - Drop all custom indexes")
        print("  analyze - Show index usage statistics (PostgreSQL)")
        print("  list    - List all index definitions")
