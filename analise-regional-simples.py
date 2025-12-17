#!/usr/bin/env python3
"""
Sofia Pulse - Análise Regional de Papers (SEM DEPENDÊNCIAS)
"""

import psycopg2

# Configuração direta do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'sofia',
    'password': 'your_password_here',  # Será lido do .env manualmente
    'database': 'sofia_db'
}

# Ler senha do .env
try:
    with open('/home/ubuntu/sofia-pulse/.env', 'r') as f:
        for line in f:
            if line.startswith('POSTGRES_PASSWORD='):
                DB_CONFIG['password'] = line.split('=', 1)[1].strip()
                break
except:
    pass

print("🚀 Sofia Pulse - Análise Regional de Papers")
print("=" * 80)
print()

# Conectar
try:
    print(f"📡 Conectando ao banco de dados...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("✅ Conectado!")
    print()
except Exception as e:
    print(f"❌ Erro: {e}")
    exit(1)

# 1. Criar função
print("🔧 Criando função de mapeamento...")
cursor.execute("""
CREATE OR REPLACE FUNCTION map_country_to_region(country_code TEXT)
RETURNS TEXT AS $$
BEGIN
  IF country_code = 'BR' THEN RETURN 'Brasil';
  ELSIF country_code IN ('US', 'CA', 'MX') THEN RETURN 'América do Norte';
  ELSIF country_code IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'IE', 'PT', 'GR', 'PL', 'CZ', 'HU', 'RO', 'BG', 'HR', 'SI', 'SK', 'LT', 'LV', 'EE', 'CY', 'MT', 'LU', 'IS', 'LI', 'MC', 'AD', 'SM', 'VA', 'AL', 'BA', 'MK', 'ME', 'RS', 'XK', 'MD', 'UA', 'BY', 'RU') THEN RETURN 'Europa';
  ELSIF country_code IN ('CN', 'JP', 'KR', 'IN', 'SG', 'HK', 'TW', 'TH', 'MY', 'ID', 'PH', 'VN', 'BD', 'PK', 'LK', 'MM', 'KH', 'LA', 'BN', 'MN', 'NP', 'BT', 'MV', 'AF', 'IR', 'IQ', 'SA', 'AE', 'IL', 'TR', 'JO', 'LB', 'SY', 'YE', 'OM', 'KW', 'QA', 'BH', 'PS', 'AM', 'AZ', 'GE', 'KZ', 'UZ', 'TM', 'TJ', 'KG') THEN RETURN 'Ásia';
  ELSIF country_code IN ('AU', 'NZ', 'FJ', 'PG', 'NC', 'PF', 'WS', 'TO', 'VU', 'SB', 'KI', 'FM', 'MH', 'PW', 'NR', 'TV') THEN RETURN 'Oceania';
  ELSE RETURN 'Outros';
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
""")
conn.commit()
print("✅ Função criada!")
print()

# 2. Estatísticas gerais
print("=" * 80)
print("📊 ESTATÍSTICAS GERAIS POR REGIÃO")
print("=" * 80)
print()

cursor.execute("""
WITH papers_with_regions AS (
  SELECT 
    p.id,
    p.cited_by_count,
    ARRAY(
      SELECT DISTINCT map_country_to_region(country)
      FROM UNNEST(p.author_countries) AS country
    ) AS regions
  FROM openalex_papers p
  WHERE p.author_countries IS NOT NULL 
    AND array_length(p.author_countries, 1) > 0
    AND p.publication_year >= 2020
)
SELECT 
  CASE region
    WHEN 'Brasil' THEN '🇧🇷 Brasil'
    WHEN 'América do Norte' THEN '🇺🇸 América do Norte'
    WHEN 'Europa' THEN '🇪🇺 Europa'
    WHEN 'Ásia' THEN '🌏 Ásia'
    WHEN 'Oceania' THEN '🇦🇺 Oceania'
  END AS regiao,
  COUNT(DISTINCT p.id) AS papers,
  SUM(p.cited_by_count) AS citacoes,
  AVG(p.cited_by_count)::INT AS media,
  ROUND(COUNT(DISTINCT p.id)::NUMERIC * 100.0 / SUM(COUNT(DISTINCT p.id)) OVER (), 2) AS pct
FROM papers_with_regions p
CROSS JOIN UNNEST(p.regions) AS region
WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania')
GROUP BY region
ORDER BY papers DESC;
""")

results = cursor.fetchall()
for row in results:
    print(f"{row[0]:<25} {row[1]:>8} papers  {row[2]:>10} citações  {row[3]:>5} média  {row[4]:>6}%")

print()

# 3. Assunto #1 por região
print("=" * 80)
print("📊 ASSUNTO #1 MAIS CITADO POR REGIÃO")
print("=" * 80)
print()

cursor.execute("""
WITH papers_with_regions AS (
  SELECT 
    p.id,
    p.cited_by_count,
    p.primary_concept,
    ARRAY(
      SELECT DISTINCT map_country_to_region(country)
      FROM UNNEST(p.author_countries) AS country
    ) AS regions
  FROM openalex_papers p
  WHERE p.author_countries IS NOT NULL 
    AND array_length(p.author_countries, 1) > 0
    AND p.publication_year >= 2020
),
region_stats AS (
  SELECT 
    region,
    primary_concept,
    COUNT(DISTINCT p.id) AS paper_count,
    ROUND(COUNT(DISTINCT p.id)::NUMERIC * 100.0 / SUM(COUNT(DISTINCT p.id)) OVER (PARTITION BY region), 2) AS percentage
  FROM papers_with_regions p
  CROSS JOIN UNNEST(p.regions) AS region
  WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania')
  GROUP BY region, primary_concept
),
top_per_region AS (
  SELECT 
    region,
    primary_concept,
    paper_count,
    percentage,
    ROW_NUMBER() OVER (PARTITION BY region ORDER BY paper_count DESC) AS rank
  FROM region_stats
)
SELECT 
  CASE region
    WHEN 'Brasil' THEN '🇧🇷 Brasil'
    WHEN 'América do Norte' THEN '🇺🇸 América do Norte'
    WHEN 'Europa' THEN '🇪🇺 Europa'
    WHEN 'Ásia' THEN '🌏 Ásia'
    WHEN 'Oceania' THEN '🇦🇺 Oceania'
  END AS regiao,
  primary_concept AS assunto,
  paper_count AS papers,
  percentage AS pct
FROM top_per_region
WHERE rank = 1
ORDER BY 
  CASE region
    WHEN 'Brasil' THEN 1
    WHEN 'América do Norte' THEN 2
    WHEN 'Europa' THEN 3
    WHEN 'Ásia' THEN 4
    WHEN 'Oceania' THEN 5
  END;
""")

results = cursor.fetchall()
for row in results:
    print(f"{row[0]:<25} {row[1]:<40} {row[2]:>6} papers ({row[3]:>5}%)")

print()

# 4. Top 5 por região
print("=" * 80)
print("📊 TOP 5 ASSUNTOS POR REGIÃO")
print("=" * 80)
print()

cursor.execute("""
WITH papers_with_regions AS (
  SELECT 
    p.id,
    p.concepts,
    ARRAY(
      SELECT DISTINCT map_country_to_region(country)
      FROM UNNEST(p.author_countries) AS country
    ) AS regions
  FROM openalex_papers p
  WHERE p.author_countries IS NOT NULL 
    AND array_length(p.author_countries, 1) > 0
    AND p.publication_year >= 2020
),
region_concept_stats AS (
  SELECT 
    region,
    concept,
    COUNT(DISTINCT p.id) AS paper_count,
    ROUND(COUNT(DISTINCT p.id)::NUMERIC * 100.0 / SUM(COUNT(DISTINCT p.id)) OVER (PARTITION BY region), 2) AS percentage
  FROM papers_with_regions p
  CROSS JOIN UNNEST(p.regions) AS region
  CROSS JOIN UNNEST(p.concepts) AS concept
  WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania')
  GROUP BY region, concept
),
ranked_concepts AS (
  SELECT 
    region,
    concept,
    paper_count,
    percentage,
    ROW_NUMBER() OVER (PARTITION BY region ORDER BY paper_count DESC) AS rank
  FROM region_concept_stats
)
SELECT 
  CASE region
    WHEN 'Brasil' THEN '🇧🇷 Brasil'
    WHEN 'América do Norte' THEN '🇺🇸 América do Norte'
    WHEN 'Europa' THEN '🇪🇺 Europa'
    WHEN 'Ásia' THEN '🌏 Ásia'
    WHEN 'Oceania' THEN '🇦🇺 Oceania'
  END AS regiao,
  rank,
  concept AS assunto,
  paper_count AS papers,
  percentage AS pct
FROM ranked_concepts
WHERE rank <= 5
ORDER BY 
  CASE region
    WHEN 'Brasil' THEN 1
    WHEN 'América do Norte' THEN 2
    WHEN 'Europa' THEN 3
    WHEN 'Ásia' THEN 4
    WHEN 'Oceania' THEN 5
  END,
  rank;
""")

results = cursor.fetchall()
current_region = None
for row in results:
    if row[0] != current_region:
        if current_region is not None:
            print()
        current_region = row[0]
        print(f"\n{row[0]}")
        print("-" * 80)
    print(f"  {row[1]}. {row[2]:<45} {row[3]:>6} papers ({row[4]:>5}%)")

print()
print("=" * 80)
print("✅ ANÁLISE CONCLUÍDA")
print("=" * 80)
print()
print("💡 COMPARAÇÃO COM DADOS FORNECIDOS:")
print()
print("   🇧🇷 Brasil: AI Ethics - 1,234 papers - 28%")
print("   🇺🇸 América do Norte: LLMs - 5,678 papers - 42%")
print("   🇪🇺 Europa: Quantum AI - 3,456 papers - 35%")
print("   🌏 Ásia: Computer Vision - 6,789 papers - 44%")
print("   🇦🇺 Oceania: Climate AI - 892 papers - 31%")
print()

cursor.close()
conn.close()
