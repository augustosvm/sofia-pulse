-- Migration: Create Jobs Table
-- Author: Sofia Pulse
-- Date: 2025-11-18
-- Description: Tabela para rastrear vagas de emprego tech por país e setor

CREATE TABLE IF NOT EXISTS sofia.jobs (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  company VARCHAR(255) NOT NULL,
  location VARCHAR(255),
  country VARCHAR(100) NOT NULL,
  sector VARCHAR(100) NOT NULL,
  description TEXT,
  salary_range VARCHAR(100),
  remote BOOLEAN DEFAULT FALSE,
  posted_date DATE NOT NULL,
  url TEXT NOT NULL,
  source VARCHAR(50) NOT NULL, -- 'Indeed', 'LinkedIn', 'AngelList'

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(url)
);

-- Indexes
CREATE INDEX idx_jobs_country ON sofia.jobs(country);
CREATE INDEX idx_jobs_sector ON sofia.jobs(sector);
CREATE INDEX idx_jobs_posted_date ON sofia.jobs(posted_date);
CREATE INDEX idx_jobs_remote ON sofia.jobs(remote);
CREATE INDEX idx_jobs_source ON sofia.jobs(source);

-- Composite indexes para queries comuns
CREATE INDEX idx_jobs_country_sector ON sofia.jobs(country, sector);
CREATE INDEX idx_jobs_country_posted ON sofia.jobs(country, posted_date DESC);

-- Comments
COMMENT ON TABLE sofia.jobs IS 'Vagas de emprego tech coletadas de Indeed, LinkedIn, AngelList';
COMMENT ON COLUMN sofia.jobs.country IS 'País da vaga (Brasil, USA, etc)';
COMMENT ON COLUMN sofia.jobs.sector IS 'Setor (AI/ML, Frontend, Backend, etc)';
COMMENT ON COLUMN sofia.jobs.remote IS 'TRUE se vaga é remota';
COMMENT ON COLUMN sofia.jobs.source IS 'Fonte: Indeed, LinkedIn, AngelList';

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_jobs_updated_at
  BEFORE UPDATE ON sofia.jobs
  FOR EACH ROW
  EXECUTE FUNCTION update_jobs_updated_at();

-- Queries úteis

-- Vagas recentes no Brasil por setor
COMMENT ON TABLE sofia.jobs IS '
Query: Vagas recentes no Brasil
SELECT sector, COUNT(*) as vagas,
  COUNT(*) FILTER (WHERE remote) as remotas
FROM sofia.jobs
WHERE country = ''Brasil''
  AND posted_date >= CURRENT_DATE - INTERVAL ''30 days''
GROUP BY sector
ORDER BY vagas DESC;
';

-- Empresas contratando por país
COMMENT ON COLUMN sofia.jobs.company IS '
Query: Top empresas contratando
SELECT company, country, COUNT(*) as vagas_abertas
FROM sofia.jobs
WHERE posted_date >= CURRENT_DATE - INTERVAL ''30 days''
GROUP BY company, country
ORDER BY vagas_abertas DESC
LIMIT 20;
';

-- Setores em alta por país
COMMENT ON COLUMN sofia.jobs.sector IS '
Query: Setores tech em alta
SELECT country, sector, COUNT(*) as vagas,
  ROUND(AVG(CASE WHEN remote THEN 1 ELSE 0 END) * 100) as pct_remote
FROM sofia.jobs
WHERE posted_date >= CURRENT_DATE - INTERVAL ''30 days''
GROUP BY country, sector
ORDER BY country, vagas DESC;
';
