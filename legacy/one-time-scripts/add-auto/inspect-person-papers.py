#!/usr/bin/env python3
"""Inspecionar person_papers"""

import psycopg2
import json

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("=" * 80)
print("🔍 INSPEÇÃO: PERSON_PAPERS")
print("=" * 80)
print()

# 1. Colunas
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='person_papers'
""")
cols = cur.fetchall()
print("Colunas:")
for c in cols:
    print(f"   - {c[0]} ({c[1]})")

print()

# 2. Amostra
print("Amostra de dados:")
cur.execute("SELECT * FROM sofia.person_papers LIMIT 1")
row = cur.fetchone()
if row:
    print(row)
    
    # Se tiver coluna de metadados ou afiliação
    for idx, col in enumerate(cols):
        name = col[0]
        if name in ['affiliation', 'institution', 'metadata', 'raw_data']:
            print(f"   >>> {name}: {row[idx]}")

conn.close()
