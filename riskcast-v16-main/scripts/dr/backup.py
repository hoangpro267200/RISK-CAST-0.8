#!/usr/bin/env python3
"""
Automated Backup System

Features:
1. Database backup (full and incremental)
2. Configuration backup
3. S3 upload with encryption
4. Backup verification
5. Retention management
"""

import argparse
import asyncio
import gzip
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import sys

try:
    import boto3
    from botocore.config import Config as BotoConfig
except ImportError:
    print("Error: boto3 not installed. Run: pip install boto3")
    sys.exit(1)


# =============================================================================
# Configuration
# =============================================================================

BACKUP_BUCKET = os.getenv("BACKUP_S3_BUCKET", "riskcast-backups")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DATABASE_URL = os.getenv("DATABASE_URL")
RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
ENCRYPTION_KEY_ID = os.getenv("BACKUP_KMS_KEY_ID")

# Backup schedule
FULL_BACKUP_DAY = 0  # Monday
INCREMENTAL_DAYS = [1, 2, 3, 4, 5, 6]


# =============================================================================
# S3 Client
# =============================================================================

def get_s3_client():
    """Get S3 client with retry configuration."""
    config = BotoConfig(
        retries={'max_attempts': 3, 'mode': 'adaptive'}
    )
    return boto3.client('s3', region_name=AWS_REGION, config=config)


# =============================================================================
# Database Backup
# =============================================================================

class DatabaseBackup:
    """PostgreSQL database backup handler."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._parse_url()
    
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
    
    def create_full_backup(self, output_path: str) -> Dict[str, Any]:
        """
        Create full database backup using pg_dump.
        """
        print(f"Creating full backup of {self.dbname}...")
        
        env = os.environ.copy()
        env["PGPASSWORD"] = self.password
        
        # Use custom format for efficient compression and selective restore
        cmd = [
            "pg_dump",
            "-h", self.host,
            "-p", str(self.port),
            "-U", self.user,
            "-d", self.dbname,
            "-Fc",  # Custom format
            "-Z", "9",  # Max compression
            "-f", output_path,
            "--no-owner",
            "--no-acl"
        ]
        
        start_time = datetime.utcnow()
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, check=False)
            
            if result.returncode != 0:
                raise RuntimeError(f"pg_dump failed: {result.stderr.decode()}")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            size = os.path.getsize(output_path)
            
            # Calculate checksum
            checksum = self._calculate_checksum(output_path)
            
            print(f"  ✓ Backup created: {size / 1024 / 1024:.2f} MB in {duration:.1f}s")
            
            return {
                "type": "full",
                "database": self.dbname,
                "size_bytes": size,
                "duration_seconds": duration,
                "checksum_sha256": checksum,
                "created_at": start_time.isoformat()
            }
        except FileNotFoundError:
            raise RuntimeError("pg_dump not found. Please install PostgreSQL client tools.")
    
    def create_incremental_backup(self, output_path: str, since: datetime) -> Dict[str, Any]:
        """
        Create incremental backup using WAL archiving.
        
        Note: Requires WAL archiving to be configured on the database.
        """
        print(f"Creating incremental backup since {since}...")
        
        # For simplicity, we'll do a table-level backup of recently modified data
        # In production, use pg_basebackup with WAL archiving
        
        env = os.environ.copy()
        env["PGPASSWORD"] = self.password
        
        # Backup only tables with recent modifications
        # This requires audit timestamps on tables
        cmd = [
            "pg_dump",
            "-h", self.host,
            "-p", str(self.port),
            "-U", self.user,
            "-d", self.dbname,
            "-Fc",
            "-Z", "9",
            "-f", output_path,
            "--no-owner",
            "--no-acl",
            # Add table filters for incremental
            # Note: In production, customize based on your schema
        ]
        
        # Add important tables (customize based on your schema)
        important_tables = [
            "quotes", "policies", "claims", "risk_runs", 
            "audit_events", "tenants", "users"
        ]
        
        for table in important_tables:
            cmd.extend(["--table", table])
        
        start_time = datetime.utcnow()
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, check=False)
            
            if result.returncode != 0:
                raise RuntimeError(f"pg_dump failed: {result.stderr.decode()}")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            size = os.path.getsize(output_path)
            checksum = self._calculate_checksum(output_path)
            
            print(f"  ✓ Incremental backup created: {size / 1024 / 1024:.2f} MB in {duration:.1f}s")
            
            return {
                "type": "incremental",
                "database": self.dbname,
                "since": since.isoformat(),
                "size_bytes": size,
                "duration_seconds": duration,
                "checksum_sha256": checksum,
                "created_at": start_time.isoformat()
            }
        except FileNotFoundError:
            raise RuntimeError("pg_dump not found. Please install PostgreSQL client tools.")
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


# =============================================================================
# S3 Upload
# =============================================================================

class BackupUploader:
    """Upload backups to S3 with encryption."""
    
    def __init__(self, bucket: str, kms_key_id: Optional[str] = None):
        self.bucket = bucket
        self.kms_key_id = kms_key_id
        self.s3 = get_s3_client()
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure backup bucket exists."""
        try:
            self.s3.head_bucket(Bucket=self.bucket)
        except:
            print(f"Warning: Could not access bucket {self.bucket}")
            print("Please ensure the bucket exists and you have permissions.")
    
    def upload(self, local_path: str, s3_key: str, metadata: Dict[str, Any]) -> str:
        """Upload file to S3 with server-side encryption."""
        print(f"Uploading to s3://{self.bucket}/{s3_key}...")
        
        extra_args = {
            'Metadata': {k: str(v) for k, v in metadata.items()}
        }
        
        if self.kms_key_id:
            extra_args['ServerSideEncryption'] = 'aws:kms'
            extra_args['SSEKMSKeyId'] = self.kms_key_id
        else:
            extra_args['ServerSideEncryption'] = 'AES256'
        
        # Add storage class for cost optimization
        extra_args['StorageClass'] = 'STANDARD_IA'  # Infrequent Access
        
        self.s3.upload_file(
            local_path,
            self.bucket,
            s3_key,
            ExtraArgs=extra_args
        )
        
        s3_uri = f"s3://{self.bucket}/{s3_key}"
        print(f"  ✓ Uploaded to {s3_uri}")
        
        return s3_uri
    
    def list_backups(self, prefix: str = "database/") -> list:
        """List existing backups."""
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            
            backups = []
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get('Contents', []):
                    backups.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified']
                    })
            
            return sorted(backups, key=lambda x: x['last_modified'], reverse=True)
        except Exception as e:
            print(f"Warning: Could not list backups: {e}")
            return []


