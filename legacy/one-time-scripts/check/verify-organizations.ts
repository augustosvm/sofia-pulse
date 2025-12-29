#!/usr/bin/env npx tsx
import { Pool } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DB || 'sofia_db',
});

async function verify() {
  const platforms = ['himalayas', 'adzuna', 'catho'];

  console.log('📊 Organization Linking Verification\n' + '='.repeat(70));

  for (const platform of platforms) {
    const result = await pool.query(`
      SELECT
        COUNT(*) as total_jobs,
        COUNT(organization_id) as jobs_with_org,
        COUNT(DISTINCT organization_id) as unique_orgs,
        ROUND(100.0 * COUNT(organization_id) / COUNT(*), 1) as coverage_pct
      FROM sofia.jobs
      WHERE platform = $1
    `, [platform]);

    const stats = result.rows[0];
    console.log(`\n${platform.toUpperCase()}:`);
    console.log(`  Total jobs: ${stats.total_jobs}`);
    console.log(`  With organization: ${stats.jobs_with_org} (${stats.coverage_pct}%)`);
    console.log(`  Unique companies: ${stats.unique_orgs}`);
  }

  console.log('\n' + '='.repeat(70));
  await pool.end();
}

verify().catch(console.error);
