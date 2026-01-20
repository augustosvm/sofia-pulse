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
    console.log('🔍 Checking sofia.jobs columns...');
    const result = await pool.query(`
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'sofia' AND table_name = 'jobs'
        ORDER BY column_name;
    `);

    const cols = result.rows.map(r => r.column_name);
    console.log('Columns:', cols.join(', '));

    // Check specific critical columns
    console.log('Has "location"?', cols.includes('location'));
    console.log('Has "raw_location"?', cols.includes('raw_location'));
    console.log('Has "city"?', cols.includes('city'));
    console.log('Has "raw_city"?', cols.includes('raw_city'));
    console.log('Has "company"?', cols.includes('company'));
    console.log('Has "raw_company"?', cols.includes('raw_company'));

    await pool.end();
}

main();
