#!/usr/bin/env python3
"""
Sofia Pulse - Qual assunto de IA está EM EVIDÊNCIA em cada REGIÃO?
Mostra o TOP assunto de IA em cada região
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

print("🚀 Sofia Pulse - Assunto de IA EM EVIDÊNCIA por REGIÃO")
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

print("=" * 80)
print("📊 TOP 5 ASSUNTOS DE IA EM CADA REGIÃO")
print("=" * 80)
print()

# Query para pegar top 5 keywords de IA em cada região
cursor.execute("""
WITH papers_by_region AS (
    SELECT 
        pp.id,
        pp.keywords,
        map_country_to_region(gu.country_code) as region
    FROM sofia.person_papers pp
    JOIN sofia.global_universities_progress gu 
      ON pp.paper_source = 'global_university'
    WHERE pp.keywords IS NOT NULL
      AND gu.country_code IS NOT NULL
      AND (
        pp.keywords::text ILIKE '%artificial intelligence%' OR
        pp.keywords::text ILIKE '%machine learning%' OR
        pp.keywords::text ILIKE '%deep learning%' OR
        pp.keywords::text ILIKE '%computer vision%' OR
        pp.keywords::text ILIKE '%natural language%' OR
        pp.keywords::text ILIKE '%quantum%' OR
        pp.keywords::text ILIKE '%blockchain%' OR
        pp.keywords::text ILIKE '%climate%'
      )
    
    UNION ALL
    
    SELECT 
        pp.id,
        pp.keywords,
        'Brasil' as region
    FROM sofia.person_papers pp
    WHERE pp.paper_source = 'brazilian_university'
      AND pp.keywords IS NOT NULL
      AND (
        pp.keywords::text ILIKE '%artificial intelligence%' OR
        pp.keywords::text ILIKE '%machine learning%' OR
        pp.keywords::text ILIKE '%deep learning%' OR
        pp.keywords::text ILIKE '%computer vision%' OR
        pp.keywords::text ILIKE '%natural language%' OR
        pp.keywords::text ILIKE '%quantum%' OR
        pp.keywords::text ILIKE '%blockchain%' OR
        pp.keywords::text ILIKE '%climate%'
      )
),
keywords_by_region AS (
    SELECT 
        region,
        UNNEST(keywords) as keyword,
        COUNT(DISTINCT id) as papers,
        ROUND(COUNT(DISTINCT id)::NUMERIC * 100.0 / SUM(COUNT(DISTINCT id)) OVER (PARTITION BY region), 2) as pct_region
    FROM papers_by_region
    WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania', 'África')
    GROUP BY region, keyword
),
ranked_keywords AS (
    SELECT 
        region,
        keyword,
        papers,
        pct_region,
        ROW_NUMBER() OVER (PARTITION BY region ORDER BY papers DESC) as rank
    FROM keywords_by_region
    WHERE keyword IN (
        'Artificial intelligence', 'Machine learning', 'Deep learning',
        'Computer vision', 'Natural language processing', 'NLP',
        'Quantum', 'Quantum computing', 'Quantum chemistry',
        'Climate change', 'Global warming', 'Environmental science',
        'Blockchain', 'Cryptocurrency'
    )
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
    keyword,
    papers,
    pct_region
FROM ranked_keywords
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

for row in results:
    if row[0] != current_region:
        if current_region is not None:
            print()
        current_region = row[0]
        print(f"\n{row[0]}")
        print("-" * 80)
    
    print(f"  {row[1]}. {row[2]:<40} {row[3]:>6} papers ({row[4]:>5}% da região)")

print()
print("=" * 80)
print("✅ ANÁLISE CONCLUÍDA")
print("=" * 80)
print()
print("💡 Agora você pode ver qual assunto de IA está em evidência em cada região!")
print()

cursor.close()
conn.close()
