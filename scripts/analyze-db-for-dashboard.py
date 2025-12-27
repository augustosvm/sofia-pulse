#!/usr/bin/env python3
"""
Analisa o banco de dados PostgreSQL para identificar dados disponíveis
e recomendar dashboards para o frontend do Sofia Pulse
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Configuração do banco
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'sofia_db'),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', ''),
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def analyze_tables(conn):
    """Lista todas as tabelas e contagem de registros"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Buscar todas as tabelas do schema sofia
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'sofia' 
        ORDER BY table_name
    """)
    tables = cur.fetchall()
    
    print("=" * 80)
    print("TABELAS DISPONÍVEIS NO BANCO DE DADOS")
    print("=" * 80)
    
    table_stats = []
    
    for table in tables:
        table_name = table['table_name']
        
        # Contar registros
        try:
            cur.execute(f"SELECT COUNT(*) as count FROM sofia.{table_name}")
            count = cur.fetchone()['count']
            
            # Verificar se tem colunas geográficas
            cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'sofia' 
                AND table_name = '{table_name}'
                AND (column_name LIKE '%lat%' OR column_name LIKE '%lon%' 
                     OR column_name LIKE '%city%' OR column_name LIKE '%country%'
                     OR column_name LIKE '%location%')
            """)
            geo_cols = [row['column_name'] for row in cur.fetchall()]
            
            table_stats.append({
                'name': table_name,
                'count': count,
                'has_geo': len(geo_cols) > 0,
                'geo_cols': geo_cols
            })
            
        except Exception as e:
            print(f"  ⚠️  {table_name}: Erro ao analisar - {str(e)[:50]}")
    
    # Ordenar por contagem de registros
    table_stats.sort(key=lambda x: x['count'], reverse=True)
    
    print("\nTOP 20 TABELAS POR VOLUME DE DADOS:")
    print("-" * 80)
    for i, stat in enumerate(table_stats[:20], 1):
        geo_indicator = "🗺️" if stat['has_geo'] else "  "
        print(f"{i:2}. {geo_indicator} {stat['name']:40} {stat['count']:>10,} registros")
        if stat['has_geo']:
            print(f"      Colunas geo: {', '.join(stat['geo_cols'])}")
    
    print("\n" + "=" * 80)
    print(f"TOTAL: {len(table_stats)} tabelas, {sum(s['count'] for s in table_stats):,} registros")
    print(f"Tabelas com dados geográficos: {sum(1 for s in table_stats if s['has_geo'])}")
    print("=" * 80)
    
    cur.close()
    return table_stats

