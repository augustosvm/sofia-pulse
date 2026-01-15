#!/usr/bin/env python3
"""Apply fixed security views migration"""
import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "91.98.158.19"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD", "SofiaPulse2025Secure@DB"),
    "database": os.getenv("POSTGRES_DB", "sofia_db")
}

try:
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    # Read migration file
    migration_file = Path(__file__).parent.parent / "migrations" / "051_security_events_fixed.sql"
    print(f"Reading migration: {migration_file}")
    migration_sql = migration_file.read_text()

    # Execute migration
    print("Applying migration...")
    cur.execute(migration_sql)
    print("OK Migration applied")

    # Verify views
    print("\nVerifying views:")
    cur.execute("""
        SELECT matviewname
        FROM pg_matviews
        WHERE schemaname = 'sofia' AND matviewname LIKE 'mv_security%'
        ORDER BY matviewname
    """)
    views = cur.fetchall()

    for view in views:
        view_name = view[0]
        cur.execute(f"SELECT COUNT(*) FROM sofia.{view_name}")
        count = cur.fetchone()[0]
        print(f"  - {view_name}: {count} records")

        # Sample data
        if view_name == 'mv_security_country_summary':
            cur.execute(f"""
                SELECT country_name, incidents, fatalities, severity_norm, risk_level
                FROM sofia.{view_name}
                ORDER BY severity_norm DESC
                LIMIT 5
            """)
            print(f"\n    Top 5 countries by severity:")
            for row in cur.fetchall():
                print(f"      {row[0]}: {row[1]} incidents, {row[2]} fatalities, severity={row[3]}, {row[4]}")

    cur.close()
    conn.close()
    print("\n[SUCCESS] Security views fixed!")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    exit(1)
