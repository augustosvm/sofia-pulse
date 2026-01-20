#!/usr/bin/env python3
import psycopg2, os, traceback
from pathlib import Path

def load_env():
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v.strip()

load_env()

try:
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB")
    )
    
    cur = conn.cursor()
    
    # Test 1: Check if table exists
    print("Test 1: Checking if sofia.security_events exists...")
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'sofia' 
            AND table_name = 'security_events'
        )
    """)
    exists = cur.fetchone()[0]
    print(f"   Result: {exists}")
    
    if not exists:
        print("   Table does NOT exist! Creating it...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sofia.security_events (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(100) UNIQUE,
                event_date DATE,
                event_type VARCHAR(100),
                sub_event_type VARCHAR(100),
                country_name VARCHAR(200),
                country_code VARCHAR(10),
                admin1 VARCHAR(200),
                admin2 VARCHAR(200),
                location TEXT,
                latitude DECIMAL(10, 6),
                longitude DECIMAL(10, 6),
                fatalities INTEGER DEFAULT 0,
                notes TEXT,
                data_source VARCHAR(50),
                source_url TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("   Table created!")
    
    # Test 2: Try to count
    print("\nTest 2: Counting records...")
    cur.execute("SELECT COUNT(*) FROM sofia.security_events")
    count = cur.fetchone()[0]
    print(f"   Total records: {count:,}")
    
    # Test 3: Count by data_source
    print("\nTest 3: Counting by data_source...")
    cur.execute("""
        SELECT data_source, COUNT(*) 
        FROM sofia.security_events 
        GROUP BY data_source
    """)
    for source, count in cur.fetchall():
        print(f"   {source}: {count:,}")
    
    cur.close()
    conn.close()
    print("\nAll tests passed!")
    
except Exception as e:
    print(f"\nERROR: {e}")
    traceback.print_exc()
