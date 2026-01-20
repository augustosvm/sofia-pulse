import { Pool } from 'pg';
import * as dotenv from 'dotenv';
dotenv.config();

const pool = new Pool({
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD || 'sofia123strong',
    database: process.env.POSTGRES_DB || 'sofia_db',
});

async function main() {
    console.log('🔍 Checking for "source" column in sofia.jobs...');
    try {
        const result = await pool.query(`
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' AND table_name = 'jobs' AND column_name = 'source';
        `);

        if (result.rows.length > 0) {
            console.log('✅ "source" column ALREADY EXISTS.');
        } else {
            console.log('⚠️ "source" column MISSING. Adding it now...');
            await pool.query(`
                ALTER TABLE sofia.jobs 
                ADD COLUMN source VARCHAR(50);
            `);
            await pool.query(`
                CREATE INDEX IF NOT EXISTS idx_jobs_source ON sofia.jobs(source);
            `);
            console.log('✅ "source" column ADDED successfully.');
        }
    } catch (error) {
        console.error('❌ Error checking/adding column:', error);
    } finally {
        await pool.end();
    }
}

main();
