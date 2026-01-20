#!/usr/bin/env python3
"""
Security API - Testes Objetivos de Validação
"""
import psycopg2
import os
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
print("SECURITY API - TESTES OBJETIVOS")
print("="*70)

# TESTE 1: WHERE Precedence
print("\n1. TESTE WHERE PRECEDENCE")
print("-"*70)

# Simular query com sources=acled,local&country=BR
print("Simulando: sources=acled,local&country=BR")
cur.execute("""
    SELECT source, country_code, COUNT(*)
    FROM sofia.security_observations
    WHERE (
        (source IN ('ACLED', 'ACLED_AGGREGATED') AND coverage_scope = 'global_comparable')
        OR
        (source LIKE 'BRASIL_%' AND coverage_scope = 'local_only')
    )
    AND country_code = 'BR'
    AND latitude IS NOT NULL
    AND longitude IS NOT NULL
    GROUP BY source, country_code
""")

br_results = cur.fetchall()
if br_results:
    print("  ✅ Resultados para BR:")
    for source, code, count in br_results:
        print(f"     {source}: {count:,} pontos")
else:
    print("  ⚠️  Nenhum resultado para BR")

# Verificar se NÃO vaza outros países
cur.execute("""
    SELECT DISTINCT country_code
    FROM sofia.security_observations
    WHERE (
        (source IN ('ACLED', 'ACLED_AGGREGATED') AND coverage_scope = 'global_comparable')
        OR
        (source LIKE 'BRASIL_%' AND coverage_scope = 'local_only')
    )
    AND country_code = 'BR'
    AND latitude IS NOT NULL
""")

countries = [r[0] for r in cur.fetchall()]
if countries == ['BR']:
    print("  ✅ WHERE correto: Apenas BR retornado")
elif not countries:
    print("  ⚠️  Nenhum país retornado")
else:
    print(f"  ❌ WHERE ERRADO: Vazou {countries}")

# TESTE 2: Verificar todos os source names
print("\n2. TESTE SOURCE NAMES (ACLED aliases)")
print("-"*70)

cur.execute("""
    SELECT source, COUNT(*)
    FROM sofia.security_observations
    GROUP BY source
    ORDER BY COUNT(*) DESC
""")

print("Sources encontrados:")
acled_variants = []
for source, count in cur.fetchall():
    print(f"  {source:30} {count:,}")
    if 'ACLED' in source.upper():
        acled_variants.append(source)

if acled_variants:
    print(f"\n  ⚠️  ACLED variants encontrados: {acled_variants}")
    print(f"     API aceita: ['ACLED', 'ACLED_AGGREGATED']")
    missing = [v for v in acled_variants if v not in ['ACLED', 'ACLED_AGGREGATED']]
    if missing:
        print(f"  ❌ FALTANDO no alias: {missing}")
    else:
        print(f"  ✅ Todos os variants cobertos")

# TESTE 3: Coverage Score Consistency
print("\n3. TESTE COVERAGE SCORE CONSISTENCY (por país)")
print("-"*70)

cur.execute("""
    SELECT 
        country_code,
        MIN(coverage_score_global) as min_cov,
        MAX(coverage_score_global) as max_cov,
        COUNT(*) as records
    FROM sofia.security_observations
    WHERE coverage_scope = 'global_comparable'
      AND country_code IS NOT NULL
    GROUP BY country_code
    HAVING MIN(coverage_score_global) <> MAX(coverage_score_global)
    ORDER BY COUNT(*) DESC
    LIMIT 20
""")

inconsistent = cur.fetchall()
if inconsistent:
    print("  ❌ INCONSISTÊNCIA: Coverage varia dentro do mesmo país")
    for code, min_cov, max_cov, records in inconsistent[:10]:
        print(f"     {code}: min={min_cov:.0f}, max={max_cov:.0f}, records={records:,}")
    print("\n  SOLUÇÃO: Coverage deve ser calculado POR PAÍS e gravado igual em todas as linhas")
else:
    print("  ✅ Coverage consistente por país")

# TESTE 4: Coverage Score Distribution
print("\n4. TESTE COVERAGE SCORE DISTRIBUTION")
print("-"*70)

