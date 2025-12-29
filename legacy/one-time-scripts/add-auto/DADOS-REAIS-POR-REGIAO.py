#!/usr/bin/env python3
"""
DADOS REAIS DO BANCO - Assuntos de IA por REGIÃO
Sem comparação, apenas mostrando O QUE EXISTE no banco de dados
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

print("📊 DADOS REAIS DO BANCO - Assuntos de IA por REGIÃO")
print("=" * 80)
print()

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

# Criar função de mapeamento
cursor.execute("""
CREATE OR REPLACE FUNCTION map_country_to_region(country_code TEXT)
RETURNS TEXT AS $$
BEGIN
  IF country_code = 'BR' THEN RETURN 'Brasil';
  ELSIF country_code IN ('US', 'CA', 'MX') THEN RETURN 'América do Norte';
  ELSIF country_code IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'IE', 'PT', 'GR', 'PL', 'CZ', 'HU', 'RO', 'BG', 'HR', 'SI', 'SK', 'LT', 'LV', 'EE', 'CY', 'MT', 'LU', 'IS', 'LI', 'MC', 'AD', 'SM', 'VA', 'AL', 'BA', 'MK', 'ME', 'RS', 'XK', 'MD', 'UA', 'BY', 'RU') THEN RETURN 'Europa';
  ELSIF country_code IN ('CN', 'JP', 'KR', 'IN', 'SG', 'HK', 'TW', 'TH', 'MY', 'ID', 'PH', 'VN', 'BD', 'PK', 'LK', 'MM', 'KH', 'LA', 'BN', 'MN', 'NP', 'BT', 'MV', 'AF', 'IR', 'IQ', 'SA', 'AE', 'IL', 'TR', 'JO', 'LB', 'SY', 'YE', 'OM', 'KW', 'QA', 'BH', 'PS', 'AM', 'AZ', 'GE', 'KZ', 'UZ', 'TM', 'TJ', 'KG') THEN RETURN 'Ásia';
  ELSIF country_code IN ('AU', 'NZ', 'FJ', 'PG', 'NC', 'PF', 'WS', 'TO', 'VU', 'SB', 'KI', 'FM', 'MH', 'PW', 'NR', 'TV') THEN RETURN 'Oceania';
  ELSIF country_code IN ('ZA', 'EG', 'NG', 'KE', 'ET', 'GH', 'TZ', 'UG', 'DZ', 'MA', 'AO', 'SD', 'MZ', 'MG', 'CM', 'CI', 'NE', 'BF', 'ML', 'MW', 'ZM', 'SN', 'SO', 'TD', 'GN', 'RW', 'BJ', 'TN', 'BI', 'SS', 'TG', 'SL', 'LY', 'LR', 'MR', 'CF', 'ER', 'GM', 'BW', 'GA', 'GW', 'GQ', 'MU', 'SZ', 'DJ', 'RE', 'KM', 'CV', 'ST', 'SC') THEN RETURN 'África';
  ELSE RETURN 'Outros';
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
""")
conn.commit()

# Query para pegar top 5 concepts por região (openalex_papers - dados corretos)
cursor.execute("""
WITH papers_by_region AS (
    SELECT 
        p.id,
        p.concepts,
        map_country_to_region(UNNEST(p.author_countries)) as region
    FROM openalex_papers p
    WHERE p.author_countries IS NOT NULL
      AND p.publication_year >= 2020
),
concept_by_region AS (
    SELECT 
        region,
        UNNEST(concepts) as concept,
        COUNT(DISTINCT id) as papers,
        ROUND(COUNT(DISTINCT id)::NUMERIC * 100.0 / SUM(COUNT(DISTINCT id)) OVER (PARTITION BY region), 2) as pct_region
    FROM papers_by_region
    WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania', 'África')
    GROUP BY region, concept
),
ranked_concepts AS (
    SELECT 
        region,
        concept,
        papers,
        pct_region,
        ROW_NUMBER() OVER (PARTITION BY region ORDER BY papers DESC) as rank
    FROM concept_by_region
)
SELECT 
    CASE region
        WHEN 'Brasil' THEN '🇧🇷 Brasil'
        WHEN 'América do Norte' THEN '🇺🇸 América do Norte'
        WHEN 'Europa' THEN '🇪🇺 Europa'
        WHEN 'Ásia' THEN '🌏 Ásia'
        WHEN 'Oceania' THEN '🇦🇺 Oceania'
        WHEN 'África' THEN '🌍 África'
    END AS regiao,
    rank,
    concept,
    papers,
    pct_region
