#!/usr/bin/env python3
"""Procura TODAS as tabelas e arquivos com dados de trends"""

import psycopg2
import os
import glob

conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123strong', database='sofia_db')
cur = conn.cursor()

print("=" * 80)
print("🔍 PROCURANDO DADOS DE TRENDS")
print("=" * 80)
print()

# 1. Procurar tabelas no banco
print("1️⃣ TABELAS NO BANCO:")
print()

cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'sofia'
    AND (
        table_name LIKE '%trend%'
        OR table_name LIKE '%github%'
        OR table_name LIKE '%stackoverflow%'
        OR table_name LIKE '%npm%'
        OR table_name LIKE '%pypi%'
        OR table_name LIKE '%skill%'
    )
    ORDER BY table_name
""")

tables = cur.fetchall()

if tables:
    for table in tables:
        table_name = table[0]
        try:
            cur.execute(f"SELECT COUNT(*) FROM sofia.{table_name}")
            count = cur.fetchone()[0]
            
            if count > 0:
                # Mostrar colunas
                cur.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema='sofia' AND table_name='{table_name}'
                    ORDER BY ordinal_position
                    LIMIT 5
                """)
                cols = [r[0] for r in cur.fetchall()]
                
                print(f"✅ {table_name:40s} {count:>10,} registros")
                print(f"   Colunas: {', '.join(cols)}...")
                print()
        except:
            pass
else:
    print("❌ Nenhuma tabela encontrada")

print()

# 2. Procurar arquivos JSON
print("2️⃣ ARQUIVOS JSON:")
print()

json_patterns = [
    '/home/ubuntu/sofia-pulse/**/*trend*.json',
    '/home/ubuntu/sofia-pulse/**/*github*.json',
    '/home/ubuntu/sofia-pulse/**/*npm*.json',
    '/home/ubuntu/sofia-pulse/**/*stackoverflow*.json',
    '/home/ubuntu/sofia-pulse/data/**/*.json',
    '/home/ubuntu/sofia-pulse/output/**/*.json',
]

found_files = []
for pattern in json_patterns:
    files = glob.glob(pattern, recursive=True)
    found_files.extend(files)

if found_files:
    # Remover duplicatas
    found_files = list(set(found_files))
    found_files.sort()
    
    print(f"Encontrados {len(found_files)} arquivos JSON:")
    for f in found_files[:20]:  # Mostrar primeiros 20
        size = os.path.getsize(f) if os.path.exists(f) else 0
        print(f"   {f} ({size:,} bytes)")
    
    if len(found_files) > 20:
        print(f"   ... e mais {len(found_files) - 20} arquivos")
else:
    print("❌ Nenhum arquivo JSON encontrado")

print()
print("=" * 80)

conn.close()
