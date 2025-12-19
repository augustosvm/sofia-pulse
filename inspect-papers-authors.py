#!/usr/bin/env python3
"""Inspecionar estrutura de papers e authors"""

import psycopg2
import json

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("=" * 80)
print("🔍 INSPEÇÃO: PAPERS & AUTHORS")
print("=" * 80)
print()

tables = ['papers', 'authors']

for t in tables:
    print(f"--- Tabela: {t} ---")
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema='sofia' AND table_name='{t}'
    """)
    for c in cur.fetchall():
        print(f"   - {c[0]} ({c[1]})")
    
    # Check for metadata or institution fields
    cur.execute(f"SELECT * FROM sofia.{t} LIMIT 1")
    row = cur.fetchone()
    if row:
        print(f"   Amostra ID: {row[0]}")
        # Try to find jsonb cols
        for idx, desc in enumerate(cur.description):
            if desc[0] in ['metadata', 'data', 'raw_data', 'institutions', 'affiliations']:
                print(f"   >>> Coluna {desc[0]}: {row[idx]}")

    print()

conn.close()
