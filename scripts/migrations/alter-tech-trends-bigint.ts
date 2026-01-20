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
    console.log('🐘 Migrating sofia.tech_trends columns to BIGINT...');

    try {
        await pool.query(`
            ALTER TABLE sofia.tech_trends 
            ALTER COLUMN score TYPE BIGINT,
            ALTER COLUMN views TYPE BIGINT,
            ALTER COLUMN stars TYPE BIGINT,
            ALTER COLUMN forks TYPE BIGINT;
        `);

        console.log('✅ Successfully altered columns to BIGINT.');

    } catch (err) {
        console.error('❌ Error altering table:', err);
    } finally {
        await pool.end();
    }
}

main();
