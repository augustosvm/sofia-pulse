#!/usr/bin/env python3
"""Quick check of security data in database"""
import psycopg2
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Database config - parse manually
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "91.98.158.19"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD", "SofiaPulse2025Secure@DB"),
    "database": os.getenv("POSTGRES_DB", "sofia_db")
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Check if schema exists
    cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'sofia')")
    schema_exists = cur.fetchone()[0]
    print(f"OK Schema 'sofia' exists: {schema_exists}")

    if schema_exists:
        # Check security_events table
        cur.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'sofia' AND table_name = 'security_events'
            )
        """)
        table_exists = cur.fetchone()[0]
        print(f"OK Table 'security_events' exists: {table_exists}")

        if table_exists:
            # Count records
            cur.execute("SELECT COUNT(*) FROM sofia.security_events")
            count = cur.fetchone()[0]
            print(f"OK Records in security_events: {count}")

            if count > 0:
                # Show table structure
                cur.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'sofia' AND table_name = 'security_events'
                    ORDER BY ordinal_position
                """)
                print("\nTable structure:")
                columns = cur.fetchall()
                for col in columns:
                    print(f"  - {col[0]}: {col[1]}")

                # Get column names
                col_names = [c[0] for c in columns]
                select_cols = ', '.join(col_names[:5])  # First 5 columns

                # Show sample
                cur.execute(f"SELECT {select_cols} FROM sofia.security_events ORDER BY id DESC LIMIT 3")
                print(f"\nSample data (recent):")
                for row in cur.fetchall():
                    print(f"  {row}")

        # Check materialized views
        cur.execute("""
            SELECT table_name FROM information_schema.views
            WHERE table_schema = 'sofia' AND table_name LIKE 'mv_security%'
        """)
        views = cur.fetchall()
        print(f"\nOK Materialized views found: {len(views)}")
        for view in views:
            print(f"  - {view[0]}")
            cur.execute(f"SELECT COUNT(*) FROM sofia.{view[0]}")
            view_count = cur.fetchone()[0]
            print(f"    Records: {view_count}")

    cur.close()
    conn.close()
    print("\n[SUCCESS] Database check complete")

except Exception as e:
    print(f"[ERROR] Error: {e}")
    exit(1)
