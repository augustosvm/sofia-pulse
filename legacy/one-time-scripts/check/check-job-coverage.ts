#!/usr/bin/env npx tsx
/**
 * Quick check of job normalization coverage
 */
import { Pool } from 'pg';

const pool = new Pool({
  host: '91.98.158.19',
  port: 5432,
  user: 'sofia',
  password: 'sofia123strong',
  database: 'sofia_db',
});

async function checkCoverage() {
  const result = await pool.query(`
    SELECT
      COUNT(*) as total_jobs,
      COUNT(country_id) as with_country,
      COUNT(city_id) as with_city,
      ROUND(100.0 * COUNT(country_id) / COUNT(*), 1) as country_pct,
      ROUND(100.0 * COUNT(city_id) / COUNT(*), 1) as city_pct
    FROM sofia.jobs
  `);

  const stats = result.rows[0];
  console.log('\n📊 Job Geographic Coverage:');
  console.log(`  Total jobs: ${stats.total_jobs}`);
  console.log(`  With country_id: ${stats.with_country} (${stats.country_pct}%)`);
  console.log(`  With city_id: ${stats.with_city} (${stats.city_pct}%)`);

  await pool.end();
}

checkCoverage().catch(console.error);