def analyze_geographic_data(conn):
    """Analisa dados geográficos disponíveis para mapas"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n" + "=" * 80)
    print("DADOS GEOGRÁFICOS PARA MAPAS")
    print("=" * 80)
    
    # 1. Funding por cidade
    try:
        cur.execute("""
            SELECT
                ci.name as city,
                co.common_name as country,
                COUNT(*) as deals,
                SUM(f.amount_usd) as total_funding
            FROM sofia.funding_rounds f
            LEFT JOIN sofia.cities ci ON f.city_id = ci.id
            LEFT JOIN sofia.countries co ON f.country_id = co.id
            WHERE ci.name IS NOT NULL
            GROUP BY ci.id, ci.name, co.id, co.common_name
            ORDER BY total_funding DESC NULLS LAST
            LIMIT 20
        """)
        funding_cities = cur.fetchall()

        print("\n1. FUNDING POR CIDADE (Top 20):")
        print("-" * 80)
        for i, row in enumerate(funding_cities, 1):
            funding = f"${row['total_funding']/1e6:.1f}M" if row['total_funding'] else "N/A"
            print(f"{i:2}. {row['city']:25} {row['country']:20} {row['deals']:3} deals  {funding:>12}")
    except Exception as e:
        print(f"⚠️  Funding por cidade: {str(e)[:100]}")
    
    # 2. Papers por tópico (research areas)
    try:
        cur.execute("""
            SELECT
                COUNT(*) as total_papers,
                COUNT(DISTINCT doi) as unique_dois
            FROM sofia.openalex_papers
        """)
        papers_stats = cur.fetchone()

        print("\n2. PAPERS ACADÊMICOS (OpenAlex):")
        print("-" * 80)
        print(f"Total de papers: {papers_stats['total_papers']:,}")
        print(f"DOIs únicos: {papers_stats['unique_dois']:,}")
    except Exception as e:
        print(f"⚠️  Papers stats: {str(e)[:100]}")
    
    # 3. Dados socioeconômicos por país
    try:
        cur.execute("""
            SELECT
                c.common_name as country_name,
                COUNT(DISTINCT s.indicator_code) as indicators,
                COUNT(*) as data_points
            FROM sofia.socioeconomic_indicators s
            JOIN sofia.countries c ON s.country_id = c.id
            GROUP BY c.id, c.common_name
            ORDER BY data_points DESC
            LIMIT 20
        """)
        socio_countries = cur.fetchall()

        print("\n3. DADOS SOCIOECONÔMICOS POR PAÍS (Top 20):")
        print("-" * 80)
        for i, row in enumerate(socio_countries, 1):
            print(f"{i:2}. {row['country_name']:35} {row['indicators']:3} indicadores  {row['data_points']:>6,} pontos")
    except Exception as e:
        print(f"⚠️  Dados socioeconômicos: {str(e)[:100]}")
    
    cur.close()

def recommend_dashboards(table_stats):
    """Recomenda dashboards baseado nos dados disponíveis"""
    
    print("\n" + "=" * 80)
    print("RECOMENDAÇÕES DE DASHBOARDS PARA O FRONTEND")
    print("=" * 80)
    
    # Encontrar tabelas relevantes
    funding_tables = [t for t in table_stats if 'funding' in t['name'].lower()]
    paper_tables = [t for t in table_stats if 'paper' in t['name'].lower() or 'arxiv' in t['name'].lower()]
    socio_tables = [t for t in table_stats if 'socioeconomic' in t['name'].lower()]
    github_tables = [t for t in table_stats if 'github' in t['name'].lower()]
    geo_tables = [t for t in table_stats if t['has_geo']]
    
    print("\n🎯 DASHBOARD 1: OVERVIEW / HOME")
    print("-" * 80)
    print("Componentes:")
    print("  • KPI Cards: Total funding, Total papers, Total repos, Countries")
    print("  • Line Chart: Funding trends (últimos 90 dias)")
    print("  • Bar Chart: Top 10 tech trends")
    print("  • Table: Latest funding rounds (últimos 10)")
    print(f"Dados disponíveis: {sum(t['count'] for t in funding_tables):,} funding rounds")
    
    print("\n🗺️  DASHBOARD 2: MAPA INTERATIVO GLOBAL")
    print("-" * 80)
    print("Componentes:")
    print("  • Mapa mundial com markers por cidade")
    print("  • Layers:")
    print("    - Funding rounds (tamanho do marker = volume)")
    print("    - Research hubs (universidades com mais papers)")
    print("    - Socioeconomic indicators (heatmap)")
    print("  • Sidebar: Filtros por setor, período, tipo de dado")
    print("  • Popup: Detalhes ao clicar (funding, papers, indicadores)")
    print(f"Dados disponíveis: {len(geo_tables)} tabelas com dados geográficos")
    print("Tecnologia sugerida: Leaflet.js ou Mapbox GL JS")
    
    print("\n📈 DASHBOARD 3: TECH TRENDS & ANALYTICS")
    print("-" * 80)
    print("Componentes:")
    print("  • Top 10 Tech Trends (ranking com scores)")
    print("  • GitHub Trending (repos mais quentes)")
    print("  • Papers recentes (ArXiv + OpenAlex)")
    print("  • Correlação Papers ↔ Funding (scatter plot)")
    print(f"Dados disponíveis: {sum(t['count'] for t in github_tables):,} repos GitHub")
    
    print("\n💰 DASHBOARD 4: FUNDING & INVESTMENT")
    print("-" * 80)
    print("Componentes:")
    print("  • Funding por setor (pie chart)")
    print("  • Timeline de deals (últimos 90 dias)")
    print("  • Top investors (quem está investindo)")
    print("  • Geographic distribution (mapa de calor)")
    print("  • Dark Horses (oportunidades escondidas)")
    print(f"Dados disponíveis: {sum(t['count'] for t in funding_tables):,} funding rounds")
    
    print("\n🌍 DASHBOARD 5: SOCIOECONOMIC INTELLIGENCE")
    print("-" * 80)
    print("Componentes:")
    print("  • Best Cities for Tech Talent (ranking)")
    print("  • Remote Work Quality Index (mapa)")
    print("  • Innovation Hubs (scatter plot)")
    print("  • Cross-correlations (heatmap)")
    print(f"Dados disponíveis: {sum(t['count'] for t in socio_tables):,} indicadores")
    
    print("\n🔮 DASHBOARD 6: PREDICTIVE INSIGHTS")
    print("-" * 80)
    print("Componentes:")
    print("  • Career Trends Predictor (skills emergentes)")
    print("  • Capital Flow Predictor (setores quentes)")
    print("  • Dying Sectors (tecnologias em declínio)")
    print("  • Weekly Insights (para colunistas)")
    print("Dados: Analytics gerados diariamente (arquivos TXT)")
    
    print("\n" + "=" * 80)
    print("PRIORIDADE DE IMPLEMENTAÇÃO:")
    print("=" * 80)
    print("1. 🎯 Dashboard Overview (essencial, visão geral)")
    print("2. 🗺️  Mapa Interativo (diferencial, visual impactante)")
    print("3. 📈 Tech Trends (core value, dados únicos)")
    print("4. 💰 Funding & Investment (para investidores)")
    print("5. 🌍 Socioeconomic (para empresas/job seekers)")
    print("6. 🔮 Predictive Insights (premium, IA)")

def main():
    try:
        conn = get_connection()
        print("✅ Conectado ao banco de dados PostgreSQL")
        
        # Analisar tabelas
        table_stats = analyze_tables(conn)
        
        # Analisar dados geográficos
        analyze_geographic_data(conn)
        
        # Recomendar dashboards
        recommend_dashboards(table_stats)
        
        conn.close()
        print("\n✅ Análise concluída!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
