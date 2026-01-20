#!/usr/bin/env python3
"""
ACLED Coverage Diagnostic
Executes all diagnostic queries to determine geographic coverage
"""

import os
import sys
from pathlib import Path
import psycopg2
from datetime import datetime

# Load .env
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
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "sofia"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        database=os.getenv("POSTGRES_DB", "sofia_db"),
    )

def run_query(cursor, title, query):
    """Run a query and print results"""
    print(f"\n{'='*70}")
    print(f"📊 {title}")
    print(f"{'='*70}")
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        if not results:
            print("   ⚠️  No results")
            return
        
        # Get column names
        colnames = [desc[0] for desc in cursor.description]
        
        # Print header
        header = " | ".join(f"{col:20}" for col in colnames)
        print(f"\n   {header}")
        print(f"   {'-' * len(header)}")
        
        # Print rows
        for row in results[:30]:  # Limit to 30 rows
            row_str = " | ".join(f"{str(val):20}" for val in row)
            print(f"   {row_str}")
        
        if len(results) > 30:
            print(f"\n   ... ({len(results) - 30} more rows)")
        
        print(f"\n   Total rows: {len(results)}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    print("="*70)
    print("🔍 ACLED COVERAGE DIAGNOSTIC")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1) Event-level coverage (sofia.security_events or sofia.acled_events)
    print("\n\n" + "="*70)
    print("1️⃣  EVENT-LEVEL DATA (sofia.acled_events)")
    print("="*70)
    
    # Check if table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'sofia' 
            AND table_name = 'acled_events'
        )
    """)
    
    if cursor.fetchone()[0]:
        run_query(cursor, "Total Countries in Event-Level", """
            SELECT COUNT(DISTINCT country) AS countries
            FROM sofia.acled_events
        """)
        
        run_query(cursor, "Top 20 Countries by Events", """
            SELECT country, COUNT(*) AS events, MAX(event_date) AS latest_date
            FROM sofia.acled_events
            GROUP BY country
            ORDER BY events DESC
            LIMIT 20
        """)
        
        run_query(cursor, "Specific Countries Check (Ukraine, Russia, Israel, USA)", """
            SELECT country, COUNT(*) AS events, 
                   MIN(event_date) AS earliest, 
                   MAX(event_date) AS latest
            FROM sofia.acled_events
            WHERE country IN ('Ukraine', 'Russia', 'Israel', 'United States of America', 
                             'United States', 'USA')
            GROUP BY country
        """)
    else:
        print("   ⚠️  Table sofia.acled_events does not exist")
    
    # 2) Aggregated regional coverage
    print("\n\n" + "="*70)
    print("2️⃣  AGGREGATED REGIONAL DATA (acled_aggregated.regional)")
    print("="*70)
    
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'acled_aggregated' 
            AND table_name = 'regional'
        )
    """)
    
    if cursor.fetchone()[0]:
        run_query(cursor, "Regional Table Summary", """
            SELECT COUNT(DISTINCT country) AS countries,
                   COUNT(*) AS total_rows,
                   MIN(collected_at) AS first_collection,
                   MAX(collected_at) AS last_collection
            FROM acled_aggregated.regional
        """)
        
        run_query(cursor, "Coverage by Dataset and Region", """
            SELECT dataset_slug, region, 
                   COUNT(*) AS rows,
                   COUNT(DISTINCT country) AS countries
            FROM acled_aggregated.regional
            GROUP BY dataset_slug, region
            ORDER BY rows DESC
        """)
        
        run_query(cursor, "All Distinct Regions", """
            SELECT DISTINCT region, COUNT(*) AS records
            FROM acled_aggregated.regional
            GROUP BY region
            ORDER BY region
        """)
        
        run_query(cursor, "Sample Countries from Regional", """
            SELECT DISTINCT country
            FROM acled_aggregated.regional
            ORDER BY country
            LIMIT 50
        """)
    else:
        print("   ⚠️  Table acled_aggregated.regional does not exist")
    
    # 3) Metadata check
    print("\n\n" + "="*70)
    print("3️⃣  ACLED METADATA (acled_metadata.datasets)")
    print("="*70)
    
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'acled_metadata' 
            AND table_name = 'datasets'
        )
    """)
    
    if cursor.fetchone()[0]:
        run_query(cursor, "Aggregated Datasets Collected", """
            SELECT dataset_slug, source_url, collected_at, 
                   file_size_bytes, total_rows
            FROM acled_metadata.datasets
            WHERE dataset_slug ILIKE '%aggregated%'
            ORDER BY collected_at DESC
        """)
    else:
        print("   ⚠️  Table acled_metadata.datasets does not exist")
    
    # 4) Materialized views check
    print("\n\n" + "="*70)
    print("4️⃣  MATERIALIZED VIEWS (mv_security_geo_points)")
    print("="*70)
    
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM pg_matviews 
            WHERE schemaname = 'public' 
            AND matviewname = 'mv_security_geo_points'
        )
    """)
    
    if cursor.fetchone()[0]:
        run_query(cursor, "Geo Points Summary", """
            SELECT COUNT(*) AS total_points,
                   COUNT(DISTINCT country_name) AS countries
            FROM mv_security_geo_points
        """)
        
        run_query(cursor, "Top 30 Countries by Geo Points", """
            SELECT country_name, COUNT(*) AS points
            FROM mv_security_geo_points
            GROUP BY country_name
            ORDER BY points DESC
            LIMIT 30
        """)
    else:
        print("   ⚠️  Materialized view mv_security_geo_points does not exist")
    
    # 5) Geo completeness check
    print("\n\n" + "="*70)
    print("5️⃣  GEO COMPLETENESS CHECK")
    print("="*70)
    
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'acled_aggregated' 
            AND table_name = 'regional'
        )
    """)
    
    if cursor.fetchone()[0]:
        run_query(cursor, "Missing vs Has Geo Coordinates", """
            SELECT
                SUM(CASE WHEN centroid_latitude IS NULL OR centroid_longitude IS NULL 
                    THEN 1 ELSE 0 END) AS missing_geo,
                SUM(CASE WHEN centroid_latitude IS NOT NULL AND centroid_longitude IS NOT NULL 
                    THEN 1 ELSE 0 END) AS has_geo,
                ROUND(100.0 * SUM(CASE WHEN centroid_latitude IS NOT NULL 
                    AND centroid_longitude IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) 
                    AS geo_percentage
            FROM acled_aggregated.regional
        """)
    
    # Final summary
    print("\n\n" + "="*70)
    print("📋 DIAGNOSTIC SUMMARY")
    print("="*70)
    
    cursor.close()
    conn.close()
    
    print("\n✅ Diagnostic complete!")
    print("\nNext steps:")
    print("1. Review the results above")
    print("2. Identify which regions are missing")
    print("3. Run collectors for missing regions")
    print("4. Refresh materialized views if needed")

if __name__ == "__main__":
    main()
