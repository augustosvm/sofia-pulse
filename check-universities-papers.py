#!/usr/bin/env python3
"""Verificar duplicatas de universidades e papers"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or 'localhost',
    'port': os.getenv('POSTGRES_PORT') or '5432',
    'user': os.getenv('POSTGRES_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or 'sofia_db',
}

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("=" * 80)
    print("🔍 VERIFICANDO DUPLICATAS: UNIVERSIDADES E PAPERS")
    print("=" * 80)
    print()
    
    # Tabelas relacionadas a universidades/instituições
    print("📚 TABELAS DE UNIVERSIDADES/INSTITUIÇÕES:")
    print()
    
    university_tables = [
        'brazil_research_institutions',
        'global_research_institutions',
        'institutions'
    ]
    
    for table in university_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
            count = cur.fetchone()[0]
            
            cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema='sofia' AND table_name='{table}'
                ORDER BY ordinal_position
                LIMIT 10
            """)
            cols = [row[0] for row in cur.fetchall()]
            
            print(f"📋 {table}")
            print(f"   Registros: {count:,}")
            print(f"   Colunas: {', '.join(cols[:5])}...")
            print()
        except Exception as e:
            print(f"❌ {table}: {str(e)}\n")
    
    # Tabelas relacionadas a papers
    print("=" * 80)
    print("📄 TABELAS DE PAPERS:")
    print("=" * 80)
    print()
    
    paper_tables = [
        'papers',
        'paper_authors',
        'authors'
    ]
    
    for table in paper_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
            count = cur.fetchone()[0]
            
            cur.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema='sofia' AND table_name='{table}'
                ORDER BY ordinal_position
                LIMIT 10
            """)
            cols = [row[0] for row in cur.fetchall()]
            
            print(f"📋 {table}")
            print(f"   Registros: {count:,}")
            print(f"   Colunas: {', '.join(cols[:5])}...")
            print()
        except Exception as e:
            print(f"❌ {table}: {str(e)}\n")
    
    # Verificar se há overlap
    print("=" * 80)
    print("🔍 ANÁLISE DE OVERLAP:")
    print("=" * 80)
    print()
    
    # Instituições
    print("📚 INSTITUIÇÕES:")
    try:
        cur.execute("""
            SELECT 
                'brazil_research_institutions' as table_name,
                COUNT(*) as total,
                COUNT(DISTINCT name) as unique_names
            FROM sofia.brazil_research_institutions
            UNION ALL
            SELECT 
                'global_research_institutions',
                COUNT(*),
                COUNT(DISTINCT name)
            FROM sofia.global_research_institutions
            UNION ALL
            SELECT 
                'institutions',
                COUNT(*),
                COUNT(DISTINCT name)
            FROM sofia.institutions
        """)
        
        for row in cur.fetchall():
            print(f"  {row[0]:40s} {row[1]:>10,} total  {row[2]:>10,} únicos")
        
    except Exception as e:
        print(f"  Erro: {e}")
    
    print()
    
    # Papers
    print("📄 PAPERS:")
    try:
        cur.execute("""
            SELECT 
                COUNT(*) as total_papers,
                COUNT(DISTINCT title) as unique_titles,
                COUNT(DISTINCT doi) as unique_dois
            FROM sofia.papers
        """)
        
        row = cur.fetchone()
        print(f"  Total papers: {row[0]:,}")
        print(f"  Títulos únicos: {row[1]:,}")
        print(f"  DOIs únicos: {row[2]:,}")
        
    except Exception as e:
        print(f"  Erro: {e}")
    
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ Verificação completa!")
    print("=" * 80)

if __name__ == '__main__':
    main()