cur.execute("""
    SELECT 
        CASE 
            WHEN coverage_score_global >= 75 THEN 'High (75-100)'
            WHEN coverage_score_global >= 50 THEN 'Medium (50-74)'
            WHEN coverage_score_global >= 30 THEN 'Low (30-49)'
            ELSE 'Very Low (0-29)'
        END as level,
        COUNT(DISTINCT country_code) as countries
    FROM sofia.security_observations
    WHERE coverage_scope = 'global_comparable'
      AND country_code IS NOT NULL
    GROUP BY level
    ORDER BY MIN(coverage_score_global) DESC
""")

print("Distribuição de coverage por país:")
for level, count in cur.fetchall():
    print(f"  {level:20} {count:,} países")

# TESTE 5: Brasil Local não vaza para global
print("\n5. TESTE BRASIL LOCAL NÃO VAZA PARA GLOBAL")
print("-"*70)

cur.execute("""
    SELECT COUNT(*)
    FROM sofia.security_observations
    WHERE source LIKE 'BRASIL_%'
      AND coverage_scope = 'global_comparable'
""")

brasil_global = cur.fetchone()[0]
if brasil_global > 0:
    print(f"  ❌ ERRO: {brasil_global:,} registros Brasil em coverage_scope='global_comparable'")
else:
    print("  ✅ Brasil local isolado corretamente")

# TESTE 6: ACLED tem coverage_score_global > 0
print("\n6. TESTE ACLED TEM COVERAGE > 0")
print("-"*70)

cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE coverage_score_global > 0) as with_coverage,
        COUNT(*) FILTER (WHERE coverage_score_global = 0) as zero_coverage
    FROM sofia.security_observations
    WHERE source IN ('ACLED', 'ACLED_AGGREGATED')
      AND coverage_scope = 'global_comparable'
""")

total, with_cov, zero_cov = cur.fetchone()
if total > 0:
    pct_with_cov = (with_cov / total) * 100
    print(f"  Total ACLED: {total:,}")
    print(f"  Com coverage > 0: {with_cov:,} ({pct_with_cov:.1f}%)")
    print(f"  Com coverage = 0: {zero_cov:,}")
    
    if pct_with_cov < 50:
        print(f"  ⚠️  Apenas {pct_with_cov:.1f}% tem coverage > 0")
    else:
        print(f"  ✅ Coverage calculado para maioria")
else:
    print("  ⚠️  Nenhum registro ACLED encontrado")

# TESTE 7: Países com dados mas sem coverage
print("\n7. TESTE PAÍSES COM DADOS MAS SEM COVERAGE")
print("-"*70)

cur.execute("""
    SELECT country_code, country_name, COUNT(*) as records
    FROM sofia.security_observations
    WHERE coverage_scope = 'global_comparable'
      AND (coverage_score_global IS NULL OR coverage_score_global = 0)
      AND country_code IS NOT NULL
    GROUP BY country_code, country_name
    ORDER BY COUNT(*) DESC
    LIMIT 10
""")

no_coverage = cur.fetchall()
if no_coverage:
    print("  ⚠️  Países com dados mas coverage=0:")
    for code, name, records in no_coverage:
        print(f"     {code} {name[:30]:30} {records:,} records")
else:
    print("  ✅ Todos os países com dados têm coverage > 0")

# Summary
print("\n" + "="*70)
print("RESUMO DOS TESTES")
print("="*70)

where_ok = countries == ['BR'] if countries else False
acled_ok = not missing if acled_variants else True
coverage_ok = not inconsistent
brasil_ok = brasil_global == 0
acled_cov_ok = pct_with_cov >= 50 if total > 0 else False

print(f"\n{'✅' if where_ok else '❌'} WHERE precedence correto")
print(f"{'✅' if acled_ok else '⚠️'} ACLED aliases cobertos")
print(f"{'✅' if coverage_ok else '❌'} Coverage consistente por país")
print(f"{'✅' if brasil_ok else '❌'} Brasil local isolado")
print(f"{'✅' if acled_cov_ok else '⚠️'} ACLED com coverage calculado")

all_ok = where_ok and acled_ok and coverage_ok and brasil_ok and acled_cov_ok

print(f"\nSTATUS GERAL: {'✅ TODOS OS TESTES PASSARAM' if all_ok else '⚠️ PRECISA ATENÇÃO'}")

cur.close()
conn.close()

print("\n" + "="*70)
