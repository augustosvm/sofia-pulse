#!/usr/bin/env python3
"""
Security Hybrid Model - Checklist de Validação Completo
"""
import psycopg2, os
from pathlib import Path

def load_env():
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v.strip()

load_env()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    database=os.getenv("POSTGRES_DB")
)
cur = conn.cursor()

print("="*70)
print("SECURITY HYBRID MODEL - CHECKLIST DE VALIDAÇÃO")
print("="*70)

# 1. População da canônica por fonte
print("\n1. POPULAÇÃO DA CANÔNICA POR FONTE")
print("-"*70)

cur.execute("""
    SELECT 
        source,
        signal_type,
        coverage_scope,
        COUNT(*) as records,
        COUNT(DISTINCT country_code) as countries
    FROM sofia.security_observations
    GROUP BY source, signal_type, coverage_scope
    ORDER BY source
""")

sources_found = {}
for source, signal, scope, records, countries in cur.fetchall():
    sources_found[source] = (signal, scope, records, countries)
    status = "✅" if records > 0 else "❌"
    print(f"{status} {source:20} {signal:12} {scope:20} {records:,} records, {countries} countries")

# Check expected sources
expected = {
    'ACLED': ('acute', 'global_comparable'),
    'GDELT': ('acute', 'global_comparable'),
    'WORLD_BANK': ('structural', 'global_comparable'),
}

print("\nStatus por fonte esperada:")
for source, (expected_signal, expected_scope) in expected.items():
    if source in sources_found:
        actual_signal, actual_scope, records, countries = sources_found[source]
        if actual_signal == expected_signal and actual_scope == expected_scope:
            print(f"  ✅ {source}: OK ({records:,} records)")
        else:
            print(f"  ⚠️  {source}: Wrong type (expected {expected_signal}/{expected_scope})")
    else:
        print(f"  ❌ {source}: NOT FOUND")

# 2. Coverage por país (Top 20)
print("\n2. COVERAGE POR PAÍS (Top 20)")
print("-"*70)

cur.execute("""
    SELECT DISTINCT
        country_code,
        country_name,
        coverage_score_global,
        (SELECT COUNT(DISTINCT source) 
         FROM sofia.security_observations o2 
         WHERE o2.country_code = o.country_code 
           AND o2.coverage_scope = 'global_comparable') as source_count
    FROM sofia.security_observations o
    WHERE coverage_scope = 'global_comparable'
      AND country_code IS NOT NULL
    ORDER BY coverage_score_global DESC
    LIMIT 20
""")

print(f"{'Code':5} {'Country':25} {'Coverage':8} {'Sources':8}")
print("-"*70)

ukraine_found = False
usa_found = False

for code, name, coverage, sources in cur.fetchall():
    print(f"{code:5} {name[:25]:25} {coverage:8.0f} {sources:8}")
    if code in ['UA', 'UKR']:
        ukraine_found = True
    if code in ['US', 'USA']:
        usa_found = True

print("\nValidação:")
print(f"  {'✅' if ukraine_found else '❌'} Ucrânia aparece no top 20")
print(f"  {'✅' if usa_found else '❌'} EUA aparece no top 20")

# 3. Verificar países sem fonte não têm coverage alto
print("\n3. PAÍSES SEM FONTE NÃO TÊM COVERAGE ALTO")
print("-"*70)

cur.execute("""
    SELECT country_code, country_name, coverage_score_global
    FROM (
        SELECT DISTINCT country_code, country_name, coverage_score_global
        FROM sofia.security_observations
        WHERE coverage_scope = 'global_comparable'
          AND country_code IS NOT NULL
    ) sub
    WHERE coverage_score_global > 50
      AND country_code NOT IN (
          SELECT DISTINCT country_code 
          FROM sofia.security_observations 
          WHERE source IN ('ACLED', 'GDELT', 'WORLD_BANK')
            AND country_code IS NOT NULL
      )
""")

false_positives = cur.fetchall()
if false_positives:
    print("  ⚠️  ATENÇÃO: Países com coverage alto SEM fonte:")
    for code, name, coverage in false_positives:
        print(f"     {code} {name}: {coverage:.0f}")
else:
    print("  ✅ OK: Nenhum país tem coverage alto sem ter fonte")

# 4. GDELT stddev=0 check
print("\n4. GDELT STDDEV=0 CHECK")
print("-"*70)

cur.execute("""
    SELECT COUNT(*) 
    FROM sofia.security_observations
    WHERE source = 'GDELT'
      AND (severity_norm IS NULL OR severity_norm = 0)
""")

zero_severity = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(*)
    FROM sofia.security_observations
    WHERE source = 'GDELT'
""")

total_gdelt = cur.fetchone()[0]

if total_gdelt > 0:
    zero_pct = (zero_severity / total_gdelt) * 100
    if zero_pct > 50:
        print(f"  ⚠️  ATENÇÃO: {zero_pct:.1f}% dos registros GDELT têm severity=0")
        print(f"     Pode indicar problema com stddev=0")
    else:
        print(f"  ✅ OK: Apenas {zero_pct:.1f}% com severity=0 (normal)")
else:
    print("  ⚠️  Nenhum registro GDELT encontrado")

# 5. Verificar NaN/NULL em severity_norm
print("\n5. VERIFICAR NaN/NULL EM SEVERITY_NORM")
print("-"*70)

cur.execute("""
    SELECT source, COUNT(*)
    FROM sofia.security_observations
    WHERE severity_norm IS NULL
    GROUP BY source
""")

null_severity = cur.fetchall()
if null_severity:
    print("  ⚠️  ATENÇÃO: Registros com severity_norm NULL:")
    for source, count in null_severity:
        print(f"     {source}: {count:,}")
else:
    print("  ✅ OK: Nenhum registro com severity_norm NULL")

# Summary
print("\n" + "="*70)
print("RESUMO DO CHECKLIST")
print("="*70)

acled_ok = 'ACLED' in sources_found and sources_found['ACLED'][2] > 0
gdelt_ok = 'GDELT' in sources_found and sources_found['GDELT'][2] > 0
coverage_ok = ukraine_found and usa_found and not false_positives
stddev_ok = total_gdelt == 0 or zero_pct < 50
null_ok = not null_severity

print(f"\n{'✅' if acled_ok else '❌'} ACLED populado")
print(f"{'✅' if gdelt_ok else '❌'} GDELT populado")
print(f"{'⚠️' } WORLD_BANK (precisa verificar tabela fonte)")
print(f"{'⚠️' } BRASIL (precisa verificar tabela fonte)")
print(f"{'✅' if coverage_ok else '❌'} Coverage por país correto")
print(f"{'✅' if stddev_ok else '❌'} GDELT stddev OK")
print(f"{'✅' if null_ok else '❌'} Sem valores NULL em severity_norm")

all_ok = acled_ok and gdelt_ok and coverage_ok and stddev_ok and null_ok

print(f"\nSTATUS GERAL: {'✅ APROVADO' if all_ok else '⚠️ PRECISA ATENÇÃO'}")

cur.close()
conn.close()

print("\n" + "="*70)
