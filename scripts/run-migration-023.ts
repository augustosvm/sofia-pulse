#!/usr/bin/env npx tsx
/**
 * Run migration 023: Add unique constraint on (job_id, platform)
 */

import { Pool } from 'pg';
import dotenv from 'dotenv';
import { readFileSync } from 'fs';
import { join } from 'path';

dotenv.config();

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

async function runMigration() {
    console.log('🔧 Running migration 023...');
    console.log('='.repeat(60));

    const pool = new Pool(dbConfig);

    try {
        // Read migration file
        const migrationPath = join(__dirname, '../migrations/023_add_job_id_platform_unique.sql');
        const migrationSQL = readFileSync(migrationPath, 'utf-8');

        // Run migration
        await pool.query(migrationSQL);

        console.log('✅ Migration completed successfully');

    } catch (error: any) {
        console.error('❌ Migration failed:', error.message);
        throw error;
    } finally {
        await pool.end();
    }
}

if (require.main === module) {
    runMigration()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Fatal error:', err);
            process.exit(1);
        });
}

export { runMigration };
