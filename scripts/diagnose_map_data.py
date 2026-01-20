import os
import psycopg2
from datetime import datetime

# Database connection
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

    print(f"--- Diagnosing RAW sofia.security_events ---")
    cur.execute("SELECT count(*) FROM sofia.security_events")
    raw_count = cur.fetchone()[0]
    print(f"Total RAW events: {raw_count}")

    if raw_count > 0:
        cur.execute("SELECT count(*) FROM sofia.security_events WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
        geo_count = cur.fetchone()[0]
        print(f"Events with Geo (Lat/Lon): {geo_count}")
        
        cur.execute("SELECT min(event_date), max(event_date) FROM sofia.security_events")
        dates = cur.fetchone()
        print(f"Date Range: {dates[0]} to {dates[1]}")

    print(f"--- Diagnosing sofia.mv_security_geo_points ---")
    
    # 1. Total count
    cur.execute("SELECT count(*) FROM sofia.mv_security_geo_points")
    total_count = cur.fetchone()[0]
    print(f"Total rows in view: {total_count}")

    # 2. Count with incidents_30d > 0
    cur.execute("SELECT count(*) FROM sofia.mv_security_geo_points WHERE incidents_30d > 0")
    active_30d = cur.fetchone()[0]
    print(f"Rows with incidents_30d > 0: {active_30d}")

    # 3. Count with incidents_total > 0 (if valid column?) 
    # Let's check columns first or just rely on 30d.
    # Actually, let's check statistics of 30d column
    cur.execute("SELECT min(incidents_30d), max(incidents_30d), avg(incidents_30d) FROM sofia.mv_security_geo_points")
    stats = cur.fetchone()
    print(f"Incidents 30d Stats - Min: {stats[0]}, Max: {stats[1]}, Avg: {stats[2]}")
    
    # 4. Check date ranges in underlying events table if header permits
    # assuming we can just check the materialized view for now.

    cur.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
