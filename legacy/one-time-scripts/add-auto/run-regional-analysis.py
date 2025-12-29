#!/usr/bin/env python3
"""
Sofia Pulse - Script de Análise Regional de Papers

Executa as queries SQL de análise regional e mostra os resultados formatados.
"""

import psycopg2
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do banco
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost')),
    'port': int(os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432'))),
    'user': os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'postgres')),
    'password': os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', 'postgres')),
    'database': os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'sofia_db'))
}

# ============================================================================
# FUNÇÃO DE MAPEAMENTO DE PAÍSES PARA REGIÕES
# ============================================================================

CREATE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION map_country_to_region(country_code TEXT)
RETURNS TEXT AS $$
BEGIN
  -- Brasil
  IF country_code = 'BR' THEN
    RETURN 'Brasil';
  
  -- América do Norte
  ELSIF country_code IN ('US', 'CA', 'MX') THEN
    RETURN 'América do Norte';
  
  -- Europa
  ELSIF country_code IN (
    'GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 
    'NO', 'DK', 'FI', 'IE', 'PT', 'GR', 'PL', 'CZ', 'HU', 'RO',
    'BG', 'HR', 'SI', 'SK', 'LT', 'LV', 'EE', 'CY', 'MT', 'LU',
    'IS', 'LI', 'MC', 'AD', 'SM', 'VA', 'AL', 'BA', 'MK', 'ME',
    'RS', 'XK', 'MD', 'UA', 'BY', 'RU'
  ) THEN
    RETURN 'Europa';
  
  -- Ásia
  ELSIF country_code IN (
    'CN', 'JP', 'KR', 'IN', 'SG', 'HK', 'TW', 'TH', 'MY', 'ID',
    'PH', 'VN', 'BD', 'PK', 'LK', 'MM', 'KH', 'LA', 'BN', 'MN',
    'NP', 'BT', 'MV', 'AF', 'IR', 'IQ', 'SA', 'AE', 'IL', 'TR',
    'JO', 'LB', 'SY', 'YE', 'OM', 'KW', 'QA', 'BH', 'PS', 'AM',
    'AZ', 'GE', 'KZ', 'UZ', 'TM', 'TJ', 'KG'
  ) THEN
    RETURN 'Ásia';
  
  -- Oceania
  ELSIF country_code IN ('AU', 'NZ', 'FJ', 'PG', 'NC', 'PF', 'WS', 'TO', 'VU', 'SB', 'KI', 'FM', 'MH', 'PW', 'NR', 'TV') THEN
    RETURN 'Oceania';
  
  -- África
  ELSIF country_code IN (
    'ZA', 'EG', 'NG', 'KE', 'ET', 'GH', 'TZ', 'UG', 'DZ', 'MA',
    'AO', 'SD', 'MZ', 'MG', 'CM', 'CI', 'NE', 'BF', 'ML', 'MW',
    'ZM', 'SN', 'SO', 'TD', 'GN', 'RW', 'BJ', 'TN', 'BI', 'SS',
    'TG', 'SL', 'LY', 'LR', 'MR', 'CF', 'ER', 'GM', 'BW', 'GA',
    'GW', 'GQ', 'MU', 'SZ', 'DJ', 'RE', 'KM', 'CV', 'ST', 'SC'
  ) THEN
    RETURN 'África';
  
  -- América Latina (exceto Brasil)
  ELSIF country_code IN (
    'AR', 'CL', 'CO', 'PE', 'VE', 'EC', 'BO', 'PY', 'UY', 'GY',
    'SR', 'GF', 'CR', 'PA', 'CU', 'DO', 'GT', 'HN', 'SV', 'NI',
    'BZ', 'JM', 'TT', 'BS', 'BB', 'LC', 'GD', 'VC', 'AG', 'DM',
    'KN', 'HT', 'PR', 'VI', 'AW', 'CW', 'BQ', 'SX', 'MF', 'BL'
  ) THEN
    RETURN 'América Latina';
  
  ELSE
    RETURN 'Outros';
  END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
