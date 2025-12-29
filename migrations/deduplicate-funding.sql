-- ============================================================================
-- DEDUPLICAÇÃO DE FUNDING ROUNDS
-- ============================================================================
-- Remove duplicatas mantendo o registro mais recente
-- ============================================================================

-- 1. Identificar duplicatas
-- ============================================================================

DO $$
DECLARE
    duplicate_count INT;
BEGIN
    SELECT COUNT(*) INTO duplicate_count
    FROM (
        SELECT company_name, announced_date
        FROM sofia.funding_rounds
        WHERE announced_date IS NOT NULL
        GROUP BY company_name, announced_date
        HAVING COUNT(*) > 1
    ) AS dups;
    
    RAISE NOTICE '🔍 Duplicatas encontradas: % grupos', duplicate_count;
END $$;

-- 2. Remover duplicatas (manter o mais recente)
-- ============================================================================

WITH duplicates AS (
    SELECT 
        company_name,
        announced_date,
        COUNT(*) as count,
        ARRAY_AGG(id ORDER BY collected_at DESC, id DESC) as ids
    FROM sofia.funding_rounds
    WHERE announced_date IS NOT NULL
    GROUP BY company_name, announced_date
    HAVING COUNT(*) > 1
),
to_delete AS (
    SELECT UNNEST(ids[2:]) as id_to_delete
    FROM duplicates
)
DELETE FROM sofia.funding_rounds
WHERE id IN (SELECT id_to_delete FROM to_delete);

-- 3. Estatísticas pós-deduplicação
-- ============================================================================

DO $$
DECLARE
    total_funding INT;
    unique_companies INT;
    avg_rounds_per_company NUMERIC;
BEGIN
    SELECT COUNT(*) INTO total_funding FROM sofia.funding_rounds;
    SELECT COUNT(DISTINCT company_name) INTO unique_companies FROM sofia.funding_rounds;
    
    avg_rounds_per_company := ROUND(total_funding::NUMERIC / NULLIF(unique_companies, 0), 2);
    
    RAISE NOTICE '📊 ESTATÍSTICAS PÓS-DEDUPLICAÇÃO:';
    RAISE NOTICE '   Total de funding rounds: %', total_funding;
    RAISE NOTICE '   Empresas únicas: %', unique_companies;
    RAISE NOTICE '   Média de rounds por empresa: %', avg_rounds_per_company;
END $$;

-- ============================================================================
-- FIM DA DEDUPLICAÇÃO
-- ============================================================================
