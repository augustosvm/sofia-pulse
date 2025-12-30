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

  console.log('🔍 Checking sofia.jobs table schema...\n');

  const result = await pool.query(`
    SELECT column_name, data_type, character_maximum_length, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'sofia' AND table_name = 'jobs'
    ORDER BY ordinal_position;
  `);

  console.log('📋 Columns in sofia.jobs:');
  console.log('='.repeat(80));
  result.rows.forEach(row => {
    const length = row.character_maximum_length ? `(${row.character_maximum_length})` : '';
    const nullable = row.is_nullable === 'YES' ? 'NULL' : 'NOT NULL';
    console.log(`  ${row.column_name.padEnd(25)} ${row.data_type.padEnd(20)} ${length.padEnd(8)} ${nullable}`);
  });
  console.log('='.repeat(80));
  console.log(`Total columns: ${result.rows.length}\n`);

  await pool.end();
}

main();
