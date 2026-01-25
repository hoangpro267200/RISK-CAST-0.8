#!/usr/bin/env python3
"""
Check migration status and health.
"""

import asyncio
import sys
import os

import asyncpg
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


DATABASE_URL = os.getenv("DATABASE_URL")


async def get_current_revision():
    """Get current database revision."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        version = await conn.fetchval("SELECT version_num FROM alembic_version")
        return version
    except asyncpg.UndefinedTableError:
        return None
    finally:
        await conn.close()


async def check_migration_status():
    """Check current migration status."""
    print("\n" + "=" * 60)
    print("Migration Status Check")
    print("=" * 60 + "\n")
    
    # Get current revision
    current = await get_current_revision()
    
    if current is None:
        print("⚠ Database not initialized (no alembic_version table)")
        print("\nTo initialize:")
        print("  alembic upgrade head")
        return
    
    print(f"Current revision: {current}")
    
    # Get head revision
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    head = script.get_current_head()
    
    print(f"Head revision:    {head}")
    
    # Check if up to date
    if current == head:
        print("\n✓ Database is up to date")
    else:
        print("\n⚠ Database is NOT up to date")
        
        # Show pending migrations
        pending = []
        for revision in script.walk_revisions():
            if revision.revision == current:
                break
            pending.append(revision)
        
        pending.reverse()
        
        print(f"\nPending migrations ({len(pending)}):")
        for rev in pending:
            print(f"  - {rev.revision}: {rev.doc}")
        
        print("\nTo apply:")
        print("  python scripts/db/migrate.py")
    
    # Show recent history
    print("\n" + "-" * 60)
    print("Recent Migration History")
    print("-" * 60 + "\n")
    
    count = 0
    for revision in script.walk_revisions():
        is_current = revision.revision == current
        marker = "→ " if is_current else "  "
        print(f"{marker}{revision.revision}: {rev.doc}")
        
        count += 1
        if count >= 10:
            break


async def check_migration_conflicts():
    """Check for migration conflicts."""
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    
    heads = script.get_heads()
    
    if len(heads) > 1:
        print("\n⚠ Multiple heads detected (merge needed):")
        for head in heads:
            print(f"  - {head}")
        print("\nTo merge:")
        print("  alembic merge -m 'merge branches' " + " ".join(heads))
        return False
    
    return True


async def main():
    """Main function."""
    try:
        await check_migration_status()
        
        if not await check_migration_conflicts():
            sys.exit(1)
        
        print("\n✓ All checks passed")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
