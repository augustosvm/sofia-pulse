-- Migration: Create Insights Table
-- Purpose: Store generated insights from normalized data
-- Date: 2025-12-09

CREATE TABLE IF NOT EXISTS sofia.insights (
  insight_id SERIAL PRIMARY KEY,
  
  -- Classification
  domain VARCHAR(50) NOT NULL, -- research, tech, jobs, security, economy
  insight_type VARCHAR(100) NOT NULL, -- growth_spike, technology_trend, anomaly, etc
  
  -- Content
  title VARCHAR(500) NOT NULL,
  summary TEXT NOT NULL,
  
  -- Severity
  severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
  
  -- Evidence (JSON)
  evidence JSONB NOT NULL, -- Dados que provam o insight
  
  -- Metadata
  generated_at TIMESTAMP DEFAULT NOW(),
  trace_id UUID,
  watermark TIMESTAMP, -- last_processed_at usado para gerar este insight
  
  -- Deduplication
  evidence_hash VARCHAR(64) UNIQUE, -- Hash da evidência para evitar duplicação
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_insights_domain ON sofia.insights(domain);
CREATE INDEX IF NOT EXISTS idx_insights_type ON sofia.insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_insights_severity ON sofia.insights(severity);
CREATE INDEX IF NOT EXISTS idx_insights_generated_at ON sofia.insights(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_insights_trace ON sofia.insights(trace_id);
CREATE INDEX IF NOT EXISTS idx_insights_watermark ON sofia.insights(watermark);

-- GIN index for evidence JSON
CREATE INDEX IF NOT EXISTS idx_insights_evidence_gin ON sofia.insights USING gin(evidence);

-- Comments
COMMENT ON TABLE sofia.insights IS 'Generated insights from normalized data - ONLY REAL INSIGHTS';
COMMENT ON COLUMN sofia.insights.domain IS 'Data domain: research, tech, jobs, security, economy';
COMMENT ON COLUMN sofia.insights.insight_type IS 'Type of insight: growth_spike, technology_trend, anomaly, etc';
COMMENT ON COLUMN sofia.insights.evidence IS 'JSON proof of the insight (numbers, dates, entities)';
COMMENT ON COLUMN sofia.insights.evidence_hash IS 'SHA256 hash of evidence for deduplication';
COMMENT ON COLUMN sofia.insights.watermark IS 'Timestamp of last data processed to generate this insight';

-- View for latest insights by domain
CREATE OR REPLACE VIEW sofia.latest_insights_by_domain AS
SELECT
  domain,
  severity,
  COUNT(*) as total_insights,
  MAX(generated_at) as latest_insight,
  COUNT(*) FILTER (WHERE generated_at >= NOW() - INTERVAL '24 hours') as last_24h,
  COUNT(*) FILTER (WHERE generated_at >= NOW() - INTERVAL '7 days') as last_7d
FROM sofia.insights
GROUP BY domain, severity
ORDER BY domain, severity;

-- View for critical insights
CREATE OR REPLACE VIEW sofia.critical_insights AS
SELECT
  insight_id,
  domain,
  insight_type,
  title,
  summary,
  generated_at,
  evidence
FROM sofia.insights
WHERE severity = 'critical'
ORDER BY generated_at DESC
LIMIT 50;
