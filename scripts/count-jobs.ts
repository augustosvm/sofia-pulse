#!/usr/bin/env npx tsx
import { Client } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const client = new Client({
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
});

async function countJobs() {
    await client.connect();
    const result = await client.query('SELECT COUNT(*) as total FROM sofia.jobs');
    console.log(`Total de vagas no banco: ${result.rows[0].total}`);

    const byPlatform = await client.query(`
        SELECT platform, COUNT(*) as count 
        FROM sofia.jobs 
        GROUP BY platform 
        ORDER BY count DESC
    `);
    console.log('\nPor plataforma:');
    byPlatform.rows.forEach(r => console.log(`  ${r.platform}: ${r.count}`));

    await client.end();
}

countJobs().catch(console.error);
