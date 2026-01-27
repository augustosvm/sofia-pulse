-- VSCode Marketplace Daily Metrics
-- Tracks daily snapshots of extension installs, ratings, trending rank

CREATE TABLE IF NOT EXISTS sofia.vscode_extensions_daily (
  id SERIAL PRIMARY KEY,

  -- Extension identity
  extension_id TEXT NOT NULL,           -- e.g., "rust-lang.rust-analyzer"
  publisher TEXT,                       -- e.g., "rust-lang"
  extension_name TEXT,                  -- e.g., "rust-analyzer"
  display_name TEXT,                    -- e.g., "Rust Analyzer"

  -- Date snapshot
  snapshot_date DATE NOT NULL,

  -- Metrics
  installs BIGINT,                      -- Total installs (cumulative)
  installs_delta INT,                   -- Daily change (vs previous day)
  rating_value NUMERIC(3,2),            -- e.g., 4.75
  rating_count INT,                     -- Number of ratings
  trending_rank INT,                    -- Position in trending list (1-100, null if not trending)

  -- Metadata
  version TEXT,                         -- Current version
  last_updated_at TIMESTAMPTZ,          -- When extension was last updated
  categories TEXT[],                    -- e.g., ['Programming Languages', 'Linters']
  tags TEXT[],                          -- e.g., ['rust', 'lsp', 'analyzer']

  -- Audit
  collected_at TIMESTAMPTZ DEFAULT NOW(),

  -- Constraints
  UNIQUE(extension_id, snapshot_date)
);

-- Indexes for fast queries
CREATE INDEX idx_vscode_ext_date ON sofia.vscode_extensions_daily(snapshot_date DESC);
CREATE INDEX idx_vscode_ext_id_date ON sofia.vscode_extensions_daily(extension_id, snapshot_date DESC);
CREATE INDEX idx_vscode_ext_trending ON sofia.vscode_extensions_daily(trending_rank) WHERE trending_rank IS NOT NULL;
CREATE INDEX idx_vscode_ext_tags ON sofia.vscode_extensions_daily USING gin(tags);
CREATE INDEX idx_vscode_ext_categories ON sofia.vscode_extensions_daily USING gin(categories);

-- Materialized view for 7d deltas (updated daily)
CREATE MATERIALIZED VIEW IF NOT EXISTS sofia.vscode_extensions_7d_deltas AS
SELECT
  today.extension_id,
  today.display_name,
  today.snapshot_date,
  today.installs AS installs_current,
  prev.installs AS installs_7d_ago,
  today.installs - COALESCE(prev.installs, 0) AS installs_delta_7d,
  CASE
    WHEN COALESCE(prev.installs, 0) > 0 THEN
      ROUND((today.installs - prev.installs)::NUMERIC / prev.installs * 100, 2)
    ELSE NULL
  END AS installs_delta_pct_7d,
  today.rating_value,
  today.rating_count,
  today.trending_rank,
  today.tags,
  today.categories
FROM sofia.vscode_extensions_daily today
LEFT JOIN sofia.vscode_extensions_daily prev
  ON today.extension_id = prev.extension_id
  AND prev.snapshot_date = today.snapshot_date - INTERVAL '7 days'
WHERE today.snapshot_date = (SELECT MAX(snapshot_date) FROM sofia.vscode_extensions_daily);

CREATE UNIQUE INDEX idx_vscode_7d_deltas_ext ON sofia.vscode_extensions_7d_deltas(extension_id);
CREATE INDEX idx_vscode_7d_deltas_delta ON sofia.vscode_extensions_7d_deltas(installs_delta_7d DESC NULLS LAST);

COMMENT ON TABLE sofia.vscode_extensions_daily IS 'Daily snapshots of VSCode Marketplace extensions metrics for cross-signal correlation';
COMMENT ON MATERIALIZED VIEW sofia.vscode_extensions_7d_deltas IS 'Pre-computed 7-day deltas for cross-signals builder (refresh daily)';
