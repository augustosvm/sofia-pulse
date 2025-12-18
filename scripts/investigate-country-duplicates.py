#!/usr/bin/env python3
"""
Investigar duplicação de países na tabela countries
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    user=os.getenv('POSTGRES_USER', 'sofia'),
    password=os.getenv('POSTGRES_PASSWORD'),
    database=os.getenv('POSTGRES_DB', 'sofia_db')
)

cur = conn.cursor()

print("="*60)
print("ANÁLISE DE DUPLICAÇÃO DE PAÍSES")
print("="*60)

# 1. Total de países
cur.execute("SELECT COUNT(*) FROM sofia.countries")
total = cur.fetchone()[0]
print(f"\n📊 Total de países: {total}")

# 2. Países sem ISO code (criados automaticamente)
cur.execute("SELECT COUNT(*) FROM sofia.countries WHERE iso_alpha2 IS NULL")
without_iso = cur.fetchone()[0]
print(f"⚠️  Sem ISO code: {without_iso}")
print(f"✅ Com ISO code: {total - without_iso}")

# 3. Países duplicados (case insensitive)
print("\n" + "="*60)
print("PAÍSES COM NOMES SIMILARES (possíveis duplicatas)")
print("="*60)

cur.execute("""
    SELECT 
        LOWER(TRIM(common_name)) as normalized,
        COUNT(*) as count,
        STRING_AGG(common_name, ', ' ORDER BY common_name) as variations
    FROM sofia.countries
    GROUP BY LOWER(TRIM(common_name))
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    LIMIT 20
""")

duplicates = cur.fetchall()
if duplicates:
    for norm, count, variations in duplicates:
        print(f"\n{norm} ({count} variações):")
        print(f"  {variations}")
else:
    print("Nenhuma duplicata encontrada")

# 4. Países sem ISO (amostra)
print("\n" + "="*60)
print("PAÍSES SEM ISO CODE (primeiros 30)")
print("="*60)

cur.execute("""
    SELECT common_name 
    FROM sofia.countries 
    WHERE iso_alpha2 IS NULL 
    ORDER BY common_name 
    LIMIT 30
""")

no_iso = cur.fetchall()
for (name,) in no_iso:
    print(f"  - {name}")

# 5. Estatísticas por fonte
print("\n" + "="*60)
print("DISTRIBUIÇÃO")
print("="*60)

cur.execute("""
    SELECT 
        CASE 
            WHEN iso_alpha2 IS NOT NULL THEN 'Com ISO (base)'
            ELSE 'Sem ISO (auto-criado)'
        END as source,
        COUNT(*) as count
    FROM sofia.countries
    GROUP BY source
""")

for source, count in cur.fetchall():
    print(f"{source}: {count}")

cur.close()
conn.close()
