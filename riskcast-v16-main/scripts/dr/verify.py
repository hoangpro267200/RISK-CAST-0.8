#!/usr/bin/env python3
"""
Database Verification Script

Verify database integrity after backup/restore operations.
"""

import argparse
import asyncio
import sys
from datetime import datetime
from typing import Dict, Any

try:
    import asyncpg
except ImportError:
    print("Error: asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)


class DatabaseVerifier:
    """Verify database integrity."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    async def verify_connection(self) -> Dict[str, Any]:
        """Verify database connection."""
        print("Testing database connection...")
        
        try:
            conn = await asyncpg.connect(self.database_url)
            
            # Get version
            version = await conn.fetchval("SELECT version()")
            
            # Get database size
            size = await conn.fetchval("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)
            
            await conn.close()
            
            print(f"  ✓ Connection successful")
            print(f"    PostgreSQL: {version.split(',')[0]}")
            print(f"    Database size: {size}")
            
            return {
                "status": "ok",
                "version": version,
                "size": size
            }
        except Exception as e:
            print(f"  ✗ Connection failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def verify_tables(self) -> Dict[str, Any]:
        """Verify table structure and counts."""
        print("\nVerifying tables...")
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Get all tables
            tables = await conn.fetch("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            
            print(f"  Found {len(tables)} tables")
            
            # Get row counts
            counts = {}
            total_rows = 0
            
            for table in tables:
                try:
                    count = await conn.fetchval(
                        f"SELECT COUNT(*) FROM {table['tablename']}"
                    )
                    counts[table['tablename']] = count
                    total_rows += count
                except Exception as e:
                    counts[table['tablename']] = f"Error: {e}"
            
            # Display top tables
            sorted_counts = sorted(
                [(k, v) for k, v in counts.items() if isinstance(v, int)],
                key=lambda x: x[1],
                reverse=True
            )
            
            print("\n  Top tables by row count:")
            for table, count in sorted_counts[:10]:
                print(f"    {table}: {count:,} rows")
            
            if len(sorted_counts) > 10:
                print(f"    ... and {len(sorted_counts) - 10} more tables")
            
            print(f"\n  ✓ Total rows: {total_rows:,}")
            
            return {
                "status": "ok",
                "tables_count": len(tables),
                "total_rows": total_rows,
                "row_counts": counts
            }
        finally:
            await conn.close()
    
    async def verify_indexes(self) -> Dict[str, Any]:
        """Verify indexes."""
        print("\nVerifying indexes...")
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            indexes = await conn.fetch("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            
            print(f"  ✓ Found {len(indexes)} indexes")
            
            return {
                "status": "ok",
                "indexes_count": len(indexes)
            }
        finally:
            await conn.close()
    
    async def verify_constraints(self) -> Dict[str, Any]:
        """Verify foreign key constraints."""
        print("\nVerifying constraints...")
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            constraints = await conn.fetch("""
                SELECT
                    conname,
                    contype,
                    conrelid::regclass as table_name
                FROM pg_constraint
                WHERE connamespace = 'public'::regnamespace
                ORDER BY contype, conname
            """)
            
            constraint_types = {}
            for c in constraints:
                ctype = c['contype']
                constraint_types[ctype] = constraint_types.get(ctype, 0) + 1
            
            type_names = {
                'p': 'Primary keys',
                'f': 'Foreign keys',
                'c': 'Check constraints',
                'u': 'Unique constraints'
            }
            
            for ctype, count in constraint_types.items():
                name = type_names.get(ctype, f'Type {ctype}')
                print(f"    {name}: {count}")
            
            print(f"  ✓ Found {len(constraints)} constraints")
            
            return {
                "status": "ok",
                "constraints_count": len(constraints),
                "by_type": constraint_types
            }
        finally:
            await conn.close()
    
    async def verify_sequences(self) -> Dict[str, Any]:
        """Verify sequences."""
        print("\nVerifying sequences...")
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            sequences = await conn.fetch("""
                SELECT
                    sequence_name,
                    last_value
                FROM information_schema.sequences
                WHERE sequence_schema = 'public'
            """)
            
            print(f"  ✓ Found {len(sequences)} sequences")
            
            return {
                "status": "ok",
                "sequences_count": len(sequences)
            }
        finally:
            await conn.close()
    
    async def verify_data_integrity(self) -> Dict[str, Any]:
        """Verify data integrity with sample queries."""
        print("\nVerifying data integrity...")
        
        conn = await asyncpg.connect(self.database_url)
        
        try:
            checks = []
            
            # Check for orphaned records (customize for your schema)
            # Example: quotes without policies
            try:
                orphaned = await conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM quotes q 
                    LEFT JOIN policies p ON q.policy_id = p.id 
                    WHERE q.policy_id IS NOT NULL AND p.id IS NULL
                """)
                
                if orphaned == 0:
                    print("  ✓ No orphaned quotes")
                    checks.append({"check": "orphaned_quotes", "status": "ok"})
                else:
                    print(f"  ⚠ Found {orphaned} orphaned quotes")
                    checks.append({"check": "orphaned_quotes", "status": "warning", "count": orphaned})
            except Exception as e:
                print(f"  ℹ Could not check orphaned quotes: {e}")
            
            # Check for duplicate primary keys (shouldn't happen)
            try:
                tables_with_id = await conn.fetch("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename NOT LIKE 'alembic%'
                """)
                
                for table in tables_with_id:
                    try:
                        duplicates = await conn.fetchval(f"""
                            SELECT COUNT(*) 
                            FROM (
                                SELECT id, COUNT(*) as cnt 
                                FROM {table['tablename']} 
                                GROUP BY id 
                                HAVING COUNT(*) > 1
                            ) duplicates
                        """)
                        
                        if duplicates == 0:
                            checks.append({"check": f"{table['tablename']}_duplicates", "status": "ok"})
                        else:
                            print(f"  ⚠ Found {duplicates} duplicate IDs in {table['tablename']}")
                            checks.append({
                                "check": f"{table['tablename']}_duplicates",
                                "status": "warning",
                                "count": duplicates
                            })
                    except:
                        pass  # Skip tables without id column
            except Exception as e:
                print(f"  ℹ Could not check duplicates: {e}")
            
            print(f"  ✓ Completed {len(checks)} integrity checks")
            
            return {
                "status": "ok",
                "checks": checks
            }
        finally:
            await conn.close()
    
    async def run_full_verification(self) -> Dict[str, Any]:
        """Run complete verification suite."""
        print("=" * 60)
        print("DATABASE VERIFICATION")
        print("=" * 60)
        
        results = {}
        
        # Connection test
        results['connection'] = await self.verify_connection()
        if results['connection']['status'] != 'ok':
            print("\n✗ Cannot connect to database. Stopping verification.")
            return results
        
        # Tables
        results['tables'] = await self.verify_tables()
        
        # Indexes
        results['indexes'] = await self.verify_indexes()
        
        # Constraints
        results['constraints'] = await self.verify_constraints()
        
        # Sequences
        results['sequences'] = await self.verify_sequences()
        
        # Data integrity
        results['data_integrity'] = await self.verify_data_integrity()
        
        # Summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        
        all_ok = all(
            r.get('status') == 'ok' 
            for r in results.values() 
            if isinstance(r, dict)
        )
        
        if all_ok:
            print("✓ All checks passed")
            return results
        else:
            print("⚠ Some checks failed or have warnings")
            return results


async def main():
    parser = argparse.ArgumentParser(
        description="Verify database integrity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full verification
  python verify.py
  
  # Verify specific database
  export DATABASE_URL="postgresql://..."
  python verify.py
        """
    )
    
    parser.add_argument(
        "--database",
        help="Database URL (default: from DATABASE_URL env)"
    )
    
    args = parser.parse_args()
    
    import os
    database_url = args.database or os.getenv("DATABASE_URL")
    
    if not database_url:
        print("Error: No database URL provided")
        print("Set DATABASE_URL environment variable or use --database")
        sys.exit(1)
    
    try:
        verifier = DatabaseVerifier(database_url)
        results = await verifier.run_full_verification()
        
        # Exit with error if verification failed
        all_ok = all(
            r.get('status') == 'ok' 
            for r in results.values() 
            if isinstance(r, dict)
        )
        
        sys.exit(0 if all_ok else 1)
    
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