"""

# ============================================================================
# QUERY: ASSUNTO #1 POR REGIÃO (VALIDAÇÃO RÁPIDA)
# ============================================================================

TOP_1_PER_REGION_SQL = """
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
    SUM(p.cited_by_count) AS total_citations,
    ROUND(
      COUNT(DISTINCT p.id)::NUMERIC * 100.0 / 
      SUM(COUNT(DISTINCT p.id)) OVER (PARTITION BY region),
      2
    ) AS percentage
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
    total_citations,
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
  percentage AS percentual,
  total_citations AS citacoes
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
"""

# ============================================================================
# QUERY: TOP 5 ASSUNTOS POR REGIÃO
# ============================================================================

TOP_5_PER_REGION_SQL = """
WITH papers_with_regions AS (
  SELECT 
    p.id,
    p.cited_by_count,
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
    SUM(p.cited_by_count) AS total_citations,
    ROUND(
      COUNT(DISTINCT p.id)::NUMERIC * 100.0 / 
      SUM(COUNT(DISTINCT p.id)) OVER (PARTITION BY region),
      2
    ) AS percentage
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
    total_citations,
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
  rank AS ranking,
  concept AS assunto,
  paper_count AS papers,
  percentage AS percentual,
  total_citations AS citacoes
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
"""

# ============================================================================
# QUERY: ESTATÍSTICAS GERAIS POR REGIÃO
# ============================================================================

STATS_PER_REGION_SQL = """
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
    WHEN 'América Latina' THEN '🌎 América Latina'
    WHEN 'África' THEN '🌍 África'
  END AS regiao,
  COUNT(DISTINCT p.id) AS total_papers,
  SUM(p.cited_by_count) AS total_citacoes,
  AVG(p.cited_by_count)::INT AS media_citacoes,
  ROUND(
    COUNT(DISTINCT p.id)::NUMERIC * 100.0 / 
    SUM(COUNT(DISTINCT p.id)) OVER (),
    2
  ) AS percentual_global
FROM papers_with_regions p
CROSS JOIN UNNEST(p.regions) AS region
WHERE region IN ('Brasil', 'América do Norte', 'Europa', 'Ásia', 'Oceania', 'América Latina', 'África')
GROUP BY region
ORDER BY total_papers DESC;
"""

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def format_table(rows, headers):
    """Formata resultados em tabela ASCII simples"""
    if not rows:
        return "Nenhum resultado"
    
    # Converter todos os valores para string
    str_rows = [[str(val) if val is not None else '' for val in row] for row in rows]
    
    # Calcular largura de cada coluna
    col_widths = [len(h) for h in headers]
    for row in str_rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))
    
    # Criar linha separadora
    separator = '+' + '+'.join(['-' * (w + 2) for w in col_widths]) + '+'
    
    # Criar header
    header_line = '|' + '|'.join([f' {h:<{col_widths[i]}} ' for i, h in enumerate(headers)]) + '|'
    
    # Criar linhas de dados
    data_lines = []
    for row in str_rows:
        line = '|' + '|'.join([f' {val:>{col_widths[i]}} ' for i, val in enumerate(row)]) + '|'
        data_lines.append(line)
    
    # Montar tabela
    table = [separator, header_line, separator] + data_lines + [separator]
    return '\n'.join(table)

def connect_db():
    """Conecta ao banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        print(f"\n💡 Verifique as variáveis de ambiente no arquivo .env")
        print(f"   Host: {DB_CONFIG['host']}")
        print(f"   Port: {DB_CONFIG['port']}")
        print(f"   Database: {DB_CONFIG['database']}")
        return None

def create_mapping_function(conn):
    """Cria a função de mapeamento de países para regiões"""
    try:
        cursor = conn.cursor()
        cursor.execute(CREATE_FUNCTION_SQL)
        conn.commit()
        cursor.close()
        print("✅ Função map_country_to_region() criada com sucesso")
        return True
    except Exception as e:
        print(f"⚠️  Aviso ao criar função: {e}")
        print("   (Pode ser que a função já exista, continuando...)")
        return True

def run_query(conn, query, title):
    """Executa uma query e mostra os resultados formatados"""
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        
        if not results:
            print(f"\n⚠️  {title}: Nenhum resultado encontrado")
            return
        
        print(f"\n{'=' * 80}")
        print(f"📊 {title}")
        print(f"{'=' * 80}\n")
        
        # Formatar resultados em tabela
        print(format_table(results, columns))
        print(f"\n✅ Total de resultados: {len(results)}")
        
    except Exception as e:
        print(f"\n❌ Erro ao executar query: {e}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("🚀 Sofia Pulse - Análise Regional de Papers")
    print("=" * 80)
    print()
    
    # Conectar ao banco
    print("📡 Conectando ao banco de dados...")
    conn = connect_db()
    if not conn:
        return
    
    print(f"✅ Conectado a: {DB_CONFIG['database']} @ {DB_CONFIG['host']}")
    print()
    
    # Criar função de mapeamento
    print("🔧 Criando função de mapeamento de países para regiões...")
    if not create_mapping_function(conn):
        print("❌ Não foi possível criar a função. Abortando.")
        conn.close()
        return
    
    # Executar queries
    print("\n" + "=" * 80)
    print("📊 EXECUTANDO ANÁLISES")
    print("=" * 80)
    
    # 1. Estatísticas gerais
    run_query(conn, STATS_PER_REGION_SQL, "ESTATÍSTICAS GERAIS POR REGIÃO")
    
    # 2. Assunto #1 por região
    run_query(conn, TOP_1_PER_REGION_SQL, "ASSUNTO #1 MAIS CITADO POR REGIÃO")
    
    # 3. Top 5 por região
    run_query(conn, TOP_5_PER_REGION_SQL, "TOP 5 ASSUNTOS MAIS CITADOS POR REGIÃO")
    
    # Fechar conexão
    conn.close()
    
    print("\n" + "=" * 80)
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
    print("   Compare os resultados acima com estes dados fornecidos!")
    print()

if __name__ == "__main__":
    main()
