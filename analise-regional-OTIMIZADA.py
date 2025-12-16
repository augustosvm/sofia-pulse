#!/usr/bin/env python3
"""
Sofia Pulse - Análise Regional OTIMIZADA
Queries simplificadas para evitar erro de disco
"""

import psycopg2

password = 'your_password_here'
try:
    with open('/home/ubuntu/sofia-pulse/.env', 'r') as f:
        for line in f:
            if line.startswith('POSTGRES_PASSWORD='):
                password = line.split('=', 1)[1].strip()
                break
except:
    pass

print("🚀 Sofia Pulse - Análise Regional OTIMIZADA")
print("=" * 80)
print()

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

print("📡 Conectado ao banco de dados!")
print()

# 1. Análise simples: contar papers por país
print("=" * 80)
print("📊 PAPERS POR PAÍS (Top 20)")
print("=" * 80)
print()

cursor.execute("""
SELECT 
  country_code,
  institution_name,
  papers_collected
FROM sofia.global_universities_progress
WHERE country_code IS NOT NULL
ORDER BY papers_collected DESC
LIMIT 20
""")

results = cursor.fetchall()
for row in results:
    print(f"{row[0]:<5} {row[1]:<60} {row[2]:>8} papers")

print()

# 2. Total por país
print("=" * 80)
print("📊 TOTAL DE PAPERS POR PAÍS")
print("=" * 80)
print()

cursor.execute("""
SELECT 
  country_code,
  COUNT(*) as institutions,
  SUM(papers_collected) as total_papers
FROM sofia.global_universities_progress
WHERE country_code IS NOT NULL
GROUP BY country_code
ORDER BY total_papers DESC
LIMIT 20
""")

results = cursor.fetchall()
for row in results:
    print(f"{row[0]:<5} {row[1]:>3} instituições  {row[2]:>10} papers")

print()

# 3. Top 10 assuntos em person_papers (sample)
print("=" * 80)
print("📊 TOP 10 ASSUNTOS GLOBAIS (amostra de 10K papers)")
print("=" * 80)
print()

cursor.execute("""
SELECT 
  UNNEST(fields) as field,
  COUNT(*) as count
FROM (
  SELECT fields 
  FROM sofia.person_papers 
  WHERE fields IS NOT NULL 
  LIMIT 10000
) sample
GROUP BY field
ORDER BY count DESC
LIMIT 10
""")

results = cursor.fetchall()
for i, row in enumerate(results, 1):
    print(f"{i:>2}. {row[0]:<50} {row[1]:>6} papers")

print()
print("=" * 80)
print("✅ ANÁLISE OTIMIZADA CONCLUÍDA")
print("=" * 80)
print()
print("💡 Próximo passo: Análise detalhada por região com queries otimizadas")
print()

cursor.close()
conn.close()
