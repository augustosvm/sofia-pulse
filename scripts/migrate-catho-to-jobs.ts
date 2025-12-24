#!/usr/bin/env tsx
/**
 * Script para migrar vagas da tabela catho_jobs para a tabela unificada sofia.jobs
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

async function migrateCathoJobs() {
  const client = new Client(DB_CONFIG);
  await client.connect();

  console.log('🔄 Migrando vagas do Catho para tabela unificada...');
  console.log('='.repeat(50));

  try {
    // Adicionar colunas city e state se não existirem
    await client.query(`
      ALTER TABLE sofia.jobs 
      ADD COLUMN IF NOT EXISTS city VARCHAR(100),
      ADD COLUMN IF NOT EXISTS state VARCHAR(50)
    `);

    console.log('✅ Colunas city e state adicionadas');

    // Migrar dados de catho_jobs para jobs
    const result = await client.query(`
      INSERT INTO sofia.jobs (job_id, title, company, location, city, state, url, platform, collected_at)
      SELECT 
        job_id,
        title,
        company,
        location,
        city,
        state,
        url,
        'catho' as platform,
        collected_at
      FROM sofia.catho_jobs
      ON CONFLICT (job_id) DO UPDATE SET
        title = EXCLUDED.title,
        company = EXCLUDED.company,
        location = EXCLUDED.location,
        city = EXCLUDED.city,
        state = EXCLUDED.state,
        collected_at = EXCLUDED.collected_at
      RETURNING job_id
    `);

    console.log(`✅ Migradas ${result.rowCount} vagas do Catho`);

    // Verificar total agora
    const countResult = await client.query(`
      SELECT COUNT(*) as count FROM sofia.jobs WHERE platform = 'catho'
    `);

    console.log(`📊 Total de vagas Catho em sofia.jobs: ${countResult.rows[0].count}`);
    console.log('='.repeat(50));
    console.log('✅ Migração concluída!');

  } catch (err) {
    console.error('❌ Erro na migração:', err);
  } finally {
    await client.end();
  }
}

migrateCathoJobs();
