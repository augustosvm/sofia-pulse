#!/usr/bin/env npx tsx
/**
 * Google Maps Places API - Geolocalização
 * Onde as coisas realmente acontecem
 * Enriquece dados com coordenadas, endereços e POIs
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

const GOOGLE_MAPS_API_KEY = process.env.GOOGLE_MAPS_API_KEY;
const GEOCODING_URL = 'https://maps.googleapis.com/maps/api/geocode/json';
const PLACES_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json';

interface GeocodeResult {
    formatted_address: string;
    geometry: {
        location: {
            lat: number;
            lng: number;
        };
    };
    place_id: string;
    types: string[];
}

async function enrichLocationsWithGoogleMaps() {
    console.log('🗺️  Google Maps - Enriquecimento de Geolocalização');
    console.log('='.repeat(60));

    if (!GOOGLE_MAPS_API_KEY) {
        console.error('❌ GOOGLE_MAPS_API_KEY é obrigatória!');
        console.log('\n📝 Obtenha sua API key em: https://console.cloud.google.com/');
        process.exit(1);
    }

    const client = new Client(dbConfig);
    await client.connect();

    try {
        // Criar tabela de geolocalização
        await client.query(`
            CREATE TABLE IF NOT EXISTS sofia.locations_geocoded (
                id SERIAL PRIMARY KEY,
                location_name VARCHAR(500) UNIQUE,
                formatted_address TEXT,
                latitude NUMERIC(10, 7),
                longitude NUMERIC(10, 7),
                place_id VARCHAR(200),
                place_types TEXT[],
                country VARCHAR(100),
                city VARCHAR(200),
                state VARCHAR(100),
                collected_at TIMESTAMPTZ DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_locations_name 
            ON sofia.locations_geocoded(location_name);
            
            CREATE INDEX IF NOT EXISTS idx_locations_coords 
            ON sofia.locations_geocoded(latitude, longitude);
        `);

        // Buscar localizações únicas de todas as tabelas
        console.log('\n📍 Buscando localizações para geocodificar...');

        const locationsQuery = `
            SELECT DISTINCT location FROM (
                SELECT DISTINCT location FROM sofia.jobs WHERE location IS NOT NULL
                UNION
                SELECT DISTINCT city FROM sofia.jobs WHERE city IS NOT NULL
                UNION
                SELECT DISTINCT country FROM sofia.jobs WHERE country IS NOT NULL
            ) AS all_locations
            WHERE location NOT IN (SELECT location_name FROM sofia.locations_geocoded)
            LIMIT 100
        `;

        const locations = await client.query(locationsQuery);
        console.log(`   Encontradas: ${locations.rows.length} localizações para processar`);

        let geocoded = 0;
        let failed = 0;

        for (const row of locations.rows) {
            const location = row.location;

            try {
                console.log(`\n📌 ${location}`);

                const response = await axios.get(GEOCODING_URL, {
                    params: {
                        address: location,
                        key: GOOGLE_MAPS_API_KEY
                    },
                    timeout: 10000
                });

                if (response.data.status === 'OK' && response.data.results.length > 0) {
                    const result: GeocodeResult = response.data.results[0];

                    // Extrair país, cidade, estado
                    const addressComponents = response.data.results[0].address_components || [];
                    let country = null;
                    let city = null;
                    let state = null;

                    for (const component of addressComponents) {
                        if (component.types.includes('country')) {
                            country = component.long_name;
                        }
                        if (component.types.includes('locality')) {
                            city = component.long_name;
                        }
                        if (component.types.includes('administrative_area_level_1')) {
                            state = component.long_name;
                        }
                    }

                    await client.query(`
                        INSERT INTO sofia.locations_geocoded (
                            location_name, formatted_address, latitude, longitude,
                            place_id, place_types, country, city, state
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (location_name) DO UPDATE SET
                            formatted_address = EXCLUDED.formatted_address,
                            latitude = EXCLUDED.latitude,
                            longitude = EXCLUDED.longitude,
                            collected_at = NOW()
                    `, [
                        location,
                        result.formatted_address,
                        result.geometry.location.lat,
                        result.geometry.location.lng,
                        result.place_id,
                        result.types,
                        country,
                        city,
                        state
                    ]);

                    console.log(`   ✅ ${result.formatted_address}`);
                    console.log(`   📍 ${result.geometry.location.lat}, ${result.geometry.location.lng}`);
                    geocoded++;

                } else {
                    console.log(`   ⚠️  Não encontrado: ${response.data.status}`);
                    failed++;
                }

                // Rate limiting (respeitar quota da API)
                await new Promise(resolve => setTimeout(resolve, 200));

            } catch (err: any) {
                console.error(`   ❌ Erro:`, err.message);
                failed++;
            }
        }

        // Estatísticas
        const stats = await client.query(`
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT country) as countries,
                COUNT(DISTINCT city) as cities
            FROM sofia.locations_geocoded
        `);

        console.log('\n' + '='.repeat(60));
        console.log(`✅ Geocodificadas: ${geocoded} localizações`);
        console.log(`❌ Falhas: ${failed}`);
        console.log('\n📊 Estatísticas:');
        console.log(`   Total geocodificado: ${stats.rows[0].total}`);
        console.log(`   Países: ${stats.rows[0].countries}`);
        console.log(`   Cidades: ${stats.rows[0].cities}`);
        console.log('='.repeat(60));

    } catch (error: any) {
        console.error('❌ Erro fatal:', error.message);
    } finally {
        await client.end();
    }
}

if (require.main === module) {
    enrichLocationsWithGoogleMaps()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Erro fatal:', err);
            process.exit(1);
        });
}

export { enrichLocationsWithGoogleMaps };
