/**
 * Tech Conferences & Events Collector Configs
 *
 * Tracks tech conferences and events as a leading indicator for tech trends.
 *
 * Why this matters:
 * - New frameworks often announced at conferences
 * - Speaker topics = emerging technologies
 * - Attendance numbers = community size/growth
 * - Post-conference funding spikes
 *
 * Sources:
 * - Confs.tech API (open source conference tracker)
 * - Conference aggregators
 * - Tech event calendars
 */

import type { TechConferenceCollectorConfig } from '../collectors/tech-conferences-collector.js';

// ============================================================================
// CONFS.TECH (Open Source Conference Tracker)
// ============================================================================

export const confsTech: TechConferenceCollectorConfig = {
  name: 'confs-tech',
  displayName: '🎤 Confs.tech',
  url: 'https://raw.githubusercontent.com/tech-conferences/conference-data/main/conferences/2024.json',
  timeout: 30000,
  parseResponse: async (data) => {
    const conferences = Array.isArray(data) ? data : [];
    const now = new Date();
    const sixMonthsLater = new Date(now.getTime() + (180 * 24 * 60 * 60 * 1000));

    // Filter for upcoming conferences (next 6 months)
    const upcoming = conferences.filter((conf: any) => {
      const startDate = new Date(conf.startDate);
      return startDate >= now && startDate <= sixMonthsLater;
    });

    return upcoming.map((conf: any) => ({
      event_name: conf.name,
      event_type: 'conference',
      category: conf.category || conf.topics?.[0] || 'Technology',
      start_date: conf.startDate,
      end_date: conf.endDate,
      location_city: conf.city,
      location_country: conf.country,
      is_online: conf.online || false,
      website_url: conf.url,
      topics: conf.topics?.join(', ').slice(0, 255) || '',
      description: conf.description?.slice(0, 500),
      source: 'confs-tech',
    }));
  },
  schedule: '0 6 * * 1', // Weekly on Monday at 6am UTC
  description: 'Tech conferences from Confs.tech (open source tracker)',
  allowWithoutAuth: true,
};

// ============================================================================
// TECH EVENT AGGREGATOR (Placeholder for future expansion)
// ============================================================================

/*
// Future: Can add more sources like:
// - Meetup.com API (tech meetups)
// - Eventbrite API (tech events)
// - Lanyrd/Luma alternatives
// - Regional conference calendars

export const meetupTech: TechConferenceCollectorConfig = {
  name: 'meetup-tech',
  displayName: '🤝 Meetup.com Tech Events',
  url: (env) => `https://api.meetup.com/find/upcoming_events?key=${env.MEETUP_API_KEY}&topic_category=292`,
  headers: (env) => ({
    'Authorization': `Bearer ${env.MEETUP_API_KEY}`,
  }),
  parseResponse: async (data) => {
    const events = data?.events || [];
    return events.map((event: any) => ({
      event_name: event.name,
      event_type: 'meetup',
      category: 'Technology',
      start_date: new Date(event.time),
      end_date: new Date(event.time + event.duration),
      location_city: event.venue?.city,
      location_country: event.venue?.country,
      is_online: event.venue === null,
      website_url: event.link,
      attendee_count: event.yes_rsvp_count,
      source: 'meetup',
    }));
  },
  schedule: '0 7 * * 1', // Weekly on Monday at 7am UTC
  description: 'Tech meetups and events from Meetup.com',
  allowWithoutAuth: false, // Requires API key
};
*/

// ============================================================================
// EXPORT ALL COLLECTORS
// ============================================================================

export const techConferencesCollectors = {
  'confs-tech': confsTech,
  // 'meetup-tech': meetupTech, // Disabled until API key available
};
