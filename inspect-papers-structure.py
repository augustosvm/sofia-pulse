#!/usr/bin/env python3
"""Inspect paper_authors structure"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("=" * 80)
print("🔍 INSPEÇÃO: PAPER_AUTHORS")
print("=" * 80)
print()

# 1. Colunas
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='paper_authors'
""")
cols = cur.fetchall()
print("Colunas:")
has_affiliation = False
for c in cols:
    print(f"   - {c[0]} ({c[1]})")
    if c[0] == 'affiliation': has_affiliation = True

print()

# 2. Amostra de Afiliações
print("Amostra de Afiliações (affiliation_at_time):")
cur.execute("SELECT affiliation_at_time FROM sofia.paper_authors WHERE affiliation_at_time IS NOT NULL LIMIT 10")
for r in cur.fetchall():
    print(f"   - {r[0]}")

# 3. Contagem de Afiliações Únicas
print("\nContagem de Afiliações Únicas (affiliation_at_time):")
cur.execute("SELECT COUNT(DISTINCT affiliation_at_time) FROM sofia.paper_authors")
uniq = cur.fetchone()[0]
print(f"   Total Único: {uniq:,}")

conn.close()
