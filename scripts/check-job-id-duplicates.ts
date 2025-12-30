#!/usr/bin/env tsx
import { Pool } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const DB_CONFIG = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD || 'sofia123strong',
  database: process.env.POSTGRES_DB || 'sofia_db',
};

async function main() {
  const pool = new Pool(DB_CONFIG);

  try {
    console.log('🔍 Checking for NULL job_ids...\n');

    const nulls = await pool.query(`
      SELECT COUNT(*) as count
      FROM sofia.jobs
      WHERE job_id IS NULL;
    `);

    console.log(`   NULL job_ids: ${nulls.rows[0].count}`);

    console.log('\n🔍 Checking for duplicate job_ids...\n');

    const duplicates = await pool.query(`
      SELECT job_id, COUNT(*) as count
      FROM sofia.jobs
      WHERE job_id IS NOT NULL
      GROUP BY job_id
      HAVING COUNT(*) > 1
      ORDER BY count DESC
      LIMIT 10;
    `);

    if (duplicates.rows.length > 0) {
      console.log(`   Found ${duplicates.rows.length} duplicate job_ids:\n`);
      duplicates.rows.forEach(row => {
        console.log(`   - ${row.job_id}: ${row.count} occurrences`);
      });
    } else {
      console.log('   ✅ No duplicates found!');
    }

    console.log('\n📊 Total jobs:\n');

    const total = await pool.query(`
      SELECT COUNT(*) as total,
             COUNT(DISTINCT job_id) as unique_job_ids,
             COUNT(*) FILTER (WHERE job_id IS NULL) as null_job_ids
      FROM sofia.jobs;
    `);

    const row = total.rows[0];
    console.log(`   Total: ${row.total}`);
    console.log(`   Unique job_ids: ${row.unique_job_ids}`);
    console.log(`   NULL job_ids: ${row.null_job_ids}\n`);

  } catch (error: any) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
