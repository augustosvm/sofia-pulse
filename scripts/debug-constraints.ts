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
    console.log('🔍 Checking sofia.jobs constraints...');
    const result = await pool.query(`
        SELECT conname, pg_get_constraintdef(c.oid)
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE n.nspname = 'sofia' AND c.conrelid = 'sofia.jobs'::regclass;
    `);

    result.rows.forEach(r => {
        console.log(`Constraint: ${r.conname} => ${r.pg_get_constraintdef}`);
    });

    console.log('\n🔍 Checking indexes...');
    const indexes = await pool.query(`
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'sofia' AND tablename = 'jobs';
    `);
    indexes.rows.forEach(r => {
        console.log(`Index: ${r.indexname} => ${r.indexdef}`);
    });

    await pool.end();
}

main();
