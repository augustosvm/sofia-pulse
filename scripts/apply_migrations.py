#!/usr/bin/env python3
"""
Sofia Skills Kit - Apply Migrations
Official migration runner - applies all pending migrations from sql/migrations/
"""

import os
import sys
import re
from pathlib import Path
import psycopg2

# Add project path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def get_applied_migrations(cur):
    """Get list of applied migrations from sofia.schema_migrations."""
    # Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sofia.schema_migrations (
            migration_file VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    cur.execute("SELECT migration_file FROM sofia.schema_migrations ORDER BY migration_file")
    return [row[0] for row in cur.fetchall()]


def get_pending_migrations(migrations_dir, applied):
    """Get list of pending migrations sorted by number."""
    all_files = sorted(migrations_dir.glob("*.sql"))
    
    pending = []
    for file_path in all_files:
        file_name = file_path.name
        if file_name not in applied:
            # Extract number from filename (e.g., 101_name.sql -> 101)
            match = re.match(r'^(\d+)', file_name)
            number = int(match.group(1)) if match else 9999
            pending.append((number, file_name, file_path))
    
    # Sort by number
    pending.sort(key=lambda x: x[0])
    return pending


def apply_migration(cur, file_path, file_name):
    """Apply a single migration."""
    print(f"  Applying: {file_name}...")
    
    with open(file_path, 'r') as f:
        sql = f.read()
    
    try:
        cur.execute(sql)
        
        # Record migration
        cur.execute("""
            INSERT INTO sofia.schema_migrations (migration_file)
            VALUES (%s)
        """, (file_name,))
        
        print(f"    ✅ Applied: {file_name}")
        return True
    
    except Exception as e:
        print(f"    ❌ Failed: {file_name}")
        print(f"       Error: {e}")
        return False


def main():
    print("[apply_migrations] Starting migration runner...")
    
    # Check DATABASE_URL
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    
    # Connect to database
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cur = conn.cursor()
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    # Get migrations directory
    project_root = Path(__file__).resolve().parents[1]
    migrations_dir = project_root / "sql" / "migrations"
    
    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    print(f"[apply_migrations] Migrations directory: {migrations_dir}")
    
    # Get applied migrations
    applied = get_applied_migrations(cur)
    print(f"[apply_migrations] Applied migrations: {len(applied)}")
    
    # Get pending migrations
    pending = get_pending_migrations(migrations_dir, applied)
    
    if not pending:
        print("\n✅ No pending migrations")
        cur.close()
        conn.close()
        sys.exit(0)
    
    print(f"\n[apply_migrations] Pending migrations: {len(pending)}")
    for number, file_name, _ in pending:
        print(f"  - [{number:03d}] {file_name}")
    
    # Apply migrations
    print(f"\n[apply_migrations] Applying migrations...")
    
    success_count = 0
    for number, file_name, file_path in pending:
        if apply_migration(cur, file_path, file_name):
            success_count += 1
            conn.commit()
        else:
            conn.rollback()
            print(f"\n❌ Migration failed: {file_name}")
            print(f"   Stopping migration process")
            break
    
    # Summary
    print(f"\n[apply_migrations] ========================================")
    print(f"[apply_migrations] SUMMARY")
    print(f"[apply_migrations] ========================================")
    print(f"  Total pending: {len(pending)}")
    print(f"  Applied: {success_count}")
    print(f"  Failed: {len(pending) - success_count}")
    
    if success_count == len(pending):
        print(f"\n✅ All migrations applied successfully")
    else:
        print(f"\n⚠️ Some migrations failed")
    
    cur.close()
    conn.close()
    
    sys.exit(0 if success_count == len(pending) else 1)


if __name__ == "__main__":
    main()
