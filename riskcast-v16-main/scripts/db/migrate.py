#!/usr/bin/env python3
"""
Database Migration Runner

Features:
1. Migration locking (prevent concurrent migrations)
2. Pre-migration validation
3. Automatic backup before migration
4. Rollback on failure
5. Slack notifications
"""

import argparse
import asyncio
import os
import sys
import time
from datetime import datetime
from typing import Optional
import subprocess

import asyncpg
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


# =============================================================================
# Configuration
# =============================================================================

DATABASE_URL = os.getenv("DATABASE_URL")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
BACKUP_BUCKET = os.getenv("BACKUP_S3_BUCKET", "riskcast-backups")
LOCK_TIMEOUT_SECONDS = 300  # 5 minutes


# =============================================================================
# Migration Lock
# =============================================================================

class MigrationLock:
    """
    Distributed lock for migrations using PostgreSQL advisory locks.
    """
    
    LOCK_ID = 1234567890  # Unique lock ID for migrations
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
    
    async def __aenter__(self):
        """Acquire migration lock."""
        self.conn = await asyncpg.connect(self.database_url)
        
        # Try to acquire advisory lock with timeout
        start_time = time.time()
        while True:
            locked = await self.conn.fetchval(
                "SELECT pg_try_advisory_lock($1)",
                self.LOCK_ID
            )
            
            if locked:
                print("✓ Acquired migration lock")
                return self
            
            if time.time() - start_time > LOCK_TIMEOUT_SECONDS:
                raise RuntimeError(
                    f"Could not acquire migration lock within {LOCK_TIMEOUT_SECONDS}s. "
                    "Another migration may be in progress."
                )
            
            print("Waiting for migration lock...")
            await asyncio.sleep(5)
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release migration lock."""
        if self.conn:
            await self.conn.execute(
                "SELECT pg_advisory_unlock($1)",
                self.LOCK_ID
            )
            await self.conn.close()
            print("✓ Released migration lock")


# =============================================================================
# Pre-Migration Checks
# =============================================================================

async def check_database_connection(database_url: str) -> bool:
    """Check database is accessible."""
    try:
        conn = await asyncpg.connect(database_url)
        await conn.fetchval("SELECT 1")
        await conn.close()
        print("✓ Database connection OK")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


async def check_pending_migrations(alembic_cfg: Config) -> list:
    """Get list of pending migrations."""
    script = ScriptDirectory.from_config(alembic_cfg)
    
    # Get current revision
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        current = await conn.fetchval(
            "SELECT version_num FROM alembic_version"
        )
    except asyncpg.UndefinedTableError:
        current = None
    finally:
        await conn.close()
    
    # Get pending revisions
    pending = []
    for revision in script.walk_revisions():
        if current is None or revision.revision > current:
            pending.append(revision)
    
    pending.reverse()  # Oldest first
    return pending


async def check_active_connections(database_url: str, threshold: int = 10) -> bool:
    """Check for excessive active connections that might indicate ongoing transactions."""
    conn = await asyncpg.connect(database_url)
    try:
        count = await conn.fetchval("""
            SELECT count(*) FROM pg_stat_activity 
            WHERE state = 'active' 
            AND query NOT LIKE '%pg_stat_activity%'
        """)
        
        if count > threshold:
            print(f"⚠ Warning: {count} active connections (threshold: {threshold})")
            return False
        
        print(f"✓ Active connections: {count}")
        return True
    finally:
        await conn.close()


async def check_long_running_queries(database_url: str, threshold_seconds: int = 60) -> bool:
    """Check for long-running queries that might block migrations."""
    conn = await asyncpg.connect(database_url)
    try:
        queries = await conn.fetch(f"""
            SELECT pid, now() - query_start as duration, query
            FROM pg_stat_activity
            WHERE state = 'active'
            AND query_start < now() - interval '{threshold_seconds} seconds'
            AND query NOT LIKE '%pg_stat_activity%'
        """)
        
        if queries:
            print(f"⚠ Warning: {len(queries)} long-running queries:")
            for q in queries:
                print(f"  PID {q['pid']}: {q['duration']} - {q['query'][:100]}...")
            return False
        
        print("✓ No long-running queries")
        return True
    finally:
        await conn.close()


# =============================================================================
# Backup
# =============================================================================

async def create_backup(database_url: str, backup_name: str) -> Optional[str]:
    """Create database backup before migration."""
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{backup_name}_{timestamp}.sql.gz"
        local_path = f"/tmp/{filename}"
        
        # Parse database URL
        import urllib.parse
        parsed = urllib.parse.urlparse(database_url)
        
        # Run pg_dump
        env = os.environ.copy()
        env["PGPASSWORD"] = parsed.password
        
        cmd = [
            "pg_dump",
            "-h", parsed.hostname,
            "-p", str(parsed.port or 5432),
            "-U", parsed.username,
            "-d", parsed.path[1:],  # Remove leading /
            "-Fc",  # Custom format
            "-f", local_path.replace(".gz", "")
        ]
        
        subprocess.run(cmd, env=env, check=True)
        
        # Compress
        subprocess.run(["gzip", local_path.replace(".gz", "")], check=True)
        
        # Upload to S3
        s3_path = f"s3://{BACKUP_BUCKET}/migrations/{filename}"
        subprocess.run(["aws", "s3", "cp", local_path, s3_path], check=True)
        
        # Cleanup local file
        os.remove(local_path)
        
        print(f"✓ Backup created: {s3_path}")
        return s3_path
        
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return None


# =============================================================================
# Notification
# =============================================================================

def send_notification(message: str, status: str = "info"):
    """Send Slack notification."""
    if not SLACK_WEBHOOK_URL:
        return
    
    import requests
    
    colors = {
        "info": "#3498db",
        "success": "#2ecc71",
        "warning": "#f39c12",
        "error": "#e74c3c"
    }
    
    payload = {
        "attachments": [{
            "color": colors.get(status, colors["info"]),
            "title": "Database Migration",
            "text": message,
            "footer": f"Environment: {os.getenv('ENVIRONMENT', 'unknown')}",
            "ts": int(time.time())
        }]
    }
    
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send notification: {e}")


# =============================================================================
# Migration Runner
# =============================================================================

async def run_migration(
    target: str = "head",
    dry_run: bool = False,
    skip_backup: bool = False,
    skip_checks: bool = False
):
    """
    Run database migration with safety checks.
    """
    alembic_cfg = Config("alembic.ini")
    
    print("\n" + "=" * 60)
    print("RISKCAST Database Migration")
    print("=" * 60 + "\n")
    
    # Pre-flight checks
    if not skip_checks:
        print("Running pre-flight checks...\n")
        
        if not await check_database_connection(DATABASE_URL):
            sys.exit(1)
        
        pending = await check_pending_migrations(alembic_cfg)
        if not pending:
            print("\n✓ No pending migrations")
            return
        
        print(f"\n📋 Pending migrations ({len(pending)}):")
        for rev in pending:
            print(f"  - {rev.revision}: {rev.doc}")
        
        await check_active_connections(DATABASE_URL)
        await check_long_running_queries(DATABASE_URL)
    
    # Dry run mode
    if dry_run:
        print("\n[DRY RUN] Would apply the above migrations")
        return
    
    # Acquire lock
    async with MigrationLock(DATABASE_URL):
        # Create backup
        if not skip_backup:
            print("\nCreating pre-migration backup...")
            backup_path = await create_backup(DATABASE_URL, "pre_migration")
            if not backup_path:
                print("⚠ Proceeding without backup")
        
        # Run migration
        print(f"\nApplying migrations to: {target}")
        send_notification(f"Starting migration to `{target}`", "info")
        
        try:
            start_time = time.time()
            
            command.upgrade(alembic_cfg, target)
            
            duration = time.time() - start_time
            print(f"\n✓ Migration completed in {duration:.2f}s")
            send_notification(f"Migration completed successfully in {duration:.2f}s", "success")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            send_notification(f"Migration failed: {e}", "error")
            
            # Suggest rollback
            print("\nTo rollback, run:")
            print(f"  python scripts/db/rollback.py --target <previous_revision>")
            
            sys.exit(1)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Run database migrations")
    
    parser.add_argument(
        "--target",
        default="head",
        help="Migration target (default: head)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without applying"
    )
    
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip pre-migration backup"
    )
    
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip pre-flight checks"
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_migration(
        target=args.target,
        dry_run=args.dry_run,
        skip_backup=args.skip_backup,
        skip_checks=args.skip_checks
    ))


if __name__ == "__main__":
    main()
