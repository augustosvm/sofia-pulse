#!/usr/bin/env python3
"""Find tables with 'paper' or 'article' in name"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("=" * 80)
print("🔍 BUSCANDO TABELAS DE PAPERS")
print("=" * 80)
print()

cur.execute("""
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname='sofia' 
      AND (tablename LIKE '%paper%' OR tablename LIKE '%article%')
""")

rows = cur.fetchall()
print(f"Encontradas {len(rows)} tabelas:")
for r in rows:
    print(f"   - {r[0]}")
    
    # Quick count
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{r[0]}")
        count = cur.fetchone()[0]
        print(f"     (Registros: {count:,})")
    except:
        pass

conn.close()
