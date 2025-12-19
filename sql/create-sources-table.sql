-- ============================================================
-- TABELA SOURCES - Completa e Centralizada
-- Gerencia todas as fontes de dados do sistema
-- ============================================================

CREATE TABLE IF NOT EXISTS sofia.sources (
    id SERIAL PRIMARY KEY,
    
    -- Identificação
    name VARCHAR(100) UNIQUE NOT NULL,
    normalized_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200),
    
    -- Classificação
    category VARCHAR(50) NOT NULL,  -- 'api', 'scraper', 'database', 'file', 'manual'
    data_type VARCHAR(50),  -- 'papers', 'patents', 'jobs', 'trends', 'posts', 'funding'
    
    -- Informações da Fonte
    description TEXT,
    website_url VARCHAR(500),
    api_url VARCHAR(500),
    documentation_url VARCHAR(500),
    
    -- Credenciais (criptografadas no app, não aqui!)
    requires_auth BOOLEAN DEFAULT false,
    auth_type VARCHAR(50),  -- 'api_key', 'oauth', 'basic', 'bearer', 'none'
    -- NÃO armazenar api_key aqui! Usar .env
    
    -- Rate Limiting
    rate_limit_requests INTEGER,  -- requests por período
    rate_limit_period VARCHAR(20),  -- 'second', 'minute', 'hour', 'day'
    rate_limit_concurrent INTEGER DEFAULT 1,  -- requests simultâneas
    
    -- Qualidade e Confiabilidade
    reliability_score NUMERIC(3,2) DEFAULT 1.0,  -- 0.0 a 1.0
    data_quality_score NUMERIC(3,2) DEFAULT 1.0,
    priority INTEGER DEFAULT 50,  -- 1-100, maior = mais prioritário
    
    -- Status
    active BOOLEAN DEFAULT true,
    is_paid BOOLEAN DEFAULT false,
    cost_per_request NUMERIC(10,4),  -- custo em USD
    monthly_quota INTEGER,  -- quota mensal se aplicável
    
    -- Metadados
    terms_of_service_url VARCHAR(500),
    license VARCHAR(100),  -- 'MIT', 'CC-BY', 'proprietary', etc
    attribution_required BOOLEAN DEFAULT false,
    attribution_text TEXT,
    
    -- Técnico
    response_format VARCHAR(50),  -- 'json', 'xml', 'csv', 'html'
    encoding VARCHAR(20) DEFAULT 'utf-8',
    timeout_seconds INTEGER DEFAULT 30,
    retry_attempts INTEGER DEFAULT 3,
    
    -- Estatísticas
    total_requests BIGINT DEFAULT 0,
    successful_requests BIGINT DEFAULT 0,
    failed_requests BIGINT DEFAULT 0,
    last_request_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_failure_at TIMESTAMPTZ,
    
    -- Metadata flexível
    metadata JSONB,
    
    -- Auditoria
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100),
    notes TEXT
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_sources_normalized_name ON sofia.sources(normalized_name);
CREATE INDEX IF NOT EXISTS idx_sources_category ON sofia.sources(category);
CREATE INDEX IF NOT EXISTS idx_sources_data_type ON sofia.sources(data_type);
CREATE INDEX IF NOT EXISTS idx_sources_active ON sofia.sources(active);
CREATE INDEX IF NOT EXISTS idx_sources_priority ON sofia.sources(priority DESC);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_sources_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sources_updated_at
    BEFORE UPDATE ON sofia.sources
    FOR EACH ROW
    EXECUTE FUNCTION update_sources_updated_at();

-- ============================================================
-- POPULAR SOURCES INICIAIS
-- ============================================================

INSERT INTO sofia.sources (
    name, normalized_name, display_name, category, data_type,
    description, website_url, api_url, documentation_url,
    requires_auth, auth_type, rate_limit_requests, rate_limit_period,
    reliability_score, data_quality_score, priority, license
) VALUES

-- APIs Acadêmicas
('openalex', 'openalex', 'OpenAlex', 'api', 'papers',
 'Open catalog of scholarly papers, authors, institutions',
 'https://openalex.org', 'https://api.openalex.org', 'https://docs.openalex.org',
 false, 'none', 100000, 'day', 0.95, 0.95, 90, 'CC0'),

('crossref', 'crossref', 'Crossref', 'api', 'papers',
 'DOI registration agency for scholarly content',
 'https://crossref.org', 'https://api.crossref.org', 'https://api.crossref.org/swagger-ui',
 false, 'none', 50, 'second', 0.90, 0.90, 85, 'CC0'),

-- Patents
('epo', 'epo', 'European Patent Office', 'api', 'patents',
 'European patent data',
 'https://epo.org', 'https://ops.epo.org', 'https://developers.epo.org',
 true, 'oauth', 30, 'minute', 0.95, 0.95, 90, 'proprietary'),

