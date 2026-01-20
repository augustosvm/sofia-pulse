#!/usr/bin/env python3
"""Cria view simplificada do Skill Gap diretamente"""
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

import psycopg2

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "database": os.getenv("POSTGRES_DB", "sofia_db"),
}

def create_skill_gap_view():
    print("=" * 60)
    print("CRIANDO SKILL GAP VIEW SIMPLIFICADA")
    print("=" * 60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        # Drop existing views se existirem
        print("\n🗑️ Removendo views antigas...")
        views_to_drop = [
            'sofia.mv_skill_gap_country_summary',
            'sofia.mv_skill_gap_by_country',
            'sofia.mv_skill_supply_by_country',
            'sofia.mv_skill_demand_by_country',
            'sofia.skill_keywords'
        ]
        for view in views_to_drop:
            try:
                cur.execute(f"DROP MATERIALIZED VIEW IF EXISTS {view} CASCADE")
                print(f"   Dropped {view}")
            except:
                try:
                    cur.execute(f"DROP VIEW IF EXISTS {view} CASCADE")
                    print(f"   Dropped view {view}")
                except:
                    pass
        
        # Criar view de keywords
        print("\n📝 Criando skill_keywords...")
        cur.execute("""
            CREATE OR REPLACE VIEW sofia.skill_keywords AS
            SELECT unnest(ARRAY[
                'python', 'javascript', 'typescript', 'java', 'golang', 'rust', 'c++',
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
                'machine learning', 'deep learning', 'artificial intelligence', 
                'data science', 'nlp', 'computer vision', 'tensorflow', 'pytorch',
                'react', 'angular', 'vue', 'node.js', 'django', 'flask',
                'sql', 'postgresql', 'mongodb', 'redis',
                'api', 'microservices', 'agile', 'blockchain', 'cybersecurity'
            ]) AS skill
        """)
        print("   ✅ skill_keywords criada")
        
        # Criar view de demanda (jobs) - usando campo skills_required existente
        print("\n📊 Criando mv_skill_demand_by_country...")
        cur.execute("""
            CREATE MATERIALIZED VIEW sofia.mv_skill_demand_by_country AS
            WITH job_skills AS (
                SELECT 
                    UPPER(SUBSTRING(COALESCE(country, 'XX'), 1, 2)) as country_code,
                    LOWER(UNNEST(skills_required)) as skill
                FROM sofia.jobs
                WHERE skills_required IS NOT NULL AND array_length(skills_required, 1) > 0
                
                UNION ALL
                
                SELECT 
                    UPPER(SUBSTRING(COALESCE(country, 'XX'), 1, 2)) as country_code,
                    LOWER(UNNEST(skills_required)) as skill
                FROM tech_jobs
                WHERE skills_required IS NOT NULL AND array_length(skills_required, 1) > 0
            ),
            skill_counts AS (
                SELECT 
                    country_code,
                    skill,
                    COUNT(*) as job_count
                FROM job_skills
                GROUP BY country_code, skill
            ),
            country_totals AS (
                SELECT country_code, COUNT(DISTINCT skill) as total_skills, COUNT(*) as total_mentions
                FROM job_skills
                GROUP BY country_code
            )
            SELECT 
                sc.country_code,
                sc.skill,
                sc.job_count,
                ct.total_mentions as total_jobs,
                ROUND((sc.job_count::numeric / NULLIF(ct.total_mentions, 0)) * 100, 2) as demand_pct
            FROM skill_counts sc
            JOIN country_totals ct ON sc.country_code = ct.country_code
            WHERE sc.job_count >= 2
        """)
        print("   ✅ mv_skill_demand_by_country criada (usando skills_required)")
        
        # Criar view de supply (papers)
        print("\n📚 Criando mv_skill_supply_by_country...")
        cur.execute("""
            CREATE MATERIALIZED VIEW sofia.mv_skill_supply_by_country AS
            WITH paper_data AS (
                SELECT 
                    UNNEST(author_countries) as country_code,
                    concepts,
                    cited_by_count
                FROM openalex_papers
                WHERE author_countries IS NOT NULL AND concepts IS NOT NULL
            ),
            concept_counts AS (
                SELECT 
                    country_code,
                    LOWER(concept) as skill,
                    COUNT(*) as paper_count,
                    SUM(cited_by_count) as total_citations
                FROM paper_data
                CROSS JOIN UNNEST(concepts) AS concept
                GROUP BY country_code, LOWER(concept)
            ),
            country_totals AS (
                SELECT country_code, COUNT(*) as total_papers
                FROM paper_data
                GROUP BY country_code
            )
            SELECT 
                cc.country_code,
                cc.skill,
                cc.paper_count,
                ct.total_papers,
                cc.total_citations,
                ROUND((cc.paper_count::numeric / NULLIF(ct.total_papers, 0)) * 100, 2) as supply_pct
            FROM concept_counts cc
            JOIN country_totals ct ON cc.country_code = ct.country_code
        """)
        print("   ✅ mv_skill_supply_by_country criada")
        
        # Criar view principal de gap
        print("\n🎯 Criando mv_skill_gap_by_country...")
        cur.execute("""
            CREATE MATERIALIZED VIEW sofia.mv_skill_gap_by_country AS
            SELECT 
                COALESCE(d.country_code, s.country_code) as country_code,
                COALESCE(d.skill, s.skill) as skill,
                COALESCE(d.demand_pct, 0) as demand_pct,
                COALESCE(s.supply_pct, 0) as supply_pct,
                COALESCE(d.demand_pct, 0) - COALESCE(s.supply_pct, 0) as gap_score,
                CASE 
                    WHEN COALESCE(d.demand_pct, 0) - COALESCE(s.supply_pct, 0) > 30 THEN 'market_hungry'
                    WHEN COALESCE(d.demand_pct, 0) - COALESCE(s.supply_pct, 0) < -30 THEN 'academia_ahead'
                    WHEN ABS(COALESCE(d.demand_pct, 0) - COALESCE(s.supply_pct, 0)) <= 10 THEN 'aligned'
                    ELSE 'moderate_gap'
                END as gap_type,
                COALESCE(d.job_count, 0) as job_count,
                COALESCE(d.total_jobs, 0) as total_jobs,
                COALESCE(s.paper_count, 0) as paper_count,
                COALESCE(s.total_papers, 0) as total_papers,
                COALESCE(s.total_citations, 0) as total_citations
            FROM sofia.mv_skill_demand_by_country d
            FULL OUTER JOIN sofia.mv_skill_supply_by_country s 
                ON d.country_code = s.country_code AND d.skill = s.skill
            WHERE d.skill IS NOT NULL OR s.skill IS NOT NULL
        """)
        print("   ✅ mv_skill_gap_by_country criada")
        
        # Criar summary por país
        print("\n📋 Criando mv_skill_gap_country_summary...")
        cur.execute("""
            CREATE MATERIALIZED VIEW sofia.mv_skill_gap_country_summary AS
            SELECT 
                country_code,
                COUNT(DISTINCT skill) as skills_analyzed,
                ROUND(AVG(ABS(gap_score)), 2) as avg_gap_score,
                ROUND(AVG(CASE WHEN gap_score > 0 THEN gap_score ELSE 0 END), 2) as avg_demand_gap,
                ROUND(AVG(CASE WHEN gap_score < 0 THEN ABS(gap_score) ELSE 0 END), 2) as avg_supply_excess,
                SUM(job_count) as total_job_mentions,
                MAX(total_jobs) as total_jobs,
                SUM(paper_count) as total_paper_mentions,
                MAX(total_papers) as total_papers,
                CASE 
                    WHEN AVG(gap_score) > 20 THEN 'market_hungry'
                    WHEN AVG(gap_score) < -20 THEN 'academia_ahead'
                    WHEN ABS(AVG(gap_score)) <= 10 THEN 'aligned'
                    ELSE 'moderate_gap'
                END as overall_gap_type,
                CASE 
                    WHEN MAX(total_jobs) >= 50 AND MAX(total_papers) >= 20 THEN 'high'
                    WHEN MAX(total_jobs) >= 10 AND MAX(total_papers) >= 5 THEN 'medium'
                    ELSE 'low'
                END as confidence
            FROM sofia.mv_skill_gap_by_country
            GROUP BY country_code
        """)
        print("   ✅ mv_skill_gap_country_summary criada")
        
        # Verificar contagem
        print("\n📈 Contagem de registros:")
        cur.execute("SELECT COUNT(*) FROM sofia.mv_skill_demand_by_country")
        print(f"   Demand: {cur.fetchone()[0]} rows")
        
        cur.execute("SELECT COUNT(*) FROM sofia.mv_skill_supply_by_country")
        print(f"   Supply: {cur.fetchone()[0]} rows")
        
        cur.execute("SELECT COUNT(*) FROM sofia.mv_skill_gap_by_country")
        print(f"   Gap: {cur.fetchone()[0]} rows")
        
        cur.execute("SELECT COUNT(*) FROM sofia.mv_skill_gap_country_summary")
        print(f"   Summary: {cur.fetchone()[0]} rows")
        
        # Sample de dados
        print("\n🔍 Sample de Skill Gap por país:")
        cur.execute("""
            SELECT country_code, skill, demand_pct, supply_pct, gap_score, gap_type
            FROM sofia.mv_skill_gap_by_country
            WHERE ABS(gap_score) > 5
            ORDER BY ABS(gap_score) DESC
            LIMIT 10
        """)
        for row in cur.fetchall():
            print(f"   {row[0]}: {row[1]} | Demand:{row[2]}% Supply:{row[3]}% Gap:{row[4]} ({row[5]})")
        
        print("\n✅ Todas as views criadas com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_skill_gap_view()
