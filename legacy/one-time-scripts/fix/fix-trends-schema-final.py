#!/usr/bin/env python3
"""Standardize trends schema and add constraints"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("🔧 STANDARDIZING TRENDS SCHEMA")
print("=" * 80)
print()

try:
    # 1. Check existing columns
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema='sofia' AND table_name='trends'
    """)
    cols = [r[0] for r in cur.fetchall()]
    print(f"Columns: {cols}")
    
    # 2. Rename trend_name to name if exists
    if 'trend_name' in cols and 'name' not in cols:
        cur.execute("ALTER TABLE sofia.trends RENAME COLUMN trend_name TO name")
        print("✅ Renamed trend_name -> name")
    
    # 3. Add normalized_name if missing
    if 'normalized_name' not in cols:
        cur.execute("ALTER TABLE sofia.trends ADD COLUMN normalized_name VARCHAR(500)")
        print("✅ Added normalized_name")
        
        # Populate normalized_name if empty
        if 'name' in cols or 'trend_name' in cols:
             cur.execute("UPDATE sofia.trends SET normalized_name = LOWER(TRIM(name)) WHERE normalized_name IS NULL")
             print("✅ Populated normalized_name")
    
    # 4. Add UNIQUE constraint
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS trends_normalized_name_idx 
        ON sofia.trends (normalized_name)
    """)
    print("✅ Added UNIQUE INDEX on normalized_name")
    
    # 5. Add CONSTRAINT for ON CONFLICT to work
    try:
        cur.execute("""
            ALTER TABLE sofia.trends 
            ADD CONSTRAINT trends_normalized_name_key UNIQUE USING INDEX trends_normalized_name_idx
        """)
        print("✅ Added UNIQUE CONSTRAINT")
    except Exception as e:
        if 'already exists' not in str(e):
            print(f"⚠️ Constraint might already exist or error: {e}")
            
except Exception as e:
    print(f"❌ Error: {e}")

conn.close()
