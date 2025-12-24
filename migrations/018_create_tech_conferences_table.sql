-- Migration: Create tech_conferences table
-- Purpose: Store tech conferences and events data
-- Leading indicator for tech trends (frameworks announced at conferences, speaker topics = emerging tech)

CREATE TABLE IF NOT EXISTS sofia.tech_conferences (
    id SERIAL PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('conference', 'meetup', 'workshop', 'webinar', 'hackathon')),
    category VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE,
    location_city VARCHAR(100),
    location_country VARCHAR(100),
    is_online BOOLEAN DEFAULT FALSE,
    website_url TEXT,
    topics VARCHAR(255),
    description TEXT,
    attendee_count INTEGER,
    speaker_count INTEGER,
    organizer VARCHAR(255),
    collected_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint: same event name + start date
    CONSTRAINT tech_conferences_unique UNIQUE (event_name, start_date)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_tech_conferences_start_date ON sofia.tech_conferences(start_date DESC);
CREATE INDEX IF NOT EXISTS idx_tech_conferences_category ON sofia.tech_conferences(category);
CREATE INDEX IF NOT EXISTS idx_tech_conferences_country ON sofia.tech_conferences(location_country);
CREATE INDEX IF NOT EXISTS idx_tech_conferences_online ON sofia.tech_conferences(is_online);
CREATE INDEX IF NOT EXISTS idx_tech_conferences_collected_at ON sofia.tech_conferences(collected_at DESC);

-- Index for upcoming events
CREATE INDEX IF NOT EXISTS idx_tech_conferences_upcoming ON sofia.tech_conferences(start_date) WHERE start_date >= CURRENT_DATE;

-- Index for topic search (GIN for full-text search)
CREATE INDEX IF NOT EXISTS idx_tech_conferences_topics_gin ON sofia.tech_conferences USING gin(to_tsvector('english', COALESCE(topics, '')));

-- Comments
COMMENT ON TABLE sofia.tech_conferences IS 'Tech conferences and events. Leading indicator for tech trends (frameworks announced at conferences).';
COMMENT ON COLUMN sofia.tech_conferences.event_name IS 'Name of the conference/event';
COMMENT ON COLUMN sofia.tech_conferences.event_type IS 'Type: conference, meetup, workshop, webinar, hackathon';
COMMENT ON COLUMN sofia.tech_conferences.category IS 'Main category/topic (e.g., JavaScript, AI, Cloud, DevOps)';
COMMENT ON COLUMN sofia.tech_conferences.start_date IS 'Event start date';
COMMENT ON COLUMN sofia.tech_conferences.end_date IS 'Event end date';
COMMENT ON COLUMN sofia.tech_conferences.location_city IS 'City where event takes place';
COMMENT ON COLUMN sofia.tech_conferences.location_country IS 'Country where event takes place';
COMMENT ON COLUMN sofia.tech_conferences.is_online IS 'Whether event is online/virtual';
COMMENT ON COLUMN sofia.tech_conferences.website_url IS 'Official event website';
COMMENT ON COLUMN sofia.tech_conferences.topics IS 'Comma-separated topics/tags';
COMMENT ON COLUMN sofia.tech_conferences.description IS 'Event description';
COMMENT ON COLUMN sofia.tech_conferences.attendee_count IS 'Expected or actual attendee count';
COMMENT ON COLUMN sofia.tech_conferences.speaker_count IS 'Number of speakers';
COMMENT ON COLUMN sofia.tech_conferences.organizer IS 'Organization/person organizing the event';
COMMENT ON COLUMN sofia.tech_conferences.collected_at IS 'When this data was collected';
