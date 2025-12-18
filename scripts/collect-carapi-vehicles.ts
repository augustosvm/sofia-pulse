#!/usr/bin/env npx tsx
/**
 * CarAPI Collector
 * API com 90k+ veículos de 1990 até hoje
 * Requer API key (https://carapi.app/)
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

const CARAPI_JWT = process.env.CARAPI_JWT;
const CARAPI_BASE_URL = 'https://carapi.app/api';

interface CarAPIVehicle {
    id: number;
    year: number;
    make: string;
    model: string;
    trim?: string;
    body?: string;
    engine?: {
        type?: string;
        cylinders?: number;
        displacement?: number;
        horsepower?: number;
        torque?: number;
        fuel_type?: string;
    };
    transmission?: string;
    drivetrain?: string;
    mpg?: {
        city?: number;
        highway?: number;
        combined?: number;
    };
    msrp?: number;
}

async function collectCarAPIData() {
    console.log('🚗 CarAPI Collector');
    console.log('='.repeat(60));

    if (!CARAPI_JWT) {
        console.error('❌ CARAPI_JWT é obrigatório!');
        console.log('\n📝 Obtenha seu JWT em: https://carapi.app/');
        console.log('   1. Crie uma conta');
        console.log('   2. Gere um API Secret');
        console.log('   3. Use o secret para obter um JWT');
        process.exit(1);
    }

    const client = new Client(dbConfig);
    await client.connect();

    try {
        // Criar tabela se não existir
        await client.query(`
            CREATE TABLE IF NOT EXISTS sofia.carapi_vehicles (
                id SERIAL PRIMARY KEY,
                carapi_id INTEGER UNIQUE,
                year INTEGER,
                make VARCHAR(100),
                model VARCHAR(100),
                trim VARCHAR(100),
                body VARCHAR(100),
                engine_type VARCHAR(100),
                engine_cylinders INTEGER,
                engine_displacement NUMERIC,
                engine_horsepower INTEGER,
                engine_torque INTEGER,
                fuel_type VARCHAR(50),
                transmission VARCHAR(100),
                drivetrain VARCHAR(50),
                mpg_city INTEGER,
                mpg_highway INTEGER,
                mpg_combined INTEGER,
                msrp NUMERIC,
                collected_at TIMESTAMPTZ DEFAULT NOW()
            );
        `);

        let totalCollected = 0;
        const currentYear = new Date().getFullYear();
        const years = [currentYear, currentYear - 1, currentYear - 2, currentYear - 3];

        for (const year of years) {
            console.log(`\n📅 Ano ${year}`);

            try {
                // Buscar veículos por ano
                const response = await axios.get(`${CARAPI_BASE_URL}/trims`, {
                    params: {
                        year: year,
                        limit: 100 // Limitar para não estourar quota
                    },
                    headers: {
                        'Authorization': `Bearer ${CARAPI_JWT}`
                    },
                    timeout: 15000
                });

                const vehicles: CarAPIVehicle[] = response.data.data || [];

                if (vehicles.length === 0) {
                    console.log(`   Nenhum veículo encontrado`);
                    continue;
                }

                console.log(`   Encontrados: ${vehicles.length} veículos`);

                for (const vehicle of vehicles) {
                    try {
                        await client.query(`
                            INSERT INTO sofia.carapi_vehicles (
                                carapi_id, year, make, model, trim, body,
                                engine_type, engine_cylinders, engine_displacement,
                                engine_horsepower, engine_torque, fuel_type,
                                transmission, drivetrain,
                                mpg_city, mpg_highway, mpg_combined, msrp
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                            ON CONFLICT (carapi_id) DO UPDATE SET
                                collected_at = NOW(),
                                msrp = COALESCE(EXCLUDED.msrp, sofia.carapi_vehicles.msrp)
                        `, [
                            vehicle.id,
                            vehicle.year,
                            vehicle.make,
                            vehicle.model,
                            vehicle.trim || null,
                            vehicle.body || null,
                            vehicle.engine?.type || null,
                            vehicle.engine?.cylinders || null,
                            vehicle.engine?.displacement || null,
                            vehicle.engine?.horsepower || null,
                            vehicle.engine?.torque || null,
                            vehicle.engine?.fuel_type || null,
                            vehicle.transmission || null,
                            vehicle.drivetrain || null,
                            vehicle.mpg?.city || null,
                            vehicle.mpg?.highway || null,
                            vehicle.mpg?.combined || null,
                            vehicle.msrp || null
                        ]);

                        totalCollected++;

                    } catch (err: any) {
                        console.error(`      ❌ Erro ao inserir ${vehicle.make} ${vehicle.model}:`, err.message);
                    }
                }

                // Rate limiting (respeitar quota da API)
                await new Promise(resolve => setTimeout(resolve, 2000));

            } catch (err: any) {
                if (axios.isAxiosError(err)) {
                    console.error(`   ❌ Erro API: ${err.response?.status} ${err.message}`);
                    if (err.response?.status === 429) {
                        console.log('   ⚠️  Rate limit atingido. Aguardando...');
                        await new Promise(resolve => setTimeout(resolve, 60000)); // Aguardar 1 minuto
                    }
                } else {
                    console.error(`   ❌ Erro:`, err.message);
                }
            }
        }

        // Estatísticas
        const stats = await client.query(`
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT make) as makes,
                COUNT(DISTINCT model) as models,
                COUNT(DISTINCT year) as years,
                COUNT(CASE WHEN msrp IS NOT NULL THEN 1 END) as with_msrp,
                ROUND(AVG(msrp)) as avg_msrp,
                ROUND(AVG(engine_horsepower)) as avg_hp,
                ROUND(AVG(mpg_combined)) as avg_mpg
            FROM sofia.carapi_vehicles
        `);

        console.log('\n' + '='.repeat(60));
        console.log(`✅ Coletados: ${totalCollected} veículos do CarAPI`);
        console.log('\n📊 Estatísticas CarAPI:');
        console.log(`   Total de veículos: ${stats.rows[0].total}`);
        console.log(`   Fabricantes: ${stats.rows[0].makes}`);
        console.log(`   Modelos: ${stats.rows[0].models}`);
        console.log(`   Anos: ${stats.rows[0].years}`);
        console.log(`   Com MSRP: ${stats.rows[0].with_msrp}`);
        if (stats.rows[0].avg_msrp) {
            console.log(`   MSRP médio: $${stats.rows[0].avg_msrp.toLocaleString()}`);
        }
        if (stats.rows[0].avg_hp) {
            console.log(`   HP médio: ${stats.rows[0].avg_hp}`);
        }
        if (stats.rows[0].avg_mpg) {
            console.log(`   MPG médio: ${stats.rows[0].avg_mpg}`);
        }
        console.log('='.repeat(60));

    } catch (error: any) {
        console.error('❌ Erro fatal:', error.message);
    } finally {
        await client.end();
    }
}

if (require.main === module) {
    collectCarAPIData()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Erro fatal:', err);
            process.exit(1);
        });
}

export { collectCarAPIData };
