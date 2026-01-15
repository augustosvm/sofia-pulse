#!/usr/bin/env python3
"""Adjust security views to use 90 days for demo (data is from Nov 2025)"""
import psycopg2
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Database config
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

    # Drop and recreate geo view with 90 days
    print("Recreating geo view with 90 days...")
    cur.execute("DROP MATERIALIZED VIEW IF EXISTS sofia.mv_security_geo_points_30d CASCADE")

    cur.execute("""
        CREATE MATERIALIZED VIEW sofia.mv_security_geo_points_30d AS
        SELECT
            latitude,
            longitude,
            country_code,
            country_id,
            SUM(severity_score) as severity_30d,
            COUNT(*) as incidents_30d,
            SUM(COALESCE(fatalities, 0)) as fatalities_30d,
            jsonb_build_object(
                'acled_pct', ROUND(100.0 * COUNT(*) FILTER (WHERE source = 'ACLED') / NULLIF(COUNT(*), 0)),
                'gdelt_pct', ROUND(100.0 * COUNT(*) FILTER (WHERE source = 'GDELT') / NULLIF(COUNT(*), 0))
            ) as source_mix,
            CASE
                WHEN SUM(severity_score) > 100 THEN 'Critical Hotspot'
                WHEN SUM(severity_score) > 50 THEN 'High Risk Zone'
                WHEN SUM(severity_score) > 20 THEN 'Elevated Risk'
                ELSE 'Monitored Area'
            END as label
        FROM sofia.security_events
        WHERE event_date >= CURRENT_DATE - INTERVAL '90 days'
          AND latitude IS NOT NULL
          AND longitude IS NOT NULL
        GROUP BY latitude, longitude, country_code, country_id
        HAVING COUNT(*) >= 1
    """)
    print("OK Geo view recreated with 90 days")

    # Recreate index
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_mv_security_geo_severity
            ON sofia.mv_security_geo_points_30d(severity_30d DESC)
    """)

    # Check counts
    cur.execute("SELECT COUNT(*) FROM sofia.mv_security_geo_points_30d")
    count = cur.fetchone()[0]
    print(f"OK Geo view now has {count} points")

    # Show sample
    if count > 0:
        cur.execute("""
            SELECT country_code, incidents_30d, severity_30d, label
            FROM sofia.mv_security_geo_points_30d
            ORDER BY severity_30d DESC
            LIMIT 5
        """)
        print("\nTop 5 hotspots:")
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]} incidents, severity={row[2]}, {row[3]}")

    cur.close()
    conn.close()
    print("\n[SUCCESS] Views adjusted for demo!")

except Exception as e:
    print(f"[ERROR] {e}")
    exit(1)