FROM ranked_concepts
WHERE rank <= 5
ORDER BY 
    CASE region
        WHEN 'Brasil' THEN 1
        WHEN 'América do Norte' THEN 2
        WHEN 'Europa' THEN 3
        WHEN 'Ásia' THEN 4
        WHEN 'Oceania' THEN 5
        WHEN 'África' THEN 6
    END,
    rank
""")

results = cursor.fetchall()
current_region = None

print("TOP 5 ASSUNTOS POR REGIÃO (dados reais do banco)")
print("=" * 80)
print()

for row in results:
    if row[0] != current_region:
        if current_region is not None:
            print()
        current_region = row[0]
        print(f"\n{row[0]}")
        print("-" * 80)
    
    print(f"  {row[1]}. {row[2]:<45} {row[3]:>6} papers ({row[4]:>5}%)")

print()

# Mostrar também o #1 de cada região em formato resumido
print("=" * 80)
print("RESUMO: ASSUNTO #1 EM CADA REGIÃO")
print("=" * 80)
print()

cursor.execute("""
WITH papers_by_region AS (
    SELECT 
        p.id,
        p.concepts,
        map_country_to_region(UNNEST(p.author_countries)) as region
    FROM openalex_papers p
    WHERE p.author_countries IS NOT NULL
      AND p.publication_year >= 2020
),
concept_by_region AS (
    SELECT 
        region,
        UNNEST(concepts) as concept,
        COUNT(DISTINCT id) as papers,
        ROUND(COUNT(DISTINCT id)::NUMERIC * 100.0 / SUM(COUNT(DISTINCT id)) OVER (PARTITION BY region), 2) as pct_region
    FROM papers_by_region
    WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania', 'África')
    GROUP BY region, concept
),
ranked_concepts AS (
    SELECT 
        region,
        concept,
        papers,
        pct_region,
        ROW_NUMBER() OVER (PARTITION BY region ORDER BY papers DESC) as rank
    FROM concept_by_region
)
SELECT 
    CASE region
        WHEN 'Brasil' THEN '🇧🇷 Brasil'
        WHEN 'América do Norte' THEN '🇺🇸 América do Norte'
        WHEN 'Europa' THEN '🇪🇺 Europa'
        WHEN 'Ásia' THEN '🌏 Ásia'
        WHEN 'Oceania' THEN '🇦🇺 Oceania'
        WHEN 'África' THEN '🌍 África'
    END AS regiao,
    concept,
    papers,
    pct_region
FROM ranked_concepts
WHERE rank = 1
ORDER BY 
    CASE region
        WHEN 'Brasil' THEN 1
        WHEN 'América do Norte' THEN 2
        WHEN 'Europa' THEN 3
        WHEN 'Ásia' THEN 4
        WHEN 'Oceania' THEN 5
        WHEN 'África' THEN 6
    END
""")

for row in cursor.fetchall():
    print(f"{row[0]:<25} {row[1]:<40} {row[2]:>6} papers ({row[3]:>5}%)")

print()
print("=" * 80)
print("✅ DADOS EXTRAÍDOS DO BANCO DE DADOS")
print("=" * 80)
print()
print("Fonte: openalex_papers (2.699 papers com author_countries correto)")
print("Período: 2020-2024")
print()

cursor.close()
conn.close()
