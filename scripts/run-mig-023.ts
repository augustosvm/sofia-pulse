
import { Client } from 'pg';
import * as fs from 'fs';
import * as dotenv from 'dotenv';
dotenv.config();

const dbConfig = {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    user: process.env.DB_USER || 'sofia',
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME || 'sofia_db',
};

async function run() {
    const client = new Client(dbConfig);
    await client.connect();
    try {
        const sql = fs.readFileSync('db/migrations/023_create_industry_signals.sql', 'utf-8');
        await client.query(sql);
        console.log('✅ Migration 023 applied successfully');
    } catch (err) {
        console.error('❌ Migration failed:', err);
    } finally {
        client.end();
    }
}

run();
