-- ============================================================================
-- FUNDING ROUNDS - Schema Improvements & Constraints
-- ============================================================================
-- Objetivo: Unificar e padronizar dados de funding de múltiplas fontes
-- Fontes: SEC Edgar, Y Combinator, Crunchbase, etc.
-- ============================================================================

-- 1. Adicionar colunas necessárias (se não existirem)
-- ============================================================================

ALTER TABLE sofia.funding_rounds
ADD COLUMN IF NOT EXISTS source VARCHAR(50);

ALTER TABLE sofia.funding_rounds
ADD COLUMN IF NOT EXISTS metadata JSONB;

ALTER TABLE sofia.funding_rounds
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

ALTER TABLE sofia.funding_rounds
ADD COLUMN IF NOT EXISTS organization_id INTEGER;

COMMENT ON COLUMN sofia.funding_rounds.source IS 
'Fonte dos dados: sec_edgar, yc_companies, crunchbase, etc.';

COMMENT ON COLUMN sofia.funding_rounds.metadata IS 
'Dados adicionais estruturados específicos da fonte (JSON)';

COMMENT ON COLUMN sofia.funding_rounds.organization_id IS 
'FK para sofia.organizations - empresa normalizada';

-- 2. Adicionar Foreign Key para organizations
-- ============================================================================

ALTER TABLE sofia.funding_rounds
ADD CONSTRAINT fk_funding_organization
FOREIGN KEY (organization_id) 
REFERENCES sofia.organizations(id)
ON DELETE SET NULL;

-- 3. Adicionar constraint de unicidade
-- ============================================================================
-- Previne duplicatas da mesma empresa/data/fonte

ALTER TABLE sofia.funding_rounds
DROP CONSTRAINT IF EXISTS unique_funding_round;

ALTER TABLE sofia.funding_rounds
ADD CONSTRAINT unique_funding_round 
UNIQUE (company_name, announced_date, source);

-- 4. Adicionar índices para performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_funding_organization_id 
ON sofia.funding_rounds(organization_id)
WHERE organization_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_funding_source 
ON sofia.funding_rounds(source)
WHERE source IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_funding_round_type 
ON sofia.funding_rounds(round_type);

CREATE INDEX IF NOT EXISTS idx_funding_announced_date 
ON sofia.funding_rounds(announced_date DESC)
WHERE announced_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_funding_country 
ON sofia.funding_rounds(country)
WHERE country IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_funding_metadata 
ON sofia.funding_rounds USING GIN (metadata)
WHERE metadata IS NOT NULL;

-- 5. Adicionar trigger para updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_funding_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_funding_updated_at ON sofia.funding_rounds;

CREATE TRIGGER trigger_funding_updated_at
    BEFORE UPDATE ON sofia.funding_rounds
    FOR EACH ROW
    EXECUTE FUNCTION update_funding_updated_at();

-- 6. Estatísticas iniciais
-- ============================================================================

DO $$
DECLARE
    total_funding INT;
    with_org_id INT;
    with_source INT;
    with_date INT;
BEGIN
    SELECT COUNT(*) INTO total_funding FROM sofia.funding_rounds;
    SELECT COUNT(*) INTO with_org_id FROM sofia.funding_rounds WHERE organization_id IS NOT NULL;
    SELECT COUNT(*) INTO with_source FROM sofia.funding_rounds WHERE source IS NOT NULL;
    SELECT COUNT(*) INTO with_date FROM sofia.funding_rounds WHERE announced_date IS NOT NULL;
    
    RAISE NOTICE '📊 FUNDING ROUNDS - Estatísticas Iniciais:';
    RAISE NOTICE '   Total de registros: %', total_funding;
    RAISE NOTICE '   Com organization_id: % (%%)', with_org_id, ROUND(100.0 * with_org_id / NULLIF(total_funding, 0), 1);
    RAISE NOTICE '   Com source: % (%%)', with_source, ROUND(100.0 * with_source / NULLIF(total_funding, 0), 1);
    RAISE NOTICE '   Com announced_date: % (%%)', with_date, ROUND(100.0 * with_date / NULLIF(total_funding, 0), 1);
END $$;

-- ============================================================================
-- FIM DA MIGRATION
-- ============================================================================
