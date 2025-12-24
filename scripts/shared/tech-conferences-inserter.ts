/**
 * Tech Conferences & Events Inserter - TypeScript
 *
 * Unified inserter for all tech conference data sources.
 * Inserts into sofia.tech_conferences table.
 *
 * Features:
 * - Deduplication via unique constraint (event_name + start_date)
 * - ON CONFLICT handling (updates on duplicates)
 * - Batch insert support
 * - Tracks conference trends over time
 */

import { Pool, PoolClient } from 'pg';

// ============================================================================
// TYPES
// ============================================================================

export interface TechConferenceData {
  event_name: string;
  event_type: 'conference' | 'meetup' | 'workshop' | 'webinar' | 'hackathon';
  category?: string | null;
  start_date: Date | string;
  end_date?: Date | string | null;
  location_city?: string | null;
  location_country?: string | null;
  is_online?: boolean;
  website_url?: string | null;
  topics?: string | null;
  description?: string | null;
  attendee_count?: number | null;
  speaker_count?: number | null;
  organizer?: string | null;
  source: string;
  metadata?: Record<string, any>;
}

// ============================================================================
// TECH CONFERENCES INSERTER
// ============================================================================

export class TechConferencesInserter {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  /**
   * Insert tech conference into database
   */
  async insertTechConference(
    conference: TechConferenceData,
    client?: PoolClient
  ): Promise<void> {
    const db = client || this.pool;

    // Validate required fields
    if (!conference.event_name || !conference.start_date) {
      throw new Error('Missing required fields: event_name, start_date');
    }

    // Prepare dates
    let startDate: Date;
    if (typeof conference.start_date === 'string') {
      startDate = new Date(conference.start_date);
    } else {
      startDate = conference.start_date;
    }

    let endDate: Date | null = null;
    if (conference.end_date) {
      endDate = typeof conference.end_date === 'string'
        ? new Date(conference.end_date)
        : conference.end_date;
    }

    const query = `
      INSERT INTO sofia.tech_conferences (
        event_name,
        event_type,
        category,
        start_date,
        end_date,
        location_city,
        location_country,
        is_online,
        website_url,
        topics,
        description,
        attendee_count,
        speaker_count,
        organizer,
        source,
        collected_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, NOW())
      ON CONFLICT (event_name, start_date)
      DO UPDATE SET
        event_type = EXCLUDED.event_type,
        category = COALESCE(EXCLUDED.category, sofia.tech_conferences.category),
        end_date = COALESCE(EXCLUDED.end_date, sofia.tech_conferences.end_date),
        location_city = COALESCE(EXCLUDED.location_city, sofia.tech_conferences.location_city),
        location_country = COALESCE(EXCLUDED.location_country, sofia.tech_conferences.location_country),
        is_online = EXCLUDED.is_online,
        website_url = COALESCE(EXCLUDED.website_url, sofia.tech_conferences.website_url),
        topics = COALESCE(EXCLUDED.topics, sofia.tech_conferences.topics),
        description = COALESCE(EXCLUDED.description, sofia.tech_conferences.description),
        attendee_count = COALESCE(EXCLUDED.attendee_count, sofia.tech_conferences.attendee_count),
        speaker_count = COALESCE(EXCLUDED.speaker_count, sofia.tech_conferences.speaker_count),
        organizer = COALESCE(EXCLUDED.organizer, sofia.tech_conferences.organizer),
        source = EXCLUDED.source,
        collected_at = NOW()
    `;

    await db.query(query, [
      conference.event_name,
      conference.event_type,
      conference.category || null,
      startDate,
      endDate,
      conference.location_city || null,
      conference.location_country || null,
      conference.is_online !== undefined ? conference.is_online : false,
      conference.website_url || null,
      conference.topics || null,
      conference.description || null,
      conference.attendee_count || null,
      conference.speaker_count || null,
      conference.organizer || null,
      conference.source || 'unknown',
    ]);
  }

  /**
   * Batch insert tech conferences (with transaction)
   */
  async batchInsert(conferences: TechConferenceData[]): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      for (const conference of conferences) {
        await this.insertTechConference(conference, client);
      }
      await client.query('COMMIT');
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Get statistics
   */
  async getStats(): Promise<any> {
    const query = `
      SELECT
        event_type,
        COUNT(*) as total_events,
        COUNT(DISTINCT category) as unique_categories,
        AVG(attendee_count) as avg_attendees,
        MAX(attendee_count) as max_attendees,
        COUNT(CASE WHEN is_online THEN 1 END) as online_events,
        COUNT(CASE WHEN start_date >= CURRENT_DATE THEN 1 END) as upcoming_events,
        COUNT(CASE WHEN start_date >= CURRENT_DATE AND start_date < CURRENT_DATE + INTERVAL '30 days' THEN 1 END) as next_30_days
      FROM sofia.tech_conferences
      GROUP BY event_type
      ORDER BY total_events DESC;
    `;

    const result = await this.pool.query(query);
    return result.rows;
  }

  /**
   * Get upcoming conferences by topic
   */
  async getUpcomingByTopic(topic: string, limit: number = 20): Promise<any[]> {
    const query = `
      SELECT
        event_name,
        event_type,
        category,
        start_date,
        end_date,
        location_city,
        location_country,
        is_online,
        website_url,
        topics,
        attendee_count
      FROM sofia.tech_conferences
      WHERE
        start_date >= CURRENT_DATE
        AND (
          topics ILIKE '%' || $1 || '%'
          OR category ILIKE '%' || $1 || '%'
          OR event_name ILIKE '%' || $1 || '%'
        )
      ORDER BY start_date ASC
      LIMIT $2;
    `;

    const result = await this.pool.query(query, [topic, limit]);
    return result.rows;
  }
}

// ============================================================================
// EXAMPLE USAGE
// ============================================================================

/*
const inserter = new TechConferencesInserter(pool);

// Insert single conference
await inserter.insertTechConference({
  event_name: 'React Conf 2025',
  event_type: 'conference',
  category: 'JavaScript',
  start_date: new Date('2025-05-15'),
  end_date: new Date('2025-05-17'),
  location_city: 'San Francisco',
  location_country: 'USA',
  is_online: false,
  website_url: 'https://conf.react.dev',
  topics: 'React, JavaScript, Web Development',
  description: 'The official React conference',
  attendee_count: 1500,
  speaker_count: 25,
  source: 'confs-tech',
});

// Get stats
const stats = await inserter.getStats();
console.log(stats);

// Get upcoming React events
const reactEvents = await inserter.getUpcomingByTopic('React', 10);
console.log(reactEvents);
*/
