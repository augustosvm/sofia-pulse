#!/usr/bin/env python3
"""List database tables by size"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("=" * 80)
print("📊 DB TABLES BY SIZE (Top 20)")
print("=" * 80)
print()

cur.execute("""
    SELECT 
        relname as table_name, 
        n_live_tup as row_count
    FROM pg_stat_user_tables 
    WHERE schemaname='sofia' 
    ORDER BY n_live_tup DESC 
    LIMIT 20
""")

rows = cur.fetchall()
for r in rows:
    print(f"{r[0]:30} {r[1]:,}")

print("-" * 40)
print(f"Total tables: {len(rows)}")

conn.close()
