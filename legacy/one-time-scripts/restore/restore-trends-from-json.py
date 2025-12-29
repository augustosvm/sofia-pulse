#!/usr/bin/env python3
"""Restore trends data from available JSON files"""

import psycopg2
import json
import os
import datetime

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("♻️ RESTORING TRENDS FROM JSON CACHE")
print("=" * 80)
print()

files_to_process = [
    '/home/ubuntu/sofia-pulse/cache/tag-growth-data.json',
    '/home/ubuntu/sofia-pulse/cache/dashboard-data.json'
]

trends_found = {}

# 1. Process tag-growth-data.json
print("1️⃣ Processing tag-growth-data.json...")
fpath = files_to_process[0]
if os.path.exists(fpath):
    try:
        with open(fpath, 'r') as f:
            data = json.load(f)
            
        print(f"   Read {len(data)} regions")
        for region, info in data.items():
            if isinstance(info, dict) and 'tag' in info:
                tag = info['tag']
                if tag:
                    trends_found[tag] = {
                        'source': 'tag-growth-data',
                        'region': region,
                        'growth_percentage': info.get('growth_percentage'),
                        'trend': info.get('trend')
                    }
        print(f"   Extracted {len(trends_found)} unique trends so far")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print(f"   ❌ File not found: {fpath}")

print()

# 2. Process dashboard-data.json
print("2️⃣ Processing dashboard-data.json...")
fpath = files_to_process[1]
if os.path.exists(fpath):
    try:
        with open(fpath, 'r') as f:
            data = json.load(f)
            
        regions = data.get('regions', {})
        count = 0
        for region, r_data in regions.items():
            top_tags = r_data.get('top_tags', [])
            for tag_info in top_tags:
                tag = tag_info.get('tag')
                if tag:
                    if tag not in trends_found:
                        trends_found[tag] = {
                            'source': 'dashboard-data',
                            'region': region,
                            'count': tag_info.get('count'),
                            'percentage': tag_info.get('percentage')
                        }
                        count += 1
                    else:
                        # Merge info if needed
                        pass
        print(f"   Extracted {count} new trends")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print(f"   ❌ File not found: {fpath}")

print()

# 3. Insert into trends table
print(f"3️⃣ Inserting {len(trends_found)} trends into sofia.trends...")

inserted = 0
for name, meta in trends_found.items():
    try:
        norm_name = name.lower().strip()
        cur.execute("""
            INSERT INTO sofia.trends (name, normalized_name, metadata, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (normalized_name) 
            DO UPDATE SET metadata = trends.metadata || EXCLUDED.metadata
            RETURNING id
        """, (name, norm_name, json.dumps(meta)))
        inserted += 1
    except Exception as e:
        print(f"   ❌ Error inserting {name}: {e}")

print(f"   ✅ Successfully inserted/updated {inserted} trends")

# Final count
cur.execute("SELECT COUNT(*) FROM sofia.trends")
final_count = cur.fetchone()[0]
print(f"\n📊 FINAL COUNT sofia.trends: {final_count:,}")

conn.close()
