#!/usr/bin/env python3
"""
Database Restore Script

Restore from S3 backup with verification.
"""

import argparse
import asyncio
import json
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any
import sys

try:
    import boto3
except ImportError:
    print("Error: boto3 not installed. Run: pip install boto3")
    sys.exit(1)


# =============================================================================
# Configuration
# =============================================================================

DATABASE_URL = os.getenv("DATABASE_URL")
BACKUP_BUCKET = os.getenv("BACKUP_S3_BUCKET", "riskcast-backups")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


# =============================================================================
# Database Restore
# =============================================================================

class DatabaseRestore:
    """Restore database from backup."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._parse_url()
        self.s3 = boto3.client('s3', region_name=AWS_REGION)
    
    def _parse_url(self):
        """Parse database URL."""
        import urllib.parse
        
        # Handle asyncpg URLs
        url = self.database_url.replace('postgresql+asyncpg://', 'postgresql://')
        
        parsed = urllib.parse.urlparse(url)
        self.host = parsed.hostname
        self.port = parsed.port or 5432
        self.user = parsed.username
        self.password = parsed.password
        self.dbname = parsed.path[1:] if parsed.path else 'postgres'
    
    def list_available_backups(self, limit: int = 10) -> list:
        """List available backups from S3."""
        print(f"Listing backups from s3://{BACKUP_BUCKET}...")
        
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            
            backups = []
            for page in paginator.paginate(Bucket=BACKUP_BUCKET, Prefix="database/"):
                for obj in page.get('Contents', []):
                    if obj['Key'].endswith('metadata.json'):
                        backups.append(obj)
            
            # Sort by date, newest first
            backups.sort(key=lambda x: x['LastModified'], reverse=True)
            
            # Load metadata for each
            result = []
            for backup in backups[:limit]:
                try:
                    response = self.s3.get_object(Bucket=BACKUP_BUCKET, Key=backup['Key'])
                    metadata = json.loads(response['Body'].read().decode())
                    metadata['s3_key'] = backup['Key'].replace('metadata.json', 'backup.dump')
                    metadata['metadata_key'] = backup['Key']
                    result.append(metadata)
                except Exception as e:
                    print(f"Warning: Could not read {backup['Key']}: {e}")
            
            return result
        except Exception as e:
            print(f"Error listing backups: {e}")
            return []
    
    def download_backup(self, s3_key: str, local_path: str):
        """Download backup from S3."""
        print(f"Downloading {s3_key}...")
        
        try:
            # Get file size for progress
            response = self.s3.head_object(Bucket=BACKUP_BUCKET, Key=s3_key)
            size = response['ContentLength']
            
            print(f"  Size: {size / 1024 / 1024:.2f} MB")
            
            self.s3.download_file(BACKUP_BUCKET, s3_key, local_path)
            print(f"  ✓ Downloaded to {local_path}")
        except Exception as e:
            raise RuntimeError(f"Download failed: {e}")
    
    def restore(
        self,
        backup_path: str,
        target_db: Optional[str] = None,
        drop_existing: bool = False,
        parallel_jobs: int = 4
    ):
        """
        Restore database from backup file.
        """
        target = target_db or self.dbname
        
        print(f"\nRestoring to database: {target}")
        
        env = os.environ.copy()
        env["PGPASSWORD"] = self.password
        
        # Optionally drop and recreate database
        if drop_existing:
            print("  ⚠ Dropping existing database...")
            
            try:
                # Drop database
                subprocess.run([
                    "psql",
                    "-h", self.host,
                    "-p", str(self.port),
                    "-U", self.user,
                    "-d", "postgres",
                    "-c", f"DROP DATABASE IF EXISTS {target}"
                ], env=env, check=True, capture_output=True)
                
                # Create database
                subprocess.run([
                    "psql",
                    "-h", self.host,
                    "-p", str(self.port),
                    "-U", self.user,
                    "-d", "postgres",
                    "-c", f"CREATE DATABASE {target}"
                ], env=env, check=True, capture_output=True)
                
                print("  ✓ Database recreated")
            except subprocess.CalledProcessError as e:
                print(f"  Warning: Database drop/create had issues: {e.stderr.decode()}")
        
        # Restore using pg_restore
        print(f"  Running pg_restore with {parallel_jobs} parallel jobs...")
        
        cmd = [
            "pg_restore",
            "-h", self.host,
            "-p", str(self.port),
            "-U", self.user,
            "-d", target,
            "--no-owner",
            "--no-acl",
            "-j", str(parallel_jobs),  # Parallel jobs
            "--verbose",
            backup_path
        ]
        
        start_time = datetime.utcnow()
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, check=False)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # pg_restore may return non-zero even on success due to warnings
            if result.returncode != 0:
                stderr = result.stderr.decode()
                # Check if it's just warnings
                if "error" in stderr.lower() and "already exists" not in stderr.lower():
                    print(f"  ⚠ Warnings/Errors:\n{stderr[:500]}")
                else:
                    print(f"  ⚠ Warnings (may be ignorable):\n{stderr[:200]}")
            
            print(f"  ✓ Restore completed in {duration:.1f}s")
        except FileNotFoundError:
            raise RuntimeError("pg_restore not found. Please install PostgreSQL client tools.")
        except Exception as e:
            raise RuntimeError(f"Restore failed: {e}")
    
    def verify_restore(self, target_db: Optional[str] = None) -> Dict[str, Any]:
        """Verify restored database."""
        target = target_db or self.dbname
        
        print(f"\nVerifying restore of {target}...")
        
        try:
            import asyncpg
        except ImportError:
            print("  ⚠ asyncpg not installed, skipping detailed verification")
            return {"verified": False, "reason": "asyncpg not available"}
        
        async def check():
            try:
                conn = await asyncpg.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=target
                )
                
                try:
                    # Check table counts
                    tables = await conn.fetch("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY tablename
                    """)
                    
                    counts = {}
                    for table in tables:
                        try:
                            count = await conn.fetchval(
                                f"SELECT COUNT(*) FROM {table['tablename']}"
                            )
                            counts[table['tablename']] = count
                        except Exception as e:
                            counts[table['tablename']] = f"Error: {e}"
                    
                    # Check database size
                    db_size = await conn.fetchval("""
                        SELECT pg_size_pretty(pg_database_size($1))
                    """, target)
                    
                    return {
                        "verified": True,
                        "tables_count": len(tables),
                        "record_counts": counts,
                        "database_size": db_size
                    }
                finally:
                    await conn.close()
            except Exception as e:
                return {
                    "verified": False,
                    "error": str(e)
                }
        
        result = asyncio.run(check())
        
        if result.get("verified"):
            print(f"  ✓ Verification complete")
            print(f"    Tables: {result['tables_count']}")
            print(f"    Database size: {result.get('database_size', 'unknown')}")
        else:
            print(f"  ⚠ Verification failed: {result.get('error', 'unknown')}")
        
        return result


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Restore database from backup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available backups
  python restore.py --list
  
  # Restore from specific backup
  python restore.py --backup-key database/full/20240115_030000/backup.dump
  
  # Restore to different database
  python restore.py --backup-key <key> --target-db riskcast_restored
  
  # Drop and recreate database before restore
  python restore.py --backup-key <key> --drop-existing --yes
        """
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups"
    )
    
    parser.add_argument(
        "--backup-key",
        help="S3 key of backup to restore"
    )
    
    parser.add_argument(
        "--target-db",
        help="Target database name (default: from DATABASE_URL)"
    )
    
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop and recreate target database"
    )
    
    parser.add_argument(
        "--parallel-jobs",
        type=int,
        default=4,
        help="Number of parallel restore jobs (default: 4)"
    )
    
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompts"
    )
    
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip verification after restore"
    )
    
    args = parser.parse_args()
    
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        restore = DatabaseRestore(DATABASE_URL)
        
        if args.list:
            backups = restore.list_available_backups(limit=20)
            
            if not backups:
                print("No backups found")
                return
            
            print("\nAvailable Backups:")
            print("-" * 100)
            print(f"{'#':<4} {'Created At':<20} {'Type':<12} {'Size':<12} {'Tables':<8} {'S3 Key'}")
            print("-" * 100)
            
            for i, b in enumerate(backups):
                size_mb = b.get('size_bytes', 0) / 1024 / 1024
                tables = b.get('verification', {}).get('tables_count', 'N/A')
                created = b.get('created_at', 'Unknown')[:19]
                
                print(f"{i+1:<4} {created:<20} {b.get('type', 'unknown'):<12} {size_mb:>8.1f} MB {str(tables):<8} {b['s3_key']}")
            
            return
        
        if not args.backup_key:
            # Interactive selection
            backups = restore.list_available_backups(limit=10)
            
            if not backups:
                print("No backups found")
                return
            
            print("\nAvailable Backups:")
            print("-" * 80)
            for i, b in enumerate(backups):
                size_mb = b.get('size_bytes', 0) / 1024 / 1024
                created = b.get('created_at', 'Unknown')[:19]
                backup_type = b.get('type', 'unknown')
                
                print(f"{i+1}. {created} | {backup_type:<12} | {size_mb:>8.1f} MB")
            print("-" * 80)
            
            try:
                choice = int(input("\nSelect backup number (or 0 to cancel): "))
                if choice == 0:
                    print("Cancelled")
                    return
                backup_key = backups[choice - 1]['s3_key']
            except (ValueError, IndexError, KeyboardInterrupt):
                print("\nInvalid selection or cancelled")
                return
        else:
            backup_key = args.backup_key
        
        # Confirm
        if not args.yes:
            print(f"\n{'='*60}")
            print("RESTORE CONFIRMATION")
            print(f"{'='*60}")
            print(f"Source: {backup_key}")
            print(f"Target database: {args.target_db or restore.dbname}")
            print(f"Target host: {restore.host}:{restore.port}")
            
            if args.drop_existing:
                print("\n⚠ WARNING: This will DROP the existing database!")
                print("⚠ All current data will be PERMANENTLY LOST!")
            
            print(f"{'='*60}\n")
            
            confirm = input("Proceed with restore? Type 'yes' to continue: ")
            if confirm.lower() != 'yes':
                print("Cancelled")
                return
        
        # Download and restore
        print("\nStarting restore process...\n")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = f"{tmpdir}/backup.dump"
            
            # Download
            restore.download_backup(backup_key, local_path)
            
            # Restore
            restore.restore(
                local_path,
                args.target_db,
                args.drop_existing,
                args.parallel_jobs
            )
            
            # Verify
            if not args.no_verify:
                verification = restore.verify_restore(args.target_db)
                
                if verification.get('verified'):
                    print("\n" + "=" * 60)
                    print("RESTORE SUMMARY")
                    print("=" * 60)
                    print(f"Tables restored: {verification['tables_count']}")
                    print(f"Database size: {verification.get('database_size', 'unknown')}")
                    
                    # Show sample counts
                    counts = verification.get('record_counts', {})
                    if counts:
                        print("\nSample table counts:")
                        for table, count in list(counts.items())[:10]:
                            print(f"  {table}: {count:,}" if isinstance(count, int) else f"  {table}: {count}")
                        
                        if len(counts) > 10:
                            print(f"  ... and {len(counts) - 10} more tables")
        
        print("\n" + "=" * 60)
        print("✓ Restore completed successfully!")
        print("=" * 60)
    
    except KeyboardInterrupt:
        print("\n\nRestore cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
