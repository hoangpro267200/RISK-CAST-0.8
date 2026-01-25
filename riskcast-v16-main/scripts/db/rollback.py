#!/usr/bin/env python3
"""
Database Rollback Script

Safe rollback with verification.
"""

import argparse
import asyncio
import os
import sys

import asyncpg
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


DATABASE_URL = os.getenv("DATABASE_URL")


async def get_current_revision() -> str:
    """Get current database revision."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        return await conn.fetchval("SELECT version_num FROM alembic_version")
    finally:
        await conn.close()


async def get_revision_history(alembic_cfg: Config, limit: int = 10) -> list:
    """Get recent revision history."""
    script = ScriptDirectory.from_config(alembic_cfg)
    current = await get_current_revision()
    
    history = []
    for revision in script.walk_revisions():
        is_current = revision.revision == current
        history.append({
            "revision": revision.revision,
            "description": revision.doc,
            "is_current": is_current
        })
        if len(history) >= limit:
            break
    
    return history


async def rollback(target: str, confirm: bool = False):
    """
    Rollback to target revision.
    """
    alembic_cfg = Config("alembic.ini")
    
    # Show current state
    current = await get_current_revision()
    print(f"Current revision: {current}")
    print(f"Target revision:  {target}")
    
    # Show what will be rolled back
    script = ScriptDirectory.from_config(alembic_cfg)
    
    to_rollback = []
    for revision in script.walk_revisions():
        if revision.revision == target:
            break
        if revision.revision <= current:
            to_rollback.append(revision)
    
    if not to_rollback:
        print("Nothing to rollback")
        return
    
    print(f"\nMigrations to rollback ({len(to_rollback)}):")
    for rev in to_rollback:
        print(f"  - {rev.revision}: {rev.doc}")
    
    # Confirm
    if not confirm:
        response = input("\nProceed with rollback? [y/N]: ")
        if response.lower() != 'y':
            print("Rollback cancelled")
            return
    
    # Execute rollback
    print(f"\nRolling back to {target}...")
    
    try:
        command.downgrade(alembic_cfg, target)
        
        new_current = await get_current_revision()
        print(f"\n✓ Rollback complete. Current revision: {new_current}")
        
    except Exception as e:
        print(f"\n✗ Rollback failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Rollback database migrations")
    
    parser.add_argument(
        "--target", "-t",
        required=True,
        help="Target revision to rollback to"
    )
    
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation"
    )
    
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show revision history"
    )
    
    args = parser.parse_args()
    
    if args.history:
        alembic_cfg = Config("alembic.ini")
        history = asyncio.run(get_revision_history(alembic_cfg))
        print("\nRevision History:")
        for rev in history:
            marker = "→ " if rev["is_current"] else "  "
            print(f"{marker}{rev['revision']}: {rev['description']}")
        return
    
    asyncio.run(rollback(args.target, args.yes))


if __name__ == "__main__":
    main()
