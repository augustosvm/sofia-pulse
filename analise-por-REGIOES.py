#!/usr/bin/env python3
"""
Sofia Pulse - Análise Regional por REGIÕES (não países)
Brasil, América do Norte, Europa, Ásia, Oceania, África
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

print("🚀 Sofia Pulse - Análise Regional por REGIÕES")
print("=" * 80)
print()

conn = psycopg2.connect(host='localhost', port=5432, user='sofia', password=password, database='sofia_db')
cursor = conn.cursor()

print("📡 Conectado ao banco de dados!")
print()

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

# Categorias de IA
ai_categories = {
    'Artificial Intelligence': ['Artificial intelligence', 'AI'],
    'Machine Learning': ['Machine learning', 'Deep learning', 'Neural network', 'Convolutional neural network'],
    'Computer Vision': ['Computer vision', 'Image processing', 'Pattern recognition'],
    'Natural Language Processing': ['Natural language processing', 'NLP', 'Language model'],
    'Quantum Computing': ['Quantum', 'Quantum computing', 'Quantum chemistry', 'Qubit', 'Superconducting quantum'],
    'Climate AI': ['Climate change', 'Global warming', 'Environmental science', 'Climatology'],
    'Blockchain': ['Blockchain', 'Cryptocurrency', 'Bitcoin']
}

print("=" * 80)
print("📊 ANÁLISE POR REGIÃO E CATEGORIA DE IA")
print("=" * 80)
print()

for category, keywords in ai_categories.items():
    print(f"\n{'=' * 80}")
    print(f"🔍 {category}")
    print(f"{'=' * 80}\n")
    
    conditions = " OR ".join([f"pp.keywords::text ILIKE '%{kw}%'" for kw in keywords])
    
    cursor.execute(f"""
        WITH ai_papers AS (
            SELECT 
                pp.id,
                gu.country_code,
                map_country_to_region(gu.country_code) as region
            FROM sofia.person_papers pp
            JOIN sofia.global_universities_progress gu 
              ON pp.paper_source = 'global_university'
            WHERE pp.keywords IS NOT NULL
              AND ({conditions})
              AND gu.country_code IS NOT NULL
            
            UNION ALL
            
            SELECT 
                pp.id,
                'BR' as country_code,
                'Brasil' as region
            FROM sofia.person_papers pp
            WHERE pp.paper_source = 'brazilian_university'
              AND pp.keywords IS NOT NULL
              AND ({conditions})
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
            COUNT(DISTINCT id) as papers,
            ROUND(COUNT(DISTINCT id)::NUMERIC * 100.0 / SUM(COUNT(DISTINCT id)) OVER (), 2) as pct_global
        FROM ai_papers
        WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania', 'África')
        GROUP BY region
        ORDER BY papers DESC
    """)
    
    results = cursor.fetchall()
    for row in results:
        print(f"{row[0]:<25} {row[1]:>8} papers ({row[2]:>5}% do total global)")

print()
print("=" * 80)
print("✅ ANÁLISE POR REGIÃO CONCLUÍDA")
print("=" * 80)
print()

cursor.close()
conn.close()
