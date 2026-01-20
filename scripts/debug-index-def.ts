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
    console.log('🔍 Checking index def...');
    const result = await pool.query(`
        SELECT indexdef 
        FROM pg_indexes 
        WHERE indexname = 'idx_jobs_unique_posting';
    `);

    if (result.rows.length > 0) {
        console.log(result.rows[0].indexdef);
    } else {
        console.log('Index not found.');
    }

    await pool.end();
}

main();
