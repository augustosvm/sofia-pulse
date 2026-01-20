-- ============================================================================
-- SKILL GAP INDEX - Materialized View
-- ============================================================================
-- Calcula o gap entre skills demandadas (jobs) e produzidas (papers)
-- por país/região
-- ============================================================================

-- Primeiro, extraímos keywords de tecnologia das descrições de vagas
-- Depois comparamos com os concepts dos papers

-- Step 1: Lista de skills para buscar (normalizada)
CREATE OR REPLACE VIEW sofia.skill_keywords AS
SELECT unnest(ARRAY[
    -- Programming Languages
    'python', 'javascript', 'typescript', 'java', 'golang', 'rust', 'c++', 'ruby', 'php', 'scala', 'kotlin',
    -- Cloud & DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'ci/cd', 'devops',
    -- Data & AI
    'machine learning', 'deep learning', 'artificial intelligence', 'data science', 'nlp', 
    'natural language', 'computer vision', 'tensorflow', 'pytorch', 'pandas', 'spark',
    -- Web
    'react', 'angular', 'vue', 'node.js', 'nodejs', 'fastapi', 'django', 'flask',
    -- Database
    'sql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
    -- Other
    'api', 'microservices', 'agile', 'scrum', 'blockchain', 'cybersecurity', 'security'
]) AS skill;

-- Step 2: Contagem de skills nas vagas por país
CREATE MATERIALIZED VIEW IF NOT EXISTS sofia.mv_skill_demand_by_country AS
WITH job_skills AS (
    SELECT 
        COALESCE(UPPER(SUBSTRING(country, 1, 2)), 'XX') as country_code,
        LOWER(description) as desc_lower,
        source,
        posted_date
    FROM sofia.jobs
    WHERE description IS NOT NULL
      AND posted_date >= CURRENT_DATE - INTERVAL '90 days'
    
    UNION ALL
    
    SELECT 
        COALESCE(UPPER(SUBSTRING(country, 1, 2)), 'XX') as country_code,
        LOWER(description) as desc_lower,
        platform as source,
        posted_date::date
    FROM tech_jobs
    WHERE description IS NOT NULL
      AND posted_date >= CURRENT_DATE - INTERVAL '90 days'
),
skill_matches AS (
    SELECT 
        j.country_code,
        s.skill,
        COUNT(*) as job_count
    FROM job_skills j
    CROSS JOIN sofia.skill_keywords s
    WHERE j.desc_lower LIKE '%' || s.skill || '%'
    GROUP BY j.country_code, s.skill
),
country_totals AS (
    SELECT country_code, COUNT(DISTINCT desc_lower) as total_jobs
    FROM job_skills
    GROUP BY country_code
)
SELECT 
    sm.country_code,
    sm.skill,
    sm.job_count,
    ct.total_jobs,
    ROUND((sm.job_count::numeric / NULLIF(ct.total_jobs, 0)) * 100, 2) as demand_pct,
    'jobs' as data_source,
    NOW() as calculated_at
FROM skill_matches sm
JOIN country_totals ct ON sm.country_code = ct.country_code
WHERE sm.job_count >= 3  -- Mínimo de 3 ocorrências
ORDER BY sm.country_code, demand_pct DESC;

-- Step 3: Contagem de concepts nos papers por país
CREATE MATERIALIZED VIEW IF NOT EXISTS sofia.mv_skill_supply_by_country AS
WITH paper_countries AS (
    SELECT 
        UNNEST(author_countries) as country_code,
        concepts,
        primary_concept,
        cited_by_count
    FROM openalex_papers
    WHERE author_countries IS NOT NULL
      AND concepts IS NOT NULL
),
concept_matches AS (
    SELECT 
        pc.country_code,
        LOWER(concept) as concept,
        COUNT(*) as paper_count,
        SUM(pc.cited_by_count) as total_citations
    FROM paper_countries pc
    CROSS JOIN UNNEST(pc.concepts) AS concept
    GROUP BY pc.country_code, LOWER(concept)
),
country_totals AS (
    SELECT country_code, COUNT(*) as total_papers
    FROM paper_countries
    GROUP BY country_code
)
SELECT 
    cm.country_code,
    cm.concept as skill,
    cm.paper_count,
    ct.total_papers,
    cm.total_citations,
    ROUND((cm.paper_count::numeric / NULLIF(ct.total_papers, 0)) * 100, 2) as supply_pct,
    'papers' as data_source,
    NOW() as calculated_at
FROM concept_matches cm
JOIN country_totals ct ON cm.country_code = ct.country_code
WHERE cm.paper_count >= 1
ORDER BY cm.country_code, supply_pct DESC;

