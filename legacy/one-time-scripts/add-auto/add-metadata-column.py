#!/usr/bin/env python3
"""Reliably add metadata column to trends"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("🔧 FIXING TRENDS SCHEMA")
print("=" * 80)
print()

try:
    cur.execute("ALTER TABLE sofia.trends ADD COLUMN IF NOT EXISTS metadata JSONB")
    print("✅ Column 'metadata' added/verified")
    cur.execute("ALTER TABLE sofia.trends ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()")
    print("✅ Column 'created_at' added/verified")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Verify
try:
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema='sofia' AND table_name='trends'
        ORDER BY ordinal_position
    """)
    cols = [r[0] for r in cur.fetchall()]
    print(f"Current columns: {', '.join(cols)}")
except Exception as e:
    print(f"❌ Error verifying: {e}")

conn.close()
