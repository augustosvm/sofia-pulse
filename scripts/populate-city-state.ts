#!/usr/bin/env tsx
/**
 * Script para popular os campos city e state de todas as vagas
 * baseado no campo location
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

function parseLocation(location: string): { city: string | null, state: string | null } {
    if (!location) return { city: null, state: null };

    // Padrões comuns:
    // "São Paulo - SP"
    // "São Paulo, SP"
    // "Remote"
    // "Brazil"
    // "United States"

    // Padrão: Cidade - UF (Brasil)
    const brPattern = /^(.+?)\s*[-,]\s*([A-Z]{2})$/;
    const match = location.match(brPattern);

    if (match) {
        return {
            city: match[1].trim(),
            state: match[2].trim()
        };
    }

    // Padrão: Cidade, Estado (USA/outros)
    const usPattern = /^(.+?),\s*(.+)$/;
    const usMatch = location.match(usPattern);

    if (usMatch) {
        return {
            city: usMatch[1].trim(),
            state: usMatch[2].trim()
        };
    }

    // Se não conseguiu parsear, deixa como está
    return { city: null, state: null };
}

async function populateCityState() {
    const client = new Client(DB_CONFIG);
    await client.connect();

    console.log('🔄 Populando city e state para todas as vagas...');
    console.log('='.repeat(60));

    try {
        // Aumentar limite dos campos
        await client.query(`
      ALTER TABLE sofia.jobs 
      ALTER COLUMN city TYPE VARCHAR(200),
      ALTER COLUMN state TYPE VARCHAR(100)
    `);

        console.log('✅ Colunas ajustadas');

        // Buscar todas as vagas que não têm city/state
        const jobs = await client.query(`
      SELECT id, location 
      FROM sofia.jobs 
      WHERE (city IS NULL OR state IS NULL) AND location IS NOT NULL
      LIMIT 5000
    `);

        console.log(`📋 Processando ${jobs.rows.length} vagas...`);

        let updated = 0;
        let skipped = 0;

        for (const job of jobs.rows) {
            const { city, state } = parseLocation(job.location);

            if (city || state) {
                // Truncar se necessário
                const truncatedCity = city ? city.substring(0, 200) : null;
                const truncatedState = state ? state.substring(0, 100) : null;

                await client.query(
                    `UPDATE sofia.jobs SET city = $1, state = $2 WHERE id = $3`,
                    [truncatedCity, truncatedState, job.id]
                );
                updated++;

                if (updated % 100 === 0) {
                    console.log(`  ✅ Processadas ${updated} vagas...`);
                }
            } else {
                skipped++;
            }
        }

        console.log('='.repeat(60));
        console.log(`✅ Atualizadas: ${updated} vagas`);
        console.log(`⚠️  Ignoradas: ${skipped} vagas (sem padrão reconhecível)`);

        // Estatísticas finais
        const stats = await client.query(`
      SELECT 
        COUNT(*) as total,
        COUNT(city) as com_city,
        COUNT(state) as com_state,
        COUNT(CASE WHEN city IS NOT NULL AND state IS NOT NULL THEN 1 END) as completas
      FROM sofia.jobs
    `);

        const s = stats.rows[0];
        console.log('\n📊 Estatísticas finais:');
        console.log(`  Total de vagas: ${s.total}`);
        console.log(`  Com city: ${s.com_city} (${Math.round(s.com_city / s.total * 100)}%)`);
        console.log(`  Com state: ${s.com_state} (${Math.round(s.com_state / s.total * 100)}%)`);
        console.log(`  Completas (city + state): ${s.completas} (${Math.round(s.completas / s.total * 100)}%)`);
        console.log('='.repeat(60));

    } catch (err) {
        console.error('❌ Erro:', err);
    } finally {
        await client.end();
    }
}

populateCityState();
