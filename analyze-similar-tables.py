#!/usr/bin/env python3
"""
Análise de tabelas similares para consolidação
Identifica grupos de tabelas que podem ser consolidadas em uma estrutura unificada
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or 'localhost',
    'port': os.getenv('POSTGRES_PORT') or '5432',
    'user': os.getenv('POSTGRES_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or 'sofia_db',
}

def get_table_structure(conn, table_name):
    """Retorna estrutura detalhada de uma tabela"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT 
            column_name, 
            data_type,
            character_maximum_length,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'sofia' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    
    return cur.fetchall()

def get_table_count(conn, table_name):
    """Retorna contagem de registros"""
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table_name}")
        return cur.fetchone()[0]
    except:
        return 0

def analyze_trend_tables(conn):
    """Analisa tabelas relacionadas a trends/posts/stories"""
    
    # Grupos de tabelas similares
    groups = {
        'trends': [
            'ai_github_trends',
            'stackoverflow_trends', 
            'trends',
            'tech_job_skill_trends',
            'tech_job_salary_trends'
        ],
        'posts_stories': [
            'hackernews_stories',
            'hacker_news_stories',
            'reddit_tech',
            'reddit_tech_posts'
        ],
        'patents': [
            'epo_patents',
            'patents',
            'person_patents',
            'wipo_china_patents'
        ],
        'insights': [
            'insights',
            'insights_alerts',
            'insights_anomalies',
            'insights_acceleration',
            'insights_clusters',
            'insights_correlations',
            'insights_rankings',
            'insights_variations',
            'columnist_insights'
        ]
    }
    
    print("=" * 80)
    print("📊 ANÁLISE DE GRUPOS DE TABELAS SIMILARES")
    print("=" * 80)
    print()
    
    for group_name, tables in groups.items():
        print(f"\n{'='*80}")
        print(f"🔍 GRUPO: {group_name.upper()}")
        print(f"{'='*80}\n")
        
        for table in tables:
            try:
                count = get_table_count(conn, table)
                structure = get_table_structure(conn, table)
                
                print(f"📋 {table}")
                print(f"   Registros: {count:,}")
                print(f"   Colunas: {len(structure)}")
                print(f"   Estrutura:")
                for col in structure[:10]:  # Primeiras 10 colunas
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    print(f"      - {col['column_name']:30s} {col['data_type']:20s} {nullable}")
                if len(structure) > 10:
                    print(f"      ... e mais {len(structure) - 10} colunas")
                print()
                
            except Exception as e:
                print(f"❌ {table}: Erro ao analisar - {str(e)}\n")
    
    print("\n" + "=" * 80)
    print("✅ Análise completa!")
    print("=" * 80)

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    analyze_trend_tables(conn)
    conn.close()

if __name__ == '__main__':
    main()
