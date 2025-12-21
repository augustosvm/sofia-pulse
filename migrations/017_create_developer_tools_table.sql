-- Migration: Create developer_tools table
-- Purpose: Store developer tool adoption data from VS Code, JetBrains, Chrome Web Store
-- Leading indicator for tech trends (tool adoption predicts framework/language trends)

CREATE TABLE IF NOT EXISTS sofia.developer_tools (
    id SERIAL PRIMARY KEY,
    tool_name VARCHAR(255) NOT NULL,
    tool_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('vscode', 'chrome', 'jetbrains', 'npm', 'pypi')),
    category VARCHAR(100),
    downloads BIGINT,
    rating DECIMAL(3, 2),
    rating_count INTEGER,
    version VARCHAR(50),
    publisher VARCHAR(255),
    description TEXT,
    tags VARCHAR(255),
    homepage_url TEXT,
    repository_url TEXT,
    collected_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint: same tool can exist on multiple platforms, but (tool_id, platform) must be unique
    CONSTRAINT developer_tools_unique UNIQUE (tool_id, platform)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_developer_tools_platform ON sofia.developer_tools(platform);
CREATE INDEX IF NOT EXISTS idx_developer_tools_downloads ON sofia.developer_tools(downloads DESC);
CREATE INDEX IF NOT EXISTS idx_developer_tools_rating ON sofia.developer_tools(rating DESC);
CREATE INDEX IF NOT EXISTS idx_developer_tools_collected_at ON sofia.developer_tools(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_developer_tools_category ON sofia.developer_tools(category);
CREATE INDEX IF NOT EXISTS idx_developer_tools_publisher ON sofia.developer_tools(publisher);

-- Index for trend analysis (comparing downloads over time)
CREATE INDEX IF NOT EXISTS idx_developer_tools_trend ON sofia.developer_tools(tool_id, platform, collected_at DESC);

-- Comments
COMMENT ON TABLE sofia.developer_tools IS 'Developer tools adoption data from VS Code, JetBrains, Chrome Web Store. Leading indicator for tech trends.';
COMMENT ON COLUMN sofia.developer_tools.tool_name IS 'Display name of the tool/extension/plugin';
COMMENT ON COLUMN sofia.developer_tools.tool_id IS 'Unique identifier from the marketplace (e.g., publisher.extension-name)';
COMMENT ON COLUMN sofia.developer_tools.platform IS 'Marketplace platform (vscode, chrome, jetbrains, npm, pypi)';
COMMENT ON COLUMN sofia.developer_tools.category IS 'Tool category (e.g., Programming Languages, Debuggers, Themes)';
COMMENT ON COLUMN sofia.developer_tools.downloads IS 'Total downloads/installs count';
COMMENT ON COLUMN sofia.developer_tools.rating IS 'Average user rating (0-5 scale)';
COMMENT ON COLUMN sofia.developer_tools.rating_count IS 'Number of ratings';
COMMENT ON COLUMN sofia.developer_tools.version IS 'Latest version number';
COMMENT ON COLUMN sofia.developer_tools.publisher IS 'Publisher/vendor name';
COMMENT ON COLUMN sofia.developer_tools.description IS 'Tool description';
COMMENT ON COLUMN sofia.developer_tools.tags IS 'Comma-separated tags';
COMMENT ON COLUMN sofia.developer_tools.homepage_url IS 'Marketplace page URL';
COMMENT ON COLUMN sofia.developer_tools.repository_url IS 'Source code repository URL';
COMMENT ON COLUMN sofia.developer_tools.collected_at IS 'When this data was collected';
