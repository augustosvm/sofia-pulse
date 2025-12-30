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
    console.log('🧹 Cleaning duplicate job_ids...\n');

    console.log('📊 Before cleanup:');
    const before = await pool.query(`SELECT COUNT(*) as total FROM sofia.jobs`);
    console.log(`   Total jobs: ${before.rows[0].total}\n`);

    // Delete duplicates, keeping only the most recent (highest id)
    const result = await pool.query(`
      DELETE FROM sofia.jobs
      WHERE id IN (
        SELECT id
        FROM (
          SELECT id,
                 ROW_NUMBER() OVER (PARTITION BY job_id ORDER BY collected_at DESC NULLS LAST, id DESC) as rn
          FROM sofia.jobs
        ) t
        WHERE rn > 1
      )
    `);

    console.log(`✅ Deleted ${result.rowCount} duplicate jobs\n`);

    console.log('📊 After cleanup:');
    const after = await pool.query(`SELECT COUNT(*) as total, COUNT(DISTINCT job_id) as unique_ids FROM sofia.jobs`);
    console.log(`   Total jobs: ${after.rows[0].total}`);
    console.log(`   Unique job_ids: ${after.rows[0].unique_ids}\n`);

  } catch (error: any) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
