#!/usr/bin/env node

// Fix for Node.js 18 + undici - MUST BE AFTER SHEBANG!
// @ts-ignore
if (typeof File === 'undefined') {
  // @ts-ignore
  globalThis.File = class File extends Blob {
    constructor(bits: any[], name: string, options?: any) {
      super(bits, options);
    }
  };
}

/**
 * Space Industry Collector - Sofia Pulse
 *
 * Coleta dados de:
 * - Rocket launches (via Launch Library 2 API)
 * - Space missions
 * - Company info
 */

import { normalizeLocation } from './shared/geo-helpers';
import { Pool } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  user: process.env.DB_USER || 'sofia',
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME || 'sofia_db',
});

interface SpaceEvent {
  event_type: string;
  mission_name: string | null;
  company: string | null;
  launch_date: Date | null;
  launch_site: string | null;
  rocket_type: string | null;
  payload_type: string | null;
  payload_count: number | null;
  orbit_type: string | null;
  status: string | null;
  customers: string[] | null;
  contract_value_usd: number | null;
  country: string | null;
  description: string | null;
  source: string;
  source_url: string | null;
}

/**
 * Coleta lançamentos recentes via Launch Library 2 API
 */
async function collectLaunches(): Promise<SpaceEvent[]> {
  console.log('📡 Fetching rocket launches from Launch Library 2...');

  try {
    // Get upcoming and recent launches
    const response = await fetch(
      'https://ll.thespacedevs.com/2.2.0/launch/?limit=100&mode=detailed',
      {
        headers: {
          'User-Agent': 'Sofia-Pulse/1.0'
        }
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    const events: SpaceEvent[] = [];

    for (const launch of data.results || []) {
      // Extract company from launch service provider
      const company = launch.launch_service_provider?.name || null;
      const country = launch.pad?.location?.country_code || null;

      // Extract payload info
      const payloads = launch.mission?.orbit?.name ?
        [launch.mission.orbit.name] : null;
      const orbitType = launch.mission?.orbit?.name || null;

      events.push({
        event_type: 'launch',
        mission_name: launch.name,
        company,
        launch_date: launch.net ? new Date(launch.net) : null,
        launch_site: launch.pad?.name || null,
        rocket_type: launch.rocket?.configuration?.name || null,
        payload_type: launch.mission?.type || null,
        payload_count: launch.mission ? 1 : null,
        orbit_type: orbitType,
        status: launch.status?.name?.toLowerCase() || null,
        customers: null, // Not easily available in free API
        contract_value_usd: null,
        country,
        description: launch.mission?.description || null,
        source: 'launch_library',
        source_url: launch.slug ? `https://thespacedevs.com/launch/${launch.slug}` : null,
      });
    }

    console.log(`   ✅ Collected ${events.length} launches`);
    return events;

  } catch (error: any) {
    console.error(`   ❌ Error collecting launches: ${error.message}`);
    return [];
  }
}

/**
 * Parse company name to standardize
 */
function parseCompany(name: string | null): string | null {
  if (!name) return null;

  const mapping: Record<string, string> = {
    'spacex': 'SpaceX',
    'space exploration technologies': 'SpaceX',
    'blue origin': 'Blue Origin',
    'virgin galactic': 'Virgin Galactic',
    'virgin orbit': 'Virgin Orbit',
    'rocket lab': 'Rocket Lab',
    'united launch alliance': 'ULA',
    'ula': 'ULA',
    'arianespace': 'Arianespace',
    'roscosmos': 'Roscosmos',
    'cnsa': 'CNSA',
    'isro': 'ISRO',
    'jaxa': 'JAXA',
    'nasa': 'NASA',
  };

  const lower = name.toLowerCase();
  for (const [key, value] of Object.entries(mapping)) {
    if (lower.includes(key)) {
      return value;
    }
  }

  return name;
}

/**
 * Salva eventos no banco
 */
async function saveEvents(events: SpaceEvent[]): Promise<void> {
  if (events.length === 0) {
    console.log('   ⚠️  No events to save');
    return;
  }

  const client = await pool.connect();

  try {
    let inserted = 0;
    let skipped = 0;

    for (const event of events) {
      try {
        // Normalize company name
        const company = parseCompany(event.company);

        await client.query(
          `
          INSERT INTO sofia.space_industry (
            event_type, mission_name, company, launch_date,
            launch_site, rocket_type, payload_type, payload_count,
            orbit_type, status, customers, contract_value_usd,
            country, description, source, source_url
          , country_id)
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
          ON CONFLICT DO NOTHING
          `,
          [
            event.event_type,
            event.mission_name,
            company,
            event.launch_date,
            event.launch_site,
            event.rocket_type,
            event.payload_type,
            event.payload_count,
            event.orbit_type,
            event.status,
            event.customers,
            event.contract_value_usd,
            event.country,
            event.description,
            event.source,
            event.source_url,
          ]
        );
        inserted++;
      } catch (err: any) {
        // Skip duplicates
        if (err.code !== '23505') { // Not unique violation
          console.error(`   ⚠️  Error inserting event: ${err.message}`);
        }
        skipped++;
      }
    }

    console.log(`   ✅ Inserted: ${inserted}, Skipped: ${skipped}`);

  } finally {
    client.release();
  }
}

/**
 * Get statistics
 */
async function getStats(): Promise<void> {
  const client = await pool.connect();

  try {
    const result = await client.query(`
      SELECT
        company,
        COUNT(*) as launch_count,
        COUNT(*) FILTER (WHERE status = 'success') as successful,
        COUNT(*) FILTER (WHERE launch_date >= CURRENT_DATE - INTERVAL '30 days') as recent_30d
      FROM sofia.space_industry
      WHERE event_type = 'launch'
        AND company IS NOT NULL
      GROUP BY company
      ORDER BY launch_count DESC
      LIMIT 10
    `);

    console.log('');
    console.log('📊 TOP LAUNCH PROVIDERS:');
    console.log('─'.repeat(60));

    for (const row of result.rows) {
      console.log(
        `   ${row.company}: ${row.launch_count} total ` +
        `(${row.successful} successful, ${row.recent_30d} in last 30d)`
      );
    }

  } finally {
    client.release();
  }
}

async function main() {
  console.log('════════════════════════════════════════════════════════════════');
  console.log('🚀 SPACE INDUSTRY COLLECTOR');
  console.log('════════════════════════════════════════════════════════════════');
  console.log('');

  try {
    // Collect launches
    const launches = await collectLaunches();

    console.log('');
    console.log(`📊 Total collected: ${launches.length} events`);
    console.log('');

    // Save to database
    console.log('💾 Saving to database...');
    await saveEvents(launches);

    // Show stats
    await getStats();

    console.log('');
    console.log('✅ Space industry collection complete!');
    console.log('');

  } catch (error: any) {
    console.error(`❌ Error: ${error.message}`);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
