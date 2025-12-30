#!/usr/bin/env python3
"""
Adiciona coluna city à tabela funding_rounds e tenta extrair cidades
"""
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB"),
)
cur = conn.cursor()

# 1. Adicionar coluna city se não existir
print("1. Adicionando coluna city...")
cur.execute(
    """
    ALTER TABLE sofia.funding_rounds 
    ADD COLUMN IF NOT EXISTS city VARCHAR(255)
"""
)
conn.commit()
print("✅ Coluna city adicionada")

# 2. Mapear empresas conhecidas para cidades
print("\n2. Mapeando empresas para cidades...")
city_mappings = {
    "AMAZON COM INC": "Seattle",
    "Alphabet Inc.": "Mountain View",
    "Meta Platforms, Inc.": "Menlo Park",
    "NVIDIA CORP": "Santa Clara",
    "MICROSOFT CORP": "Redmond",
    "Airbnb, Inc.": "San Francisco",
}

updated = 0
for company, city in city_mappings.items():
    cur.execute(
        """
        UPDATE sofia.funding_rounds 
        SET city = %s 
        WHERE company_name = %s AND city IS NULL
    """,
        (city, company),
    )
    updated += cur.rowcount

conn.commit()
print(f"✅ {updated} registros atualizados com cidades")

# 3. Verificar resultado
cur.execute(
    """
    SELECT 
        city, 
        country, 
        COUNT(*) as count,
        STRING_AGG(DISTINCT company_name, ', ') as companies
    FROM sofia.funding_rounds 
    WHERE city IS NOT NULL
    GROUP BY city, country
    ORDER BY count DESC
    LIMIT 10
"""
)

print("\n3. Cidades com funding:")
for row in cur.fetchall():
    print(f"  {row[0]}, {row[1]}: {row[2]} deals ({row[3][:50]}...)")

# 4. Total com cidade vs sem cidade
cur.execute("SELECT COUNT(*) FROM sofia.funding_rounds WHERE city IS NOT NULL")
with_city = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM sofia.funding_rounds WHERE city IS NULL")
without_city = cur.fetchone()[0]

print(f"\n4. Resumo:")
print(f"  Com cidade: {with_city}")
print(f"  Sem cidade: {without_city}")
print(f"  Total: {with_city + without_city}")

conn.close()
print("\n✅ Concluído!")
