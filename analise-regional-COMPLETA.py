#!/usr/bin/env python3
"""
Sofia Pulse - Análise Regional COMPLETA de Papers
Usando person_papers (221K) + global_universities_progress (country_code)
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

print("🚀 Sofia Pulse - Análise Regional COMPLETA de Papers")
print("=" * 80)
print()

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

print("📡 Conectado ao banco de dados!")
print()

# 1. Criar função de mapeamento
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

# 2. Estatísticas gerais por região usando person_papers
print("=" * 80)
print("📊 ESTATÍSTICAS GERAIS POR REGIÃO (person_papers + universities)")
print("=" * 80)
print()

cursor.execute("""
WITH papers_by_institution AS (
  SELECT 
    pp.id,
    pp.fields,
    gu.country_code,
    map_country_to_region(gu.country_code) as region
  FROM sofia.person_papers pp
  JOIN sofia.global_universities_progress gu 
    ON pp.paper_source = 'global_university'
  WHERE gu.country_code IS NOT NULL
  
  UNION ALL
  
  SELECT 
    pp.id,
    pp.fields,
    'BR' as country_code,
    'Brasil' as region
  FROM sofia.person_papers pp
  WHERE pp.paper_source = 'brazilian_university'
)
SELECT 
  CASE region
    WHEN 'Brasil' THEN '🇧🇷 Brasil'
    WHEN 'América do Norte' THEN '🇺🇸 América do Norte'
    WHEN 'Europa' THEN '🇪🇺 Europa'
    WHEN 'Ásia' THEN '🌏 Ásia'
    WHEN 'Oceania' THEN '🇦🇺 Oceania'
  END AS regiao,
  COUNT(DISTINCT id) AS papers,
  ROUND(COUNT(DISTINCT id)::NUMERIC * 100.0 / SUM(COUNT(DISTINCT id)) OVER (), 2) AS pct
FROM papers_by_institution
WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania')
GROUP BY region
ORDER BY papers DESC;
""")

results = cursor.fetchall()
for row in results:
    print(f"{row[0]:<25} {row[1]:>10} papers  {row[2]:>6}%")

print()

# 3. Top 5 assuntos por região
print("=" * 80)
print("📊 TOP 5 ASSUNTOS POR REGIÃO")
print("=" * 80)
print()

cursor.execute("""
WITH papers_by_institution AS (
  SELECT 
    pp.id,
    pp.fields,
    gu.country_code,
    map_country_to_region(gu.country_code) as region
  FROM sofia.person_papers pp
  JOIN sofia.global_universities_progress gu 
    ON pp.paper_source = 'global_university'
  WHERE gu.country_code IS NOT NULL
  
  UNION ALL
  
  SELECT 
    pp.id,
    pp.fields,
    'BR' as country_code,
    'Brasil' as region
  FROM sofia.person_papers pp
  WHERE pp.paper_source = 'brazilian_university'
),
region_fields AS (
  SELECT 
    region,
    UNNEST(fields) as field,
    COUNT(DISTINCT id) AS paper_count,
    ROUND(COUNT(DISTINCT id)::NUMERIC * 100.0 / SUM(COUNT(DISTINCT id)) OVER (PARTITION BY region), 2) AS percentage
  FROM papers_by_institution
  WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania')
    AND fields IS NOT NULL
  GROUP BY region, field
),
ranked_fields AS (
  SELECT 
    region,
    field,
    paper_count,
    percentage,
    ROW_NUMBER() OVER (PARTITION BY region ORDER BY paper_count DESC) AS rank
  FROM region_fields
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
  field,
  paper_count,
  percentage
FROM ranked_fields
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
    print(f"  {row[1]}. {row[2]:<45} {row[3]:>8} papers ({row[4]:>5}%)")

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
