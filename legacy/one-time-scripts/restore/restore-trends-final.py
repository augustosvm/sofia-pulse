#!/usr/bin/env python3
"""Restore trends data robustly handling schema - ATTEMPT 3"""

import psycopg2
import json
import os

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("♻️ RESTORING TRENDS (FINAL ATTEMPT)")
print("=" * 80)
print()

# 1. Determine correct name column
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='trends'
""")
cols = set(r[0] for r in cur.fetchall())
print(f"Columns found: {cols}")

# PRIORITIZE trend_name because it has NOT NULL constraint
if 'trend_name' in cols:
    name_col = 'trend_name'
else:
    name_col = 'name'

print(f"Using name column: {name_col}")

# 2. Files to process
files_to_process = [
    '/home/ubuntu/sofia-pulse/cache/tag-growth-data.json',
    '/home/ubuntu/sofia-pulse/cache/dashboard-data.json'
]

trends_found = {}

# Process files
for fpath in files_to_process:
    if os.path.exists(fpath):
        try:
            with open(fpath, 'r') as f:
                data = json.load(f)
            
            # Logic for tag-growth-data
            if 'brazil' in data and isinstance(data['brazil'], dict):
                for region, info in data.items():
                    if isinstance(info, dict) and 'tag' in info:
                        tag = info['tag']
                        if tag: trends_found[tag] = {'source': 'tag-growth', 'region': region}
            
            # Logic for dashboard-data
            if 'regions' in data:
                regions = data.get('regions', {})
                for region, r_data in regions.items():
                    for tag_info in r_data.get('top_tags', []):
                        tag = tag_info.get('tag')
                        if tag: trends_found[tag] = {'source': 'dashboard', 'region': region}
                        
        except Exception as e:
            print(f"Error reading {fpath}: {e}")

print(f"Found {len(trends_found)} unique trends")

# 3. Insert
inserted = 0
for name, meta in trends_found.items():
    try:
        norm_name = name.lower().strip()
        if not norm_name: continue
        
        # Prepare query with conditional column name
        query = f"""
            INSERT INTO sofia.trends ({name_col}, normalized_name, metadata, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (normalized_name) 
            DO UPDATE SET metadata = trends.metadata || EXCLUDED.metadata
        """
        cur.execute(query, (name, norm_name, json.dumps(meta)))
        inserted += 1
    except Exception as e:
        print(f"Error inserting {name}: {e}")

print(f"✅ Successfully inserted {inserted} trends")

cur.execute("SELECT COUNT(*) FROM sofia.trends")
print(f"Final count: {cur.fetchone()[0]}")

# Show sample
print("\nSample trends:")
cur.execute(f"SELECT {name_col} FROM sofia.trends LIMIT 5")
for r in cur.fetchall():
    print(f"  - {r[0]}")

conn.close()
