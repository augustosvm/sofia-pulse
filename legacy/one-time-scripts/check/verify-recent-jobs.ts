#!/usr/bin/env npx tsx
/**
 * Verify recent job insertions with normalization
 */
import { Pool } from 'pg';

const pool = new Pool({
  host: '91.98.158.19',
  port: 5432,
  user: 'sofia',
  password: 'sofia123strong',
  database: 'sofia_db',
});

async function verifyRecentJobs() {
  console.log('\n🔍 Checking most recent jobs from Adzuna...\n');

  const result = await pool.query(`
    SELECT
      j.job_id,
      j.title,
      j.location,
      j.country,
      j.state,
      j.city,
      c.common_name as country_name,
      s.name as state_name,
      ct.name as city_name,
      j.created_at
    FROM sofia.jobs j
    LEFT JOIN sofia.countries c ON j.country_id = c.id
    LEFT JOIN sofia.states s ON j.state_id = s.id
    LEFT JOIN sofia.cities ct ON j.city_id = ct.id
    WHERE j.platform = 'adzuna'
    ORDER BY j.created_at DESC
    LIMIT 20
  `);

  console.log('Recent Jobs with Normalization:\n');
  console.log('─'.repeat(120));

  for (const job of result.rows) {
    const raw = `Raw: ${job.city || 'null'}/${job.state || 'null'}/${job.country || 'null'}`;
    const normalized = `Normalized: ${job.city_name || 'NULL'}/${job.state_name || 'NULL'}/${job.country_name || 'NULL'}`;

    console.log(`\n📍 ${job.title.substring(0, 50)}...`);
    console.log(`   Location: ${job.location || 'N/A'}`);
    console.log(`   ${raw}`);
    console.log(`   ${normalized}`);

    // Highlight normalization success
    if (job.country_name && !job.city && !job.state) {
      console.log(`   ✅ Country-only normalized correctly`);
    } else if (job.city_name) {
      console.log(`   ✅ Full normalization successful`);
    } else if (!job.country_name) {
      console.log(`   ⚠️  No normalization (invalid location data)`);
    }
  }

  console.log('\n' + '─'.repeat(120));

  // Summary stats
  const stats = await pool.query(`
    SELECT
      COUNT(*) as total,
      COUNT(country_id) as with_country,
      COUNT(city_id) as with_city,
      ROUND(100.0 * COUNT(country_id) / COUNT(*), 1) as country_pct,
      ROUND(100.0 * COUNT(city_id) / COUNT(*), 1) as city_pct
    FROM sofia.jobs
    WHERE platform = 'adzuna'
  `);

  const s = stats.rows[0];
  console.log('\n📊 Adzuna Jobs Normalization Coverage:');
  console.log(`   Total: ${s.total} jobs`);
  console.log(`   Country ID: ${s.with_country} (${s.country_pct}%)`);
  console.log(`   City ID: ${s.with_city} (${s.city_pct}%)`);
  console.log('');

  await pool.end();
}

verifyRecentJobs().catch(console.error);
