-- Migration: Create Skill State Table (Watermark Persistence)
-- Purpose: Store watermark and state per skill/domain/detector
-- Date: 2025-12-10

CREATE TABLE IF NOT EXISTS sofia.skill_state (
  state_id SERIAL PRIMARY KEY,
  
  -- Key (unique combination)
  skill_name VARCHAR(100) NOT NULL,
  domain VARCHAR(50),              -- NULL = applies to all domains
  detector VARCHAR(100),           -- NULL = applies to all detectors
  
  -- State
  last_processed_at TIMESTAMP,
  last_processed_id VARCHAR(255),  -- Last record ID processed
  state_data JSONB,                -- Additional state data
  
  -- Metadata
  updated_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  
  -- Unique constraint
  CONSTRAINT skill_state_unique UNIQUE (skill_name, domain, detector)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_skill_state_skill ON sofia.skill_state(skill_name);
CREATE INDEX IF NOT EXISTS idx_skill_state_domain ON sofia.skill_state(domain);
CREATE INDEX IF NOT EXISTS idx_skill_state_updated ON sofia.skill_state(updated_at DESC);

-- Comments
COMMENT ON TABLE sofia.skill_state IS 'Persistent state for skills (watermark, last_id, etc)';
COMMENT ON COLUMN sofia.skill_state.skill_name IS 'Skill name (e.g., insights.generate, data.normalize)';
COMMENT ON COLUMN sofia.skill_state.domain IS 'Domain (research, tech, jobs) or NULL for global';
COMMENT ON COLUMN sofia.skill_state.detector IS 'Detector name or NULL for all detectors';
COMMENT ON COLUMN sofia.skill_state.last_processed_at IS 'Watermark: last data timestamp processed';
COMMENT ON COLUMN sofia.skill_state.last_processed_id IS 'Last record ID processed (if applicable)';
COMMENT ON COLUMN sofia.skill_state.state_data IS 'Additional state data (JSONB)';
