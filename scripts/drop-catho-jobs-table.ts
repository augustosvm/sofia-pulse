#!/usr/bin/env tsx
/**
 * Script para remover a tabela catho_jobs após migração bem-sucedida
 */
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

async function dropCathoJobsTable() {
    const client = new Client(DB_CONFIG);
    await client.connect();

    console.log('🗑️  Removendo tabela catho_jobs...');
    console.log('='.repeat(50));

    try {
        // Verificar quantas vagas do Catho temos em sofia.jobs
        const cathoCount = await client.query(`
      SELECT COUNT(*) as count FROM sofia.jobs WHERE platform = 'catho'
    `);

        console.log(`✅ Vagas do Catho em sofia.jobs: ${cathoCount.rows[0].count}`);

        // Verificar quantas vagas temos em catho_jobs
        const oldCount = await client.query(`
      SELECT COUNT(*) as count FROM sofia.catho_jobs
    `);

        console.log(`📊 Vagas em catho_jobs (antiga): ${oldCount.rows[0].count}`);

        if (cathoCount.rows[0].count >= oldCount.rows[0].count) {
            // Seguro para deletar
            await client.query(`DROP TABLE IF EXISTS sofia.catho_jobs CASCADE`);
            console.log('✅ Tabela catho_jobs removida com sucesso!');
        } else {
            console.log('⚠️  ATENÇÃO: Menos vagas em sofia.jobs do que em catho_jobs!');
            console.log('   Não é seguro remover a tabela antiga.');
        }

        console.log('='.repeat(50));

    } catch (err) {
        console.error('❌ Erro:', err);
    } finally {
        await client.end();
    }
}

dropCathoJobsTable();