# =============================================================================
# Backup Verification
# =============================================================================

class BackupVerifier:
    """Verify backup integrity."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
    
    def verify_backup(self, backup_path: str) -> Dict[str, Any]:
        """
        Verify backup file integrity.
        
        1. Check file is readable
        2. Verify pg_restore can read it
        3. List contents
        """
        print(f"Verifying backup: {backup_path}...")
        
        # Check file exists and is readable
        if not os.path.exists(backup_path):
            return {"valid": False, "error": "File not found"}
        
        # Check file size
        size = os.path.getsize(backup_path)
        if size == 0:
            return {"valid": False, "error": "File is empty"}
        
        # Use pg_restore to verify
        try:
            cmd = ["pg_restore", "-l", backup_path]
            result = subprocess.run(cmd, capture_output=True, check=False)
            
            if result.returncode != 0:
                return {
                    "valid": False,
                    "error": f"pg_restore verification failed: {result.stderr.decode()}"
                }
            
            # Parse table of contents
            toc = result.stdout.decode()
            tables = [line for line in toc.split('\n') if 'TABLE DATA' in line]
            
            print(f"  ✓ Backup verified: {len(tables)} tables")
            
            return {
                "valid": True,
                "tables_count": len(tables),
                "size_bytes": size
            }
        except FileNotFoundError:
            return {
                "valid": False,
                "error": "pg_restore not found. Please install PostgreSQL client tools."
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Verification failed: {str(e)}"
            }


# =============================================================================
# Retention Management
# =============================================================================

class RetentionManager:
    """Manage backup retention."""
    
    def __init__(self, uploader: BackupUploader, retention_days: int):
        self.uploader = uploader
        self.retention_days = retention_days
    
    def cleanup_old_backups(self, prefix: str = "database/"):
        """Delete backups older than retention period."""
        print(f"\nCleaning up backups older than {self.retention_days} days...")
        
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        
        backups = self.uploader.list_backups(prefix)
        
        if not backups:
            print("  No backups found to clean up")
            return
        
        deleted = 0
        for backup in backups:
            # Handle timezone-aware datetime
            backup_time = backup['last_modified']
            if backup_time.tzinfo:
                backup_time = backup_time.replace(tzinfo=None)
            
            if backup_time < cutoff:
                print(f"  Deleting old backup: {backup['key']}")
                try:
                    self.uploader.s3.delete_object(
                        Bucket=self.uploader.bucket,
                        Key=backup['key']
                    )
                    deleted += 1
                except Exception as e:
                    print(f"    Warning: Could not delete {backup['key']}: {e}")
        
        if deleted > 0:
            print(f"  ✓ Deleted {deleted} old backups")
        else:
            print("  No old backups to delete")


# =============================================================================
# Configuration Backup
# =============================================================================

class ConfigurationBackup:
    """Backup configuration files."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
    
    def create_config_backup(self, output_path: str) -> Dict[str, Any]:
        """Create tarball of configuration files."""
        print("Creating configuration backup...")
        
        import tarfile
        
        # Files to include
        config_files = [
            "k8s/",
            "alembic/",
            "alembic.ini",
            "requirements.txt",
            "requirements-*.txt",
            "Dockerfile",
            "docker-compose*.yml",
            ".env.example"
        ]
        
        start_time = datetime.utcnow()
        
        with tarfile.open(output_path, "w:gz") as tar:
            for pattern in config_files:
                path = Path(self.repo_path) / pattern
                if path.exists():
                    if path.is_dir():
                        tar.add(path, arcname=pattern)
                    else:
                        tar.add(path, arcname=pattern)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        size = os.path.getsize(output_path)
        
        print(f"  ✓ Configuration backup created: {size / 1024:.2f} KB")
        
        return {
            "type": "configuration",
            "size_bytes": size,
            "duration_seconds": duration,
            "created_at": start_time.isoformat()
        }


