#!/usr/bin/env npx tsx
/**
 * Backfill Geographic IDs with Intelligent Fallbacks
 *
 * Popula country_id, state_id, city_id usando os helpers com fallbacks inteligentes
 * Processa registros em batch para performance
 */

import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import { normalizeLocation } from './shared/geo-helpers.js';

dotenv.config();

const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DB || 'sofia_db',
});

async function backfillJobs() {
  console.log('🔄 Backfill sofia.jobs...');

  // Get records missing country_id
  const result = await pool.query(`
    SELECT id, country, state, city
    FROM sofia.jobs
    WHERE country IS NOT NULL AND country_id IS NULL
    LIMIT 2000
  `);

  console.log(`   Processando ${result.rows.length} registros...`);

  let updated = 0;
  let failed = 0;

  for (const row of result.rows) {
    try {
      const { countryId, stateId, cityId } = await normalizeLocation(pool, {
        country: row.country,
        state: row.state,
        city: row.city,
      });

      if (countryId) {
        await pool.query(
          'UPDATE sofia.jobs SET country_id = $1, state_id = $2, city_id = $3 WHERE id = $4',
          [countryId, stateId, cityId, row.id]
        );
        updated++;
      }
    } catch (error) {
      failed++;
    }
  }

  console.log(`   ✅ Atualizados: ${updated}`);
  console.log(`   ❌ Falhas: ${failed}`);

  return updated;
}

async function backfillFunding() {
  console.log('\n🔄 Backfill sofia.funding_rounds...');

  const result = await pool.query(`
    SELECT id, country, city
    FROM sofia.funding_rounds
    WHERE country IS NOT NULL AND country_id IS NULL
    LIMIT 10000
  `);

  console.log(`   Processando ${result.rows.length} registros...`);

  let updated = 0;
  let failed = 0;

  for (const row of result.rows) {
    try {
      const { countryId, cityId } = await normalizeLocation(pool, {
        country: row.country,
        state: null,
        city: row.city,
      });

      if (countryId) {
        await pool.query(
          'UPDATE sofia.funding_rounds SET country_id = $1, city_id = $2 WHERE id = $3',
          [countryId, cityId, row.id]
        );
        updated++;
      }
    } catch (error) {
      failed++;
    }
  }

  console.log(`   ✅ Atualizados: ${updated}`);
  console.log(`   ❌ Falhas: ${failed}`);

  return updated;
}

async function showStats() {
  console.log('\n' + '='.repeat(60));
  console.log('ESTATÍSTICAS FINAIS');
  console.log('='.repeat(60));

  const jobs = await pool.query(`
    SELECT
      COUNT(*) as total,
      COUNT(country_id) as with_country_id
    FROM sofia.jobs
  `);

  const funding = await pool.query(`
    SELECT
      COUNT(*) as total,
      COUNT(country_id) as with_country_id
    FROM sofia.funding_rounds
  `);

  const j = jobs.rows[0];
  const f = funding.rows[0];

  console.log(`\n📊 sofia.jobs:`);
  console.log(`   ${j.with_country_id}/${j.total} (${(j.with_country_id / j.total * 100).toFixed(1)}%)`);

  console.log(`\n📊 sofia.funding_rounds:`);
  console.log(`   ${f.with_country_id}/${f.total} (${(f.with_country_id / f.total * 100).toFixed(1)}%)`);

  console.log('\n' + '='.repeat(60));
}

async function main() {
  console.log('========================================');
  console.log('BACKFILL COM FALLBACKS INTELIGENTES');
  console.log('========================================\n');

  try {
    await backfillJobs();
    await backfillFunding();
    await showStats();

    console.log('\n✅ Backfill concluído!\n');
  } catch (error: any) {
    console.error('❌ Erro:', error.message);
  } finally {
    await pool.end();
  }
}

main();
