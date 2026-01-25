#!/usr/bin/env python3
"""
Create database backup.
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
import urllib.parse


DATABASE_URL = os.getenv("DATABASE_URL")
BACKUP_BUCKET = os.getenv("BACKUP_S3_BUCKET", "riskcast-backups")


def create_backup(name: str = "manual", upload: bool = True):
    """Create database backup."""
    
    print("\n" + "=" * 60)
    print("Database Backup")
    print("=" * 60 + "\n")
    
    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.sql.gz"
    local_path = f"/tmp/{filename}"
    
    # Parse database URL
    parsed = urllib.parse.urlparse(DATABASE_URL)
    
    print(f"Database: {parsed.hostname}:{parsed.port or 5432}/{parsed.path[1:]}")
    print(f"Backup file: {filename}")
    print()
    
    # Run pg_dump
    env = os.environ.copy()
    env["PGPASSWORD"] = parsed.password
    
    cmd = [
        "pg_dump",
        "-h", parsed.hostname,
        "-p", str(parsed.port or 5432),
        "-U", parsed.username,
        "-d", parsed.path[1:],
        "-Fc",  # Custom format (compressed)
        "-f", local_path.replace(".gz", "")
    ]
    
    print("Running pg_dump...")
    try:
        subprocess.run(cmd, env=env, check=True)
        print("✓ Dump created")
    except subprocess.CalledProcessError as e:
        print(f"✗ Dump failed: {e}")
        sys.exit(1)
    
    # Compress
    print("Compressing...")
    try:
        subprocess.run(["gzip", local_path.replace(".gz", "")], check=True)
        print("✓ Compressed")
    except subprocess.CalledProcessError as e:
        print(f"✗ Compression failed: {e}")
        sys.exit(1)
    
    # Get file size
    size_bytes = os.path.getsize(local_path)
    size_mb = size_bytes / (1024 * 1024)
    print(f"Backup size: {size_mb:.2f} MB")
    
    # Upload to S3
    if upload:
        s3_path = f"s3://{BACKUP_BUCKET}/backups/{filename}"
        print(f"\nUploading to: {s3_path}")
        
        try:
            subprocess.run(["aws", "s3", "cp", local_path, s3_path], check=True)
            print("✓ Uploaded to S3")
            
            # Cleanup local file
            os.remove(local_path)
            print("✓ Local file cleaned up")
            
            print(f"\n✓ Backup complete: {s3_path}")
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Upload failed: {e}")
            print(f"Local backup saved at: {local_path}")
            sys.exit(1)
    else:
        print(f"\n✓ Backup saved locally: {local_path}")


def main():
    parser = argparse.ArgumentParser(description="Create database backup")
    
    parser.add_argument(
        "--name",
        default="manual",
        help="Backup name prefix (default: manual)"
    )
    
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Don't upload to S3 (save locally only)"
    )
    
    args = parser.parse_args()
    
    create_backup(args.name, not args.no_upload)


if __name__ == "__main__":
    main()
