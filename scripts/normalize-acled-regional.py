#!/usr/bin/env python3
"""
ACLED Regional to Security Events Normalizer - FINAL CORRECT VERSION
Uses the actual table structure from sofia.security_events
"""

import os
import sys
from pathlib import Path
import psycopg2
import json

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value.strip()

load_env()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "sofia"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        database=os.getenv("POSTGRES_DB", "sofia_db"),
    )

def normalize_regional_to_events():
    """Transfer aggregated regional data to security_events table"""
    
    print("="*70)
    print("ACLED REGIONAL -> SECURITY EVENTS NORMALIZER")
    print("="*70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check source data
    print("\nChecking source data...")
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT region) FROM acled_aggregated.regional")
    total, regions = cursor.fetchone()
    print(f"   Source: {total:,} records, {regions} regions")
    
    # Check target data
    cursor.execute("SELECT COUNT(*) FROM sofia.security_events WHERE source = 'ACLED_AGGREGATED'")
    existing = cursor.fetchone()[0]
    print(f"   Target: {existing:,} existing records")
    
    if existing > 0:
        print(f"\n   Clearing {existing:,} old records...")
        cursor.execute("DELETE FROM sofia.security_events WHERE source = 'ACLED_AGGREGATED'")
        conn.commit()
        print(f"   OK Cleared")
    
    # Insert normalized data
    print("\nNormalizing and inserting...")
    
    cursor.execute("""
        INSERT INTO sofia.security_events (
            source,
            source_id,
            event_date,
            week_start,
            country_name,
            admin1,
            city,
            latitude,
            longitude,
            event_type,
            sub_event_type,
            fatalities,
            event_count,
            raw_payload,
            source_url
        )
        SELECT
            'ACLED_AGGREGATED' as source,
            'ACLED_AGG_' || r.id::text as source_id,
            CASE
                WHEN r.month IS NOT NULL THEN 
                    make_date(r.year, r.month, 15)
                WHEN r.week IS NOT NULL THEN
                    (date_trunc('year', make_date(r.year, 1, 1)) + 
                     ((r.week - 1) * INTERVAL '1 week'))::date
                ELSE
                    make_date(r.year, 6, 30)
            END as event_date,
            CASE
                WHEN r.week IS NOT NULL THEN
                    (date_trunc('year', make_date(r.year, 1, 1)) + 
                     ((r.week - 1) * INTERVAL '1 week'))::date
                ELSE NULL
            END as week_start,
            r.country as country_name,
            r.admin1,
            r.admin2 as city,
            r.centroid_latitude as latitude,
            r.centroid_longitude as longitude,
            COALESCE(r.event_type, 'Political Violence') as event_type,
            r.disorder_type as sub_event_type,
            r.fatalities,
            r.events as event_count,
            jsonb_build_object(
                'region', r.region,
                'dataset_slug', r.dataset_slug,
                'year', r.year,
                'month', r.month,
                'week', r.week,
                'metadata', r.metadata
            ) as raw_payload,
            'https://acleddata.com/aggregated/' || r.dataset_slug as source_url
        FROM acled_aggregated.regional r
        WHERE r.centroid_latitude IS NOT NULL 
          AND r.centroid_longitude IS NOT NULL
          AND r.events > 0
    """)
    
    inserted = cursor.rowcount
    conn.commit()
    
    print(f"   OK Inserted {inserted:,} events")
    
    # Refresh materialized views
    print("\nRefreshing views...")
    
    try:
        cursor.execute("REFRESH MATERIALIZED VIEW sofia.mv_security_geo_points")
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM sofia.mv_security_geo_points")
        geo_points = cursor.fetchone()[0]
        print(f"   OK mv_security_geo_points: {geo_points:,} points")
    except Exception as e:
        print(f"   WARNING: {e}")
    
    try:
        cursor.execute("REFRESH MATERIALIZED VIEW sofia.mv_security_country_summary")
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM sofia.mv_security_country_summary")
        countries_count = cursor.fetchone()[0]
        print(f"   OK mv_security_country_summary: {countries_count} countries")
    except Exception as e:
        print(f"   WARNING: {e}")
    
    # Verify
    print("\nVerification:")
    cursor.execute("""
        SELECT country_name, COUNT(*) as events
        FROM sofia.security_events
        WHERE source = 'ACLED_AGGREGATED'
        GROUP BY country_name
        ORDER BY events DESC
        LIMIT 10
    """)
    
    print("\n   Top 10 countries:")
    for row in cursor.fetchall():
        print(f"   - {row[0]}: {row[1]:,} events")
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM sofia.security_events
        WHERE source = 'ACLED_AGGREGATED'
          AND country_name ILIKE '%ukraine%'
    """)
    ukraine_count = cursor.fetchone()[0]
    
    if ukraine_count > 0:
        print(f"\n   OK Ukraine: {ukraine_count:,} events")
    else:
        print("\n   WARNING: Ukraine NOT found")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*70)
    print("COMPLETE! Refresh your browser to see the map.")
    print("="*70)

if __name__ == "__main__":
    normalize_regional_to_events()
