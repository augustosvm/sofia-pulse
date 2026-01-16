#!/usr/bin/env python3
"""Setup security materialized views"""
import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env
load_dotenv()

# Database config
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "91.98.158.19"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB", "sofia_db")
}

try:
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    # Read migration file
    migration_file = Path(__file__).parent.parent / "migrations" / "051_security_events.sql"
    print(f"Reading migration: {migration_file}")
    migration_sql = migration_file.read_text()

    # Execute migration
    print("Creating materialized views...")
    cur.execute(migration_sql)
    print("OK Migration executed successfully")

    # Refresh views
    print("\nRefreshing materialized views with existing data...")
    cur.execute("SELECT sofia.refresh_security_views()")
    print("OK Views refreshed")

    # Check view counts
    print("\nVerifying views:")
    views = [
        "mv_security_country_summary",
        "mv_security_geo_points_30d",
        "mv_security_momentum"
    ]

    for view in views:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{view}")
        count = cur.fetchone()[0]
        print(f"  - {view}: {count} records")

    cur.close()
    conn.close()
    print("\n[SUCCESS] Security views setup complete!")

except Exception as e:
    print(f"[ERROR] {e}")
    exit(1)