-- Step 4: Skill Gap calculado por país
CREATE MATERIALIZED VIEW IF NOT EXISTS sofia.mv_skill_gap_by_country AS
WITH demand AS (
    SELECT country_code, skill, demand_pct, job_count, total_jobs
    FROM sofia.mv_skill_demand_by_country
),
supply AS (
    SELECT country_code, skill, supply_pct, paper_count, total_papers, total_citations
    FROM sofia.mv_skill_supply_by_country
),
all_skills AS (
    SELECT DISTINCT skill FROM demand
    UNION
    SELECT DISTINCT skill FROM supply
),
all_countries AS (
    SELECT DISTINCT country_code FROM demand
    UNION
    SELECT DISTINCT country_code FROM supply
),
gap_calculation AS (
    SELECT 
        c.country_code,
        s.skill,
        COALESCE(d.demand_pct, 0) as demand_pct,
        COALESCE(sup.supply_pct, 0) as supply_pct,
        COALESCE(d.demand_pct, 0) - COALESCE(sup.supply_pct, 0) as gap_score,
        COALESCE(d.job_count, 0) as job_count,
        COALESCE(d.total_jobs, 0) as total_jobs,
        COALESCE(sup.paper_count, 0) as paper_count,
        COALESCE(sup.total_papers, 0) as total_papers,
        COALESCE(sup.total_citations, 0) as total_citations
    FROM all_countries c
    CROSS JOIN all_skills s
    LEFT JOIN demand d ON c.country_code = d.country_code AND s.skill = d.skill
    LEFT JOIN supply sup ON c.country_code = sup.country_code AND s.skill = sup.skill
    WHERE d.demand_pct IS NOT NULL OR sup.supply_pct IS NOT NULL
)
SELECT 
    country_code,
    skill,
    demand_pct,
    supply_pct,
    gap_score,
    -- Classificação do gap
    CASE 
        WHEN gap_score > 30 THEN 'market_hungry'    -- Vermelho: mercado faminto
        WHEN gap_score < -30 THEN 'academia_ahead'  -- Azul: academia à frente
        WHEN ABS(gap_score) <= 10 THEN 'aligned'    -- Verde: alinhado
        ELSE 'moderate_gap'                          -- Amarelo: gap moderado
    END as gap_type,
    job_count,
    total_jobs,
    paper_count,
    total_papers,
    total_citations,
    -- Confidence score
    CASE 
        WHEN total_jobs >= 50 AND total_papers >= 20 THEN 'high'
        WHEN total_jobs >= 10 AND total_papers >= 5 THEN 'medium'
        ELSE 'low'
    END as confidence,
    NOW() as calculated_at
FROM gap_calculation
ORDER BY country_code, ABS(gap_score) DESC;

-- Step 5: Agregação por país (score geral)
CREATE MATERIALIZED VIEW IF NOT EXISTS sofia.mv_skill_gap_country_summary AS
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
    -- Top 3 skills com maior gap de demanda
    (SELECT ARRAY_AGG(skill ORDER BY gap_score DESC) 
     FROM (SELECT skill, gap_score FROM sofia.mv_skill_gap_by_country g2 
           WHERE g2.country_code = g.country_code AND gap_score > 0 
           ORDER BY gap_score DESC LIMIT 3) x) as top_demand_gaps,
    -- Top 3 skills com maior supply (academia à frente)
    (SELECT ARRAY_AGG(skill ORDER BY gap_score) 
     FROM (SELECT skill, gap_score FROM sofia.mv_skill_gap_by_country g3 
           WHERE g3.country_code = g.country_code AND gap_score < 0 
           ORDER BY gap_score LIMIT 3) y) as top_supply_excess,
    -- Classificação geral do país
    CASE 
        WHEN AVG(gap_score) > 20 THEN 'market_hungry'
        WHEN AVG(gap_score) < -20 THEN 'academia_ahead'
        WHEN ABS(AVG(gap_score)) <= 10 THEN 'aligned'
        ELSE 'moderate_gap'
    END as overall_gap_type,
    -- Confidence
    CASE 
        WHEN MAX(total_jobs) >= 50 AND MAX(total_papers) >= 20 THEN 'high'
        WHEN MAX(total_jobs) >= 10 AND MAX(total_papers) >= 5 THEN 'medium'
        ELSE 'low'
    END as confidence,
    NOW() as calculated_at
FROM sofia.mv_skill_gap_by_country g
GROUP BY country_code;

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_skill_gap_country ON sofia.mv_skill_gap_by_country(country_code);
CREATE INDEX IF NOT EXISTS idx_skill_gap_skill ON sofia.mv_skill_gap_by_country(skill);
CREATE INDEX IF NOT EXISTS idx_skill_gap_type ON sofia.mv_skill_gap_by_country(gap_type);
CREATE INDEX IF NOT EXISTS idx_skill_gap_summary_country ON sofia.mv_skill_gap_country_summary(country_code);

-- Refresh command (para crontab)
-- REFRESH MATERIALIZED VIEW sofia.mv_skill_demand_by_country;
-- REFRESH MATERIALIZED VIEW sofia.mv_skill_supply_by_country;
-- REFRESH MATERIALIZED VIEW sofia.mv_skill_gap_by_country;
-- REFRESH MATERIALIZED VIEW sofia.mv_skill_gap_country_summary;