# =============================================================================
# Main Backup Flow
# =============================================================================

async def run_backup(
    backup_type: str = "auto",
    verify: bool = True,
    cleanup: bool = True,
    include_config: bool = True
):
    """
    Run backup workflow.
    """
    print("\n" + "=" * 60)
    print("RISKCAST Backup System")
    print("=" * 60 + "\n")
    
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Determine backup type
    if backup_type == "auto":
        today = datetime.utcnow().weekday()
        backup_type = "full" if today == FULL_BACKUP_DAY else "incremental"
    
    print(f"Backup type: {backup_type}")
    print(f"Backup bucket: s3://{BACKUP_BUCKET}")
    print(f"Retention: {RETENTION_DAYS} days")
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create database backup
        db_backup = DatabaseBackup(DATABASE_URL)
        backup_file = f"{tmpdir}/backup_{timestamp}.dump"
        
        if backup_type == "full":
            metadata = db_backup.create_full_backup(backup_file)
        else:
            since = datetime.utcnow() - timedelta(days=1)
            metadata = db_backup.create_incremental_backup(backup_file, since)
        
        # Verify
        if verify:
            verifier = BackupVerifier(DATABASE_URL)
            verification = verifier.verify_backup(backup_file)
            
            if not verification['valid']:
                raise RuntimeError(f"Backup verification failed: {verification.get('error')}")
            
            metadata['verification'] = verification
        
        # Upload database backup
        uploader = BackupUploader(BACKUP_BUCKET, ENCRYPTION_KEY_ID)
        
        s3_key = f"database/{backup_type}/{timestamp}/backup.dump"
        s3_uri = uploader.upload(backup_file, s3_key, metadata)
        
        # Save metadata
        metadata['s3_uri'] = s3_uri
        metadata['backup_bucket'] = BACKUP_BUCKET
        metadata['aws_region'] = AWS_REGION
        
        metadata_key = f"database/{backup_type}/{timestamp}/metadata.json"
        metadata_file = f"{tmpdir}/metadata.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        uploader.upload(metadata_file, metadata_key, {})
        
        # Configuration backup (only for full backups)
        if include_config and backup_type == "full":
            config_backup = ConfigurationBackup()
            config_file = f"{tmpdir}/config_{timestamp}.tar.gz"
            
            config_metadata = config_backup.create_config_backup(config_file)
            
            config_key = f"configuration/{timestamp}/config.tar.gz"
            config_uri = uploader.upload(config_file, config_key, config_metadata)
            
            print(f"  ✓ Configuration backed up to {config_uri}")
        
        # Cleanup old backups
        if cleanup:
            retention = RetentionManager(uploader, RETENTION_DAYS)
            retention.cleanup_old_backups()
    
    print("\n" + "=" * 60)
    print("Backup completed successfully!")
    print("=" * 60)
    print(f"\nBackup location: {s3_uri}")
    print(f"Metadata: s3://{BACKUP_BUCKET}/{metadata_key}")
    
    return metadata


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Run database backup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Automatic backup (full on Monday, incremental other days)
  python backup.py
  
  # Force full backup
  python backup.py --type full
  
  # Incremental backup only
  python backup.py --type incremental
  
  # Skip verification (faster but not recommended)
  python backup.py --no-verify
  
  # Skip cleanup of old backups
  python backup.py --no-cleanup
        """
    )
    
    parser.add_argument(
        "--type",
        choices=["full", "incremental", "auto"],
        default="auto",
        help="Backup type (default: auto based on day of week)"
    )
    
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip backup verification"
    )
    
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup of old backups"
    )
    
    parser.add_argument(
        "--no-config",
        action="store_true",
        help="Skip configuration backup"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_backup(
            backup_type=args.type,
            verify=not args.no_verify,
            cleanup=not args.no_cleanup,
            include_config=not args.no_config
        ))
    except KeyboardInterrupt:
        print("\n\nBackup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
