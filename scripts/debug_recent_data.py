import psycopg2
import os

DB_HOST = "91.98.158.19"
DB_NAME = "sofia_db"
DB_USER = "sofia"
DB_PASS = "SofiaPulse2025Secure@DB"
DB_PORT = "5432"

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    cur = conn.cursor()
    
    print("--- recent data debug ---")
    
    # 1. Check sources
    cur.execute("SELECT DISTINCT source FROM sofia.security_events WHERE event_date >= NOW() - INTERVAL '90 days'")
    print(f"Sources (90d): {cur.fetchall()}")

    # 2. Check NULL country codes
    cur.execute("SELECT count(*) FROM sofia.security_events WHERE event_date >= NOW() - INTERVAL '90 days' AND country_code IS NULL")
    null_count = cur.fetchone()[0]
    print(f"Recent Events with NULL country_code: {null_count}")

    # 3. List top countries with NULL code
    if null_count > 0:
        cur.execute("""
            SELECT country_name, count(*) as c 
            FROM sofia.security_events 
            WHERE event_date >= NOW() - INTERVAL '90 days' 
              AND country_code IS NULL
            GROUP BY country_name 
            ORDER BY c DESC 
            LIMIT 20
        """)
        print("Top Missing Country Codes:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}")

    # 4. Check Sources for GEO events only
    print("--- Sources with Geo Data ---")
    cur.execute("SELECT source, count(*) FROM sofia.security_events WHERE event_date >= NOW() - INTERVAL '90 days' AND latitude IS NOT NULL GROUP BY source")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

    print("--- ACLED_AGGREGATED Diagnostics ---")
    cur.execute("SELECT count(*) FROM sofia.security_events WHERE source='ACLED_AGGREGATED' AND event_date >= NOW() - INTERVAL '90 days' AND country_code IS NULL")
    print(f"ACLED_AGGREGATED with NULL Code: {cur.fetchone()[0]}")

    cur.execute("SELECT count(*) FROM sofia.security_events WHERE source='ACLED_AGGREGATED' AND event_date >= NOW() - INTERVAL '90 days' AND country_name IS NULL")
    print(f"ACLED_AGGREGATED with NULL Name: {cur.fetchone()[0]}")

    print("--- Top Missing Names (ACLED_AGGREGATED) ---")
    cur.execute("""
        SELECT country_name, count(*) as c 
        FROM sofia.security_events 
        WHERE source='ACLED_AGGREGATED'
          AND event_date >= NOW() - INTERVAL '90 days' 
          AND country_code IS NULL
        GROUP BY country_name 
        ORDER BY c DESC 
        LIMIT 20
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

except Exception as e:
    print(f"Error: {e}")
