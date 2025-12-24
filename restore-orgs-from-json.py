#!/usr/bin/env python3
"""Restore organizations from global-370-universities.json"""

import psycopg2
import json
import os
import psycopg2.extras

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("♻️ RESTORING ORGS FROM JSON")
print("=" * 80)
print()

fpath = '/home/ubuntu/sofia-pulse/data/global-370-universities.json'

if not os.path.exists(fpath):
    print(f"❌ File not found: {fpath}")
    exit(1)

try:
    print(f"1️⃣ Reading {fpath}...")
    with open(fpath, 'r') as f:
        data = json.load(f)
        
    print(f"   Loaded {len(data):,} records")
    
    # Check structure
    sample = data[0] if data else {}
    print(f"   Sample keys: {list(sample.keys())}")
    
    # Access the correct list
    if isinstance(data, dict) and 'universities' in data:
        items = data['universities']
    elif isinstance(data, list):
        items = data
    else:
        print("❌ Unknown JSON structure")
        items = []

    print(f"   Using {len(items):,} records")
    
    # 2. Prepare batch
    print("2️⃣ Preparing batch...")
    batch = []
    
    for item in items:
        # Adapt to file structure
        name = item.get('name') or item.get('institution') or item.get('university') or item.get('display_name')
        country = item.get('country') or item.get('location')
        
        if not name: continue
        
        norm_name = name.lower().strip()
        
        # Decide type
        org_type = 'research_center'
        if 'university' in norm_name or 'college' in norm_name: org_type = 'university'
        elif 'hospital' in norm_name: org_type = 'hospital'
        elif 'school' in norm_name: org_type = 'school'
        
        meta = json.dumps({'source': 'global-370-universities.json', 'original_data': item})
        
        batch.append((name, norm_name, org_type, meta))

    print(f"   Ready to insert {len(batch):,} organizations")
    
    # 3. Insert
    print("3️⃣ Inserting...")
    query = """
        INSERT INTO sofia.organizations (name, normalized_name, type, metadata)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (normalized_name) DO NOTHING
    """
    
    psycopg2.extras.execute_batch(cur, query, batch, page_size=1000)
    print("✅ Insert complete")
    
    # Final count
    cur.execute("SELECT COUNT(*) FROM sofia.organizations")
    print(f"📊 Final organizations count: {cur.fetchone()[0]:,}")

except Exception as e:
    print(f"❌ Error: {e}")

conn.close()
