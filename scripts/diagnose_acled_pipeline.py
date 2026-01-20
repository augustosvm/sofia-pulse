#!/usr/bin/env python3
"""
Diagnóstico do Pipeline ACLED - Identificar Gargalos
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB")
)
cur = conn.cursor()

print("="*70)
print("DIAGNÓSTICO DO PIPELINE ACLED")
print("="*70)

# Query 1: LATAM entrou em acled_aggregated.regional?
print("\n1️⃣ LATAM em acled_aggregated.regional:")
cur.execute("""
    SELECT COUNT(*) FROM acled_aggregated.regional
    WHERE region ILIKE '%Latin America%'
""")
latam_regional = cur.fetchone()[0]
print(f"   ✅ {latam_regional:,} registros encontrados")

# Query 2: LATAM entrou em security_events?
print("\n2️⃣ LATAM em sofia.security_events:")
cur.execute("""
    SELECT COUNT(*) FROM sofia.security_events
    WHERE source='ACLED_AGGREGATED'
      AND LOWER(country_name) IN ('brazil','argentina','chile','colombia','peru','venezuela')
""")
latam_events = cur.fetchone()[0]
print(f"   {'✅' if latam_events > 0 else '❌'} {latam_events:,} registros encontrados")

# Query 3: Quantos ACLED ficaram com country_code NULL?
print("\n3️⃣ ACLED com country_code NULL em security_observations:")
cur.execute("""
    SELECT COUNT(*) AS null_cc
    FROM sofia.security_observations
    WHERE source='ACLED' AND country_code IS NULL
""")
null_cc = cur.fetchone()[0]
cur.execute("""
    SELECT COUNT(*) AS total
    FROM sofia.security_observations
    WHERE source='ACLED'
""")
total_acled = cur.fetchone()[0]
null_pct = (null_cc / total_acled * 100) if total_acled > 0 else 0
print(f"   ❌ {null_cc:,} de {total_acled:,} ({null_pct:.1f}%) sem country_code")

# Query 4: Amostra de nomes que falharam
print("\n4️⃣ Amostra de country_name que falharam o match:")
cur.execute("""
    SELECT DISTINCT country_name
    FROM sofia.security_observations
    WHERE source='ACLED' AND country_code IS NULL
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"   - {row[0]}")

print("\n" + "="*70)
print("DIAGNÓSTICO:")
if latam_regional > 0 and latam_events == 0:
    print("🔴 GARGALO 1 CONFIRMADO: LATAM está em regional mas NÃO em security_events")
if null_pct > 5:
    print(f"🔴 GARGALO 2 CONFIRMADO: {null_pct:.1f}% dos registros sem ISO2 (match por nome falhou)")
print("="*70)

conn.close()
