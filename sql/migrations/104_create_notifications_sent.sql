-- Migration: Create Notifications Sent Table (WhatsApp Dedupe)
-- Purpose: Track sent notifications to prevent duplicates
-- Date: 2025-12-10

CREATE TABLE IF NOT EXISTS sofia.notifications_sent (
  notification_id SERIAL PRIMARY KEY,
  
  -- Dedupe key
  date_brt DATE NOT NULL,           -- Date in America/Sao_Paulo timezone
  channel VARCHAR(50) NOT NULL,     -- whatsapp, email, slack, etc
  message_hash VARCHAR(64) NOT NULL, -- SHA256 hash of message content
  
  -- Notification data
  recipient VARCHAR(255),
  severity VARCHAR(20),             -- info, warning, critical
  title VARCHAR(500),
  message_preview TEXT,             -- First 200 chars
  
  -- Metadata
  sent_at TIMESTAMP DEFAULT NOW(),
  trace_id UUID,
  
  -- Unique constraint (1 message per channel per day)
  CONSTRAINT notifications_sent_unique UNIQUE (date_brt, channel, message_hash)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_notifications_sent_date ON sofia.notifications_sent(date_brt DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_channel ON sofia.notifications_sent(channel);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_severity ON sofia.notifications_sent(severity);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_sent_at ON sofia.notifications_sent(sent_at DESC);

-- Comments
COMMENT ON TABLE sofia.notifications_sent IS 'Track sent notifications to prevent duplicates (anti-spam)';
COMMENT ON COLUMN sofia.notifications_sent.date_brt IS 'Date in BRT timezone (for daily dedupe)';
COMMENT ON COLUMN sofia.notifications_sent.message_hash IS 'SHA256 hash of message content for deduplication';

-- Cleanup function (delete old records)
CREATE OR REPLACE FUNCTION cleanup_old_notifications()
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM sofia.notifications_sent
  WHERE date_brt < CURRENT_DATE - INTERVAL '30 days';
  
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_notifications() IS 'Delete notifications older than 30 days (call from cron)';
