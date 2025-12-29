#!/usr/bin/env npx tsx
/**
 * Backfill Script: Update job city_id using new intelligent fallbacks
 *
 * This script:
 * 1. Reads all jobs without city_id
 * 2. Applies normalizeLocation() with new fallbacks ("Paulo" → "São Paulo", etc.)
 * 3. Updates jobs with normalized geographic IDs
 *
 * Run: npx tsx scripts/backfill-job-cities.ts
 */

import { Pool } from 'pg';
import { normalizeLocation } from './shared/geo-helpers.js';

const pool = new Pool({
  host: process.env.DB_HOST || '91.98.158.19',
  port: parseInt(process.env.DB_PORT || '5432'),
  user: process.env.DB_USER || 'sofia',
  password: process.env.DB_PASSWORD || 'sofia123strong',
  database: process.env.DB_NAME || 'sofia_db',
});

interface Job {
  id: number;
  job_id: string;
  platform: string;
  country: string | null;
  state: string | null;
  city: string | null;
  location: string | null;
}

async function backfillJobCities() {
  console.log('🔄 Starting job city backfill...\n');

  try {
    // Get jobs without city_id but with location data
    const result = await pool.query<Job>(`
      SELECT id, job_id, platform, country, state, city, location
      FROM sofia.jobs
      WHERE city_id IS NULL
      ORDER BY id
    `);

    const jobs = result.rows;
    console.log(`📊 Found ${jobs.length} jobs without city_id\n`);

    if (jobs.length === 0) {
      console.log('✅ All jobs already have city_id!');
      return;
    }

    let updated = 0;
    let skipped = 0;
    let errors = 0;

    // Process in batches
    const batchSize = 100;
    for (let i = 0; i < jobs.length; i += batchSize) {
      const batch = jobs.slice(i, i + batchSize);

      for (const job of batch) {
        try {
          // Try to normalize location using new fallbacks
          const { countryId, stateId, cityId } = await normalizeLocation(pool, {
            country: job.country || job.location,
            state: job.state,
            city: job.city || job.location,
          });

          // Only update if we found at least a country
          if (countryId) {
            await pool.query(
              `UPDATE sofia.jobs
               SET country_id = $1, state_id = $2, city_id = $3
               WHERE id = $4`,
              [countryId, stateId, cityId, job.id]
            );

            updated++;

            if (cityId && (i + batch.indexOf(job)) % 50 === 0) {
              console.log(
                `✅ [${i + batch.indexOf(job) + 1}/${jobs.length}] Updated: ${job.platform}/${
                  job.job_id
                } - ${job.city || job.location}`
              );
            }
          } else {
            skipped++;
          }
        } catch (error) {
          errors++;
          console.error(
            `❌ Error updating job ${job.id} (${job.platform}/${job.job_id}):`,
            error instanceof Error ? error.message : error
          );
        }
      }

      // Log progress every batch
      if ((i + batchSize) % 1000 === 0) {
        console.log(`\n📈 Progress: ${i + batchSize}/${jobs.length} processed\n`);
      }
    }

    // Final statistics
    console.log('\n========================================');
    console.log('BACKFILL RESULTS');
    console.log('========================================');
    console.log(`Total jobs processed: ${jobs.length}`);
    console.log(`✅ Updated: ${updated}`);
    console.log(`⏭️  Skipped: ${skipped}`);
    console.log(`❌ Errors: ${errors}`);

    // Check final coverage
    const coverage = await pool.query(`
      SELECT
        COUNT(*) as total,
        COUNT(country_id) as with_country,
        COUNT(city_id) as with_city,
        ROUND(100.0 * COUNT(country_id) / COUNT(*), 1) as country_pct,
        ROUND(100.0 * COUNT(city_id) / COUNT(*), 1) as city_pct
      FROM sofia.jobs
    `);

    const stats = coverage.rows[0];
    console.log('\nFinal Coverage:');
    console.log(`  Country: ${stats.with_country}/${stats.total} (${stats.country_pct}%)`);
    console.log(`  City: ${stats.with_city}/${stats.total} (${stats.city_pct}%)`);
    console.log('========================================\n');
  } catch (error) {
    console.error('❌ Backfill failed:', error);
    throw error;
  } finally {
    await pool.end();
  }
}

// Run backfill
backfillJobCities().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
