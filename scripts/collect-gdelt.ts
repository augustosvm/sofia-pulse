#!/usr/bin/env tsx

import { Client } from 'pg';
import * as dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

const dbConfig = {
  host: process.env.DB_HOST || process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || process.env.POSTGRES_PORT || '5432'),
  user: process.env.DB_USER || process.env.POSTGRES_USER || 'sofia',
  password: process.env.DB_PASSWORD || process.env.POSTGRES_PASSWORD,
  database: process.env.DB_NAME || process.env.POSTGRES_DB || 'sofia_db',
};

interface GDELTEvent {
  event_id: string;
  event_date: string;
  actor1_name: string;
  actor1_country: string;
  actor2_name: string;
  actor2_country: string;
  event_code: string;
  goldstein_scale: number;
  num_mentions: number;
  num_sources: number;
  num_articles: number;
  avg_tone: number;
  action_geo_country: string;
  source_url: string;
  categories: string[];
  is_tech_related: boolean;
  is_market_relevant: boolean;
}

async function fetchGDELTEvents(): Promise<GDELTEvent[]> {
  // GDELT DOC 2.0 API
  const now = new Date();
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const dateStr = yesterday.toISOString().slice(0, 10).replace(/-/g, '');

  // Keywords tech-related
  const keywords = [
    'technology', 'AI', 'artificial intelligence', 'semiconductor',
    'chip', 'tech company', 'startup', 'IPO', 'funding',
    'cybersecurity', 'data breach', 'regulation tech',
    'antitrust tech', 'patent', 'innovation'
  ];

  const events: GDELTEvent[] = [];

  for (const keyword of keywords.slice(0, 3)) { // Limit to avoid rate limits
    const url = `https://api.gdeltproject.org/api/v2/doc/doc?query=${encodeURIComponent(keyword)}&mode=artlist&format=json&maxrecords=50&startdatetime=${dateStr}000000&enddatetime=${dateStr}235959`;

    try {
      const response = await axios.get(url, { timeout: 30000 });

      if (response.data && response.data.articles) {
        for (const article of response.data.articles.slice(0, 20)) {
          const event: GDELTEvent = {
            event_id: `${dateStr}-${article.url_hash || Math.random().toString(36).substr(2, 9)}`,
            event_date: `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`,
            actor1_name: article.domain || 'Unknown',
            actor1_country: article.sourcelang === 'eng' ? 'US' : 'XX',
            actor2_name: '',
            actor2_country: '',
            event_code: '010',
            goldstein_scale: parseFloat(article.tone) || 0,
            num_mentions: 1,
            num_sources: 1,
            num_articles: 1,
            avg_tone: parseFloat(article.tone) || 0,
            action_geo_country: article.sourcelang === 'eng' ? 'US' : 'XX',
            source_url: article.url || '',
            categories: [keyword],
            is_tech_related: true,
            is_market_relevant: article.tone < -5 || article.tone > 5,
          };

          events.push(event);
        }
      }

      await new Promise(resolve => setTimeout(resolve, 2000));
    } catch (error: any) {
      console.error(`Error fetching GDELT for ${keyword}:`, error.message);
    }
  }

  return events;
}

async function insertEvent(client: Client, event: GDELTEvent): Promise<void> {
  const query = `
    INSERT INTO sofia.gdelt_events (
      event_id, event_date, actor1_name, actor1_country, actor2_name, actor2_country,
      event_code, goldstein_scale, num_mentions, num_sources, num_articles, avg_tone,
      action_geo_country, source_url, categories, is_tech_related, is_market_relevant
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
    ON CONFLICT (event_id) DO NOTHING;
  `;

  await client.query(query, [
    event.event_id,
    event.event_date,
    event.actor1_name,
    event.actor1_country,
    event.actor2_name,
    event.actor2_country,
    event.event_code,
    event.goldstein_scale,
    event.num_mentions,
    event.num_sources,
    event.num_articles,
    event.avg_tone,
    event.action_geo_country,
    event.source_url,
    event.categories,
    event.is_tech_related,
    event.is_market_relevant,
  ]);
}

async function main() {
  console.log('🌍 GDELT Geopolitical Events Collector');
  console.log('='.repeat(60));

  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('✅ Connected to PostgreSQL');

    const fs = await import('fs/promises');
    const migrationSQL = await fs.readFile('db/migrations/011_create_gdelt_events.sql', 'utf-8');
    await client.query(migrationSQL);
    console.log('✅ Migration complete');

    console.log('📊 Fetching GDELT events...');
    const events = await fetchGDELTEvents();
    console.log(`   ✅ Fetched ${events.length} events`);

    console.log('💾 Inserting into database...');
    for (const event of events) {
      await insertEvent(client, event);
    }
    console.log(`✅ ${events.length} events inserted`);

    const summary = await client.query(`
      SELECT COUNT(*) as total,
             AVG(avg_tone) as avg_tone,
             COUNT(*) FILTER (WHERE is_market_relevant) as market_relevant
      FROM sofia.gdelt_events
      WHERE event_date >= CURRENT_DATE - INTERVAL '7 days';
    `);

    console.log('');
    console.log('📊 Summary (last 7 days):');
    console.log(`   Total events: ${summary.rows[0].total}`);
    console.log(`   Avg tone: ${parseFloat(summary.rows[0].avg_tone).toFixed(2)}`);
    console.log(`   Market relevant: ${summary.rows[0].market_relevant}`);

  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

if (require.main === module) {
  main();
}
