#!/usr/bin/env python3
"""Auditoria da tabela global_research_institutions"""

import psycopg2

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("=" * 80)
print("🧐 AUDITORIA: global_research_institutions")
print("=" * 80)
print()

table = 'global_research_institutions'

# 1. Contagem Total (sem filtros)
cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
total = cur.fetchone()[0]
print(f"Total registros na tabela: {total:,}")

# 2. Contagem de Nulos
cur.execute(f"SELECT COUNT(*) FROM sofia.{table} WHERE institution IS NULL")
nulls = cur.fetchone()[0]
print(f"Registros com institution NULL: {nulls:,}")
print(f"Registros válidos (NOT NULL): {total - nulls:,}")

# 3. Colunas
cur.execute(f"""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema='sofia' AND table_name='{table}'
""")
cols = [r[0] for r in cur.fetchall()]
print(f"Colunas: {', '.join(cols)}")

# 4. Amostra de dados (se tiver nulos, o que tem neles?)
if nulls > 0:
    print("\nAmostra de registros NULL:")
    cur.execute(f"SELECT * FROM sofia.{table} WHERE institution IS NULL LIMIT 2")
    for r in cur.fetchall():
        print(r)

conn.close()
