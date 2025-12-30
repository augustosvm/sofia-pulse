#!/usr/bin/env tsx
import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import * as fs from 'fs';
import * as path from 'path';

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
    console.log('🔧 Applying migration 009: Add job_id UNIQUE constraint\n');

    const migrationPath = path.join(__dirname, '../db/migrations/009_add_job_id_unique_constraint.sql');
    const sql = fs.readFileSync(migrationPath, 'utf-8');

    await pool.query(sql);

    console.log('✅ Migration 009 applied successfully!\n');

  } catch (error: any) {
    console.error('❌ Error applying migration:', error.message);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
