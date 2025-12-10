#!/usr/bin/env python3
"""
Script de diagnóstico para verificar tabelas de jobs
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB')
)

cur = conn.cursor()

print("=" * 60)
print("DIAGNÓSTICO DE TABELAS DE JOBS")
print("=" * 60)

# Verificar tabelas relacionadas a jobs
print("\n1. Tabelas com 'job' no nome:")
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='sofia' AND table_name LIKE '%job%'
    ORDER BY table_name
""")
tables = cur.fetchall()
for table in tables:
    print(f"   - {table[0]}")

if not tables:
    print("   ❌ Nenhuma tabela encontrada!")
else:
    # Verificar estrutura da tabela
    table_name = tables[0][0]
    print(f"\n2. Estrutura da tabela 'sofia.{table_name}':")
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema='sofia' AND table_name='{table_name}'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    for col in columns:
        print(f"   - {col[0]}: {col[1]}")
    
    # Contar registros
    print(f"\n3. Total de registros em 'sofia.{table_name}':")
    cur.execute(f"SELECT COUNT(*) FROM sofia.{table_name}")
    count = cur.fetchone()[0]
    print(f"   Total: {count}")
    
    if count > 0:
        print(f"\n4. Últimos 5 registros:")
        cur.execute(f"""
            SELECT id, title, company, platform, collected_at 
            FROM sofia.{table_name} 
            ORDER BY collected_at DESC NULLS LAST
            LIMIT 5
        """)
        for row in cur.fetchall():
            print(f"   - ID:{row[0]} | {row[1]} @ {row[2]} | Platform:{row[3]} | {row[4]}")

print("\n" + "=" * 60)

conn.close()
