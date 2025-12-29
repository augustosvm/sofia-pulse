#!/usr/bin/env python3
"""Deep search for trends data in DB and Files"""

import psycopg2
import os
import json
import glob

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("=" * 80)
print("🔍 DEEP SEARCH FOR DATA")
print("=" * 80)
print()

# 1. DB TABLES CHECK
print("1️⃣ DB TABLES STATUS:")
tables_to_check = [
    'ai_github_trends', 'github_trending', 'stackoverflow_trends', 
    'ai_npm_packages', 'ai_pypi_packages', 'tech_radar', 'trends'
]

for t in tables_to_check:
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{t}")
        count = cur.fetchone()[0]
        print(f"   {t:30s} {count:>10,} records")
    except:
        print(f"   {t:30s} {'NOT FOUND':>10s}")

print()

# 2. FILE CONTENT SEARCH
print("2️⃣ SEARCHING FOR JSON DATA FILES:")
base_dir = '/home/ubuntu/sofia-pulse'
keywords = ['stars', 'repo_name', 'full_name', 'stargazers_count']

print(f"   Searching in {base_dir} for files containing keywords...")

found_files = []
# Search specifically in likely directories first to be fast
search_dirs = [
    os.path.join(base_dir, 'data'),
    os.path.join(base_dir, 'output'),
    base_dir
]

for directory in search_dirs:
    if not os.path.exists(directory): continue
    
    for root, dirs, files in os.walk(directory):
        if 'node_modules' in root or '.git' in root: continue
        
        for file in files:
            if not file.endswith('.json'): continue
            
            filepath = os.path.join(root, file)
            try:
                # Read first 1kb to check for keywords
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2000)
                    
                if any(k in content for k in keywords):
                    size = os.path.getsize(filepath)
                    print(f"   📄 FOUND: {filepath} ({size:,} bytes)")
                    found_files.append(filepath)
            except Exception as e:
                pass

if not found_files:
    print("   ❌ No relevant JSON files found")
else:
    print(f"   ✅ Found {len(found_files)} potential data files")

conn.close()
