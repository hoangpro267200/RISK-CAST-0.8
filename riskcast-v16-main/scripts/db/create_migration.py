#!/usr/bin/env python3
"""
Create new database migration with proper naming and structure.
"""

import argparse
import subprocess
import sys
from datetime import datetime


def create_migration(message: str, autogenerate: bool = True):
    """Create a new migration."""
    
    # Sanitize message
    clean_message = message.lower().replace(" ", "_")
    
    # Build command
    cmd = ["alembic", "revision"]
    
    if autogenerate:
        cmd.append("--autogenerate")
    
    cmd.extend(["-m", message])
    
    print(f"Creating migration: {message}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        
        # Extract filename
        for line in result.stdout.split('\n'):
            if 'Generating' in line or 'Creating' in line:
                print(f"\n✓ Migration created!")
                print(f"\nNext steps:")
                print(f"1. Review the migration file")
                print(f"2. Test locally: alembic upgrade head")
                print(f"3. Test downgrade: alembic downgrade -1")
                print(f"4. Commit the migration file")
                break
        
    except subprocess.CalledProcessError as e:
        print(f"Error creating migration: {e}")
        print(e.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Create new database migration",
        epilog="""
Examples:
  python scripts/db/create_migration.py "add user status column"
  python scripts/db/create_migration.py "rename user name to full_name" --no-autogenerate
        """
    )
    
    parser.add_argument(
        "message",
        help="Migration description"
    )
    
    parser.add_argument(
        "--no-autogenerate",
        action="store_true",
        help="Don't autogenerate from models (create empty migration)"
    )
    
    args = parser.parse_args()
    
    create_migration(args.message, not args.no_autogenerate)


if __name__ == "__main__":
    main()
