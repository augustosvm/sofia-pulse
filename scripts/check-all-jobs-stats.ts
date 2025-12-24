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

async function checkAllJobsStats() {
    const client = new Client(DB_CONFIG);
    await client.connect();

    console.log('='.repeat(60));
    console.log('📊 ESTATÍSTICAS DE TODAS AS VAGAS');
    console.log('='.repeat(60));

    // Verificar tabela sofia.jobs (unificada)
    try {
        const jobsResult = await client.query(`
      SELECT 
        platform,
        COUNT(*) as total,
        COUNT(DISTINCT job_id) as unicos,
        COUNT(CASE WHEN collected_at::date = CURRENT_DATE THEN 1 END) as hoje
      FROM sofia.jobs 
      GROUP BY platform
      ORDER BY total DESC
    `);

        if (jobsResult.rows.length > 0) {
            console.log('\n📋 Tabela sofia.jobs (unificada):');
            console.log('-'.repeat(60));
            let totalGeral = 0;
            jobsResult.rows.forEach(row => {
                console.log(`  ${row.platform.padEnd(20)} | Total: ${String(row.total).padStart(5)} | Únicos: ${String(row.unicos).padStart(5)} | Hoje: ${String(row.hoje).padStart(5)}`);
                totalGeral += parseInt(row.total);
            });
            console.log('-'.repeat(60));
            console.log(`  TOTAL GERAL: ${totalGeral} vagas`);
        }
    } catch (err) {
        console.log('  ⚠️  Tabela sofia.jobs não existe ou está vazia');
    }

    // Verificar tabela catho_jobs
    try {
        const cathoResult = await client.query(`
      SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT job_id) as unicos,
        COUNT(CASE WHEN collected_at::date = CURRENT_DATE THEN 1 END) as hoje
      FROM sofia.catho_jobs
    `);

        if (cathoResult.rows[0].total > 0) {
            console.log('\n📋 Tabela sofia.catho_jobs (específica):');
            console.log('-'.repeat(60));
            const row = cathoResult.rows[0];
            console.log(`  Catho                | Total: ${String(row.total).padStart(5)} | Únicos: ${String(row.unicos).padStart(5)} | Hoje: ${String(row.hoje).padStart(5)}`);
        }
    } catch (err) {
        console.log('  ⚠️  Tabela sofia.catho_jobs não existe');
    }

    // Listar todas as tabelas relacionadas a jobs
    console.log('\n📁 Tabelas de jobs encontradas:');
    console.log('-'.repeat(60));
    const tablesResult = await client.query(`
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'sofia' 
    AND table_name LIKE '%job%'
    ORDER BY table_name
  `);

    tablesResult.rows.forEach(row => {
        console.log(`  - ${row.table_name}`);
    });

    console.log('='.repeat(60));

    await client.end();
}

checkAllJobsStats();
