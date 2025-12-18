#!/usr/bin/env tsx
import { Client } from 'pg';
import * as dotenv from 'dotenv';

dotenv.config();

const DB_CONFIG = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD || 'sofia123strong',
    database: process.env.POSTGRES_DB || 'sofia_db',
};

async function checkCathoStats() {
    const client = new Client(DB_CONFIG);
    await client.connect();

    console.log('='.repeat(50));
    console.log('📊 ESTATÍSTICAS CATHO');
    console.log('='.repeat(50));

    // Total
    const totalResult = await client.query(
        "SELECT COUNT(*) as count FROM sofia.catho_jobs"
    );
    console.log(`Total de vagas: ${totalResult.rows[0].count}`);

    // Únicos
    const unicosResult = await client.query(
        "SELECT COUNT(DISTINCT job_id) as count FROM sofia.catho_jobs"
    );
    console.log(`Vagas únicas (job_id): ${unicosResult.rows[0].count}`);

    // Hoje
    const hojeResult = await client.query(
        "SELECT COUNT(*) as count FROM sofia.catho_jobs WHERE collected_at::date = CURRENT_DATE"
    );
    console.log(`Coletadas hoje: ${hojeResult.rows[0].count}`);

    // Últimas 5 vagas
    const lastJobs = await client.query(
        "SELECT title, company, location, collected_at FROM sofia.catho_jobs ORDER BY collected_at DESC LIMIT 5"
    );

    console.log('\n📋 Últimas 5 vagas coletadas:');
    lastJobs.rows.forEach((job, i) => {
        console.log(`${i + 1}. ${job.title} - ${job.company} (${job.location})`);
    });

    console.log('='.repeat(50));

    await client.end();
}

checkCathoStats();
