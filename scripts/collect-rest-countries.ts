#!/usr/bin/env npx tsx
/**
 * REST Countries API - Normalização de Países
 * API gratuita para normalizar nomes de países
 * Resolve problemas de comparação entre diferentes fontes
 */

import axios from 'axios';
import { Client } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

const REST_COUNTRIES_URL = 'https://restcountries.com/v3.1/all';

interface Country {
    name: {
        common: string;
        official: string;
        nativeName?: any;
    };
    cca2: string; // ISO 3166-1 alpha-2
    cca3: string; // ISO 3166-1 alpha-3
    ccn3?: string; // ISO 3166-1 numeric
    altSpellings?: string[];
    region: string;
    subregion?: string;
    languages?: { [key: string]: string };
    translations?: { [key: string]: { official: string; common: string } };
    capital?: string[];
    population: number;
    area?: number;
}

async function collectCountriesData() {
    console.log('🌍 REST Countries - Normalização de Países');
    console.log('='.repeat(60));

    const client = new Client(dbConfig);
    await client.connect();

    try {
        // Criar tabela de normalização
        await client.query(`
            CREATE TABLE IF NOT EXISTS sofia.countries_normalization (
                id SERIAL PRIMARY KEY,
                common_name VARCHAR(200) UNIQUE,
                official_name VARCHAR(300),
                iso_alpha2 CHAR(2) UNIQUE,
                iso_alpha3 CHAR(3) UNIQUE,
                iso_numeric CHAR(3),
                region VARCHAR(100),
                subregion VARCHAR(100),
                capital VARCHAR(200),
                population BIGINT,
                area NUMERIC,
                alt_spellings TEXT[],
                translations JSONB,
                collected_at TIMESTAMPTZ DEFAULT NOW()
            );
        `);

        console.log('\n📥 Buscando dados de países...');
        const response = await axios.get<Country[]>(REST_COUNTRIES_URL, {
            timeout: 30000
        });

        const countries = response.data;
        console.log(`   Encontrados: ${countries.length} países`);

        let inserted = 0;
        let updated = 0;

        for (const country of countries) {
            try {
                const result = await client.query(`
                    INSERT INTO sofia.countries_normalization (
                        common_name, official_name, iso_alpha2, iso_alpha3, iso_numeric,
                        region, subregion, capital, population, area,
                        alt_spellings, translations
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (common_name) DO UPDATE SET
                        official_name = EXCLUDED.official_name,
                        population = EXCLUDED.population,
                        collected_at = NOW()
                    RETURNING (xmax = 0) AS inserted
                `, [
                    country.name.common,
                    country.name.official,
                    country.cca2,
                    country.cca3,
                    country.ccn3 || null,
                    country.region,
                    country.subregion || null,
                    country.capital?.[0] || null,
                    country.population,
                    country.area || null,
                    country.altSpellings || [],
                    JSON.stringify(country.translations || {})
                ]);

                if (result.rows[0].inserted) {
                    inserted++;
                } else {
                    updated++;
                }

            } catch (err: any) {
                console.error(`   ❌ Erro ao inserir ${country.name.common}:`, err.message);
            }
        }

        // Criar índices para busca rápida
        await client.query(`
            CREATE INDEX IF NOT EXISTS idx_countries_common_name 
            ON sofia.countries_normalization(common_name);
            
            CREATE INDEX IF NOT EXISTS idx_countries_iso_alpha2 
            ON sofia.countries_normalization(iso_alpha2);
            
            CREATE INDEX IF NOT EXISTS idx_countries_iso_alpha3 
            ON sofia.countries_normalization(iso_alpha3);
            
            CREATE INDEX IF NOT EXISTS idx_countries_region 
            ON sofia.countries_normalization(region);
        `);

        // Estatísticas
        const stats = await client.query(`
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT region) as regions,
                COUNT(DISTINCT subregion) as subregions,
                SUM(population) as total_population,
                SUM(area) as total_area
            FROM sofia.countries_normalization
        `);

        console.log('\n' + '='.repeat(60));
        console.log(`✅ Inseridos: ${inserted} países`);
        console.log(`🔄 Atualizados: ${updated} países`);
        console.log('\n📊 Estatísticas:');
        console.log(`   Total de países: ${stats.rows[0].total}`);
        console.log(`   Regiões: ${stats.rows[0].regions}`);
        console.log(`   Sub-regiões: ${stats.rows[0].subregions}`);
        console.log(`   População total: ${(stats.rows[0].total_population / 1000000000).toFixed(2)}B`);
        console.log(`   Área total: ${(stats.rows[0].total_area / 1000000).toFixed(2)}M km²`);
        console.log('='.repeat(60));

        // Criar função helper para normalização
        await client.query(`
            CREATE OR REPLACE FUNCTION normalize_country_name(input_name TEXT)
            RETURNS TEXT AS $$
            DECLARE
                normalized_name TEXT;
            BEGIN
                -- Tentar match exato
                SELECT common_name INTO normalized_name
                FROM sofia.countries_normalization
                WHERE common_name ILIKE input_name
                   OR official_name ILIKE input_name
                   OR iso_alpha2 = UPPER(input_name)
                   OR iso_alpha3 = UPPER(input_name)
                   OR input_name = ANY(alt_spellings)
                LIMIT 1;
                
                -- Se não encontrou, tentar match parcial
                IF normalized_name IS NULL THEN
                    SELECT common_name INTO normalized_name
                    FROM sofia.countries_normalization
                    WHERE common_name ILIKE '%' || input_name || '%'
                       OR official_name ILIKE '%' || input_name || '%'
                    LIMIT 1;
                END IF;
                
                RETURN COALESCE(normalized_name, input_name);
            END;
            $$ LANGUAGE plpgsql IMMUTABLE;
        `);

        console.log('\n✅ Função normalize_country_name() criada!');
        console.log('   Uso: SELECT normalize_country_name(\'USA\') → \'United States\'');

    } catch (error: any) {
        console.error('❌ Erro fatal:', error.message);
    } finally {
        await client.end();
    }
}

if (require.main === module) {
    collectCountriesData()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Erro fatal:', err);
            process.exit(1);
        });
}

export { collectCountriesData };