('wipo', 'wipo', 'WIPO', 'api', 'patents',
 'World Intellectual Property Organization',
 'https://wipo.int', 'https://patentscope.wipo.int/search', null,
 false, 'none', 10, 'second', 0.90, 0.90, 85, 'proprietary'),

-- Tech Trends
('github', 'github', 'GitHub', 'api', 'trends',
 'GitHub repositories and trends',
 'https://github.com', 'https://api.github.com', 'https://docs.github.com/rest',
 true, 'bearer', 5000, 'hour', 0.95, 0.95, 95, 'proprietary'),

('stackoverflow', 'stackoverflow', 'Stack Overflow', 'api', 'trends',
 'Q&A for programmers',
 'https://stackoverflow.com', 'https://api.stackexchange.com', 'https://api.stackexchange.com/docs',
 false, 'api_key', 300, 'day', 0.90, 0.90, 85, 'CC BY-SA'),

('npm', 'npm', 'NPM Registry', 'api', 'trends',
 'Node.js package registry',
 'https://npmjs.com', 'https://registry.npmjs.org', 'https://github.com/npm/registry/blob/master/docs/REGISTRY-API.md',
 false, 'none', 1000, 'hour', 0.95, 0.95, 90, 'proprietary'),

('pypi', 'pypi', 'PyPI', 'api', 'trends',
 'Python package index',
 'https://pypi.org', 'https://pypi.org/pypi', 'https://warehouse.pypa.io/api-reference/',
 false, 'none', 1000, 'hour', 0.95, 0.95, 90, 'proprietary'),

-- Community
('hackernews', 'hackernews', 'Hacker News', 'api', 'posts',
 'Tech news and discussions',
 'https://news.ycombinator.com', 'https://hacker-news.firebaseio.com', 'https://github.com/HackerNews/API',
 false, 'none', 1000, 'hour', 0.85, 0.80, 75, 'proprietary'),

('reddit', 'reddit', 'Reddit', 'api', 'posts',
 'Social news aggregation',
 'https://reddit.com', 'https://oauth.reddit.com', 'https://www.reddit.com/dev/api',
 true, 'oauth', 60, 'minute', 0.80, 0.75, 70, 'proprietary'),

-- Jobs
('linkedin', 'linkedin', 'LinkedIn', 'scraper', 'jobs',
 'Professional networking and jobs',
 'https://linkedin.com', null, null,
 true, 'oauth', 100, 'day', 0.85, 0.85, 80, 'proprietary'),

('catho', 'catho', 'Catho', 'scraper', 'jobs',
 'Brazilian job board',
 'https://catho.com.br', null, null,
 false, 'none', 10, 'minute', 0.75, 0.70, 60, 'proprietary'),

-- Funding
('crunchbase', 'crunchbase', 'Crunchbase', 'api', 'funding',
 'Startup funding and company data',
 'https://crunchbase.com', 'https://api.crunchbase.com', 'https://data.crunchbase.com/docs',
 true, 'api_key', 200, 'day', 0.90, 0.90, 85, 'proprietary'),

-- Manual/Internal
('manual', 'manual', 'Manual Entry', 'manual', 'various',
 'Data entered manually by users',
 null, null, null,
 false, 'none', null, null, 0.70, 0.60, 30, 'proprietary')

ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- FUNÇÕES HELPER
-- ============================================================

-- Incrementar contador de requests
CREATE OR REPLACE FUNCTION increment_source_requests(
    source_name TEXT,
    success BOOLEAN DEFAULT true
)
RETURNS VOID AS $$
BEGIN
    UPDATE sofia.sources
    SET 
        total_requests = total_requests + 1,
        successful_requests = CASE WHEN success THEN successful_requests + 1 ELSE successful_requests END,
        failed_requests = CASE WHEN NOT success THEN failed_requests + 1 ELSE failed_requests END,
        last_request_at = NOW(),
        last_success_at = CASE WHEN success THEN NOW() ELSE last_success_at END,
        last_failure_at = CASE WHEN NOT success THEN NOW() ELSE last_failure_at END
    WHERE normalized_name = normalize_string(source_name);
END;
$$ LANGUAGE plpgsql;

-- Get source by name
CREATE OR REPLACE FUNCTION get_source_id(source_name TEXT)
RETURNS INTEGER AS $$
DECLARE
    source_id_result INTEGER;
BEGIN
    SELECT id INTO source_id_result
    FROM sofia.sources
    WHERE normalized_name = normalize_string(source_name)
    AND active = true
    LIMIT 1;
    
    RETURN source_id_result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- VERIFICAÇÃO
-- ============================================================

SELECT 
    'Sources Created' AS status,
    COUNT(*) AS total,
    COUNT(CASE WHEN active THEN 1 END) AS active,
    COUNT(CASE WHEN requires_auth THEN 1 END) AS requires_auth
FROM sofia.sources;

SELECT 
    category,
    COUNT(*) AS count,
    AVG(reliability_score)::NUMERIC(3,2) AS avg_reliability
FROM sofia.sources
WHERE active = true
GROUP BY category
ORDER BY count DESC;
