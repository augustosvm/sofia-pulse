#!/usr/bin/env npx tsx
/**
 * CarsXE API Collector
 * API de dados automotivos com VIN decoding, especificações, market value
 * Requer API key (https://carsxe.com/)
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

const CARSXE_API_KEY = process.env.CARSXE_API_KEY;
const CARSXE_BASE_URL = 'https://api.carsxe.com';

interface CarsXEVehicle {
    year: number;
    make: string;
    model: string;
    trim?: string;
    body?: string;
    engine?: string;
    transmission?: string;
    drivetrain?: string;
    fuel_type?: string;
    mpg_city?: number;
    mpg_highway?: number;
    msrp?: number;
}

async function collectCarsXEData() {
    console.log('🚗 CarsXE API Collector');
    console.log('='.repeat(60));

    if (!CARSXE_API_KEY) {
        console.error('❌ CARSXE_API_KEY é obrigatória!');
        console.log('\n📝 Obtenha sua API key em: https://carsxe.com/');
        process.exit(1);
    }

    const client = new Client(dbConfig);
    await client.connect();

    try {
        // Criar tabela se não existir
        await client.query(`
            CREATE TABLE IF NOT EXISTS sofia.carsxe_vehicles (
                id SERIAL PRIMARY KEY,
                year INTEGER,
                make VARCHAR(100),
                model VARCHAR(100),
                trim VARCHAR(100),
                body VARCHAR(100),
                engine VARCHAR(200),
                transmission VARCHAR(100),
                drivetrain VARCHAR(50),
                fuel_type VARCHAR(50),
                mpg_city INTEGER,
                mpg_highway INTEGER,
                msrp NUMERIC,
                collected_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(year, make, model, trim)
            );
        `);

        let totalCollected = 0;
        const currentYear = new Date().getFullYear();
        const years = [currentYear, currentYear - 1, currentYear - 2];

        // Marcas populares para coletar
        const popularMakes = [
            'Toyota', 'Honda', 'Ford', 'Chevrolet', 'Nissan',
            'Volkswagen', 'Hyundai', 'Kia', 'Mazda', 'Subaru',
            'BMW', 'Mercedes-Benz', 'Audi', 'Lexus', 'Tesla'
        ];

        for (const make of popularMakes) {
            console.log(`\n🏭 ${make}`);

            for (const year of years) {
                try {
                    // Buscar modelos para cada marca e ano
                    const response = await axios.get(`${CARSXE_BASE_URL}/specs`, {
                        params: {
                            key: CARSXE_API_KEY,
                            year: year,
                            make: make
                        },
                        timeout: 15000
                    });

                    const vehicles: CarsXEVehicle[] = response.data || [];

                    if (vehicles.length === 0) {
                        console.log(`   ${year}: Nenhum modelo encontrado`);
                        continue;
                    }

                    console.log(`   ${year}: ${vehicles.length} veículos`);

                    for (const vehicle of vehicles) {
                        try {
                            await client.query(`
                                INSERT INTO sofia.carsxe_vehicles (
                                    year, make, model, trim, body, engine,
                                    transmission, drivetrain, fuel_type,
                                    mpg_city, mpg_highway, msrp
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                                ON CONFLICT (year, make, model, trim) DO UPDATE SET
                                    collected_at = NOW(),
                                    msrp = COALESCE(EXCLUDED.msrp, sofia.carsxe_vehicles.msrp)
                            `, [
                                vehicle.year,
                                vehicle.make,
                                vehicle.model,
                                vehicle.trim || null,
                                vehicle.body || null,
                                vehicle.engine || null,
                                vehicle.transmission || null,
                                vehicle.drivetrain || null,
                                vehicle.fuel_type || null,
                                vehicle.mpg_city || null,
                                vehicle.mpg_highway || null,
                                vehicle.msrp || null
                            ]);

                            totalCollected++;

                        } catch (err: any) {
                            console.error(`      ❌ Erro ao inserir ${vehicle.model}:`, err.message);
                        }
                    }

                    // Rate limiting (respeitar limites da API)
                    await new Promise(resolve => setTimeout(resolve, 2000));

                } catch (err: any) {
                    if (axios.isAxiosError(err)) {
                        console.error(`   ❌ Erro API ${year}: ${err.response?.status} ${err.message}`);
                    } else {
                        console.error(`   ❌ Erro ${year}:`, err.message);
                    }
                }
            }
        }

        // Estatísticas
        const stats = await client.query(`
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT make) as makes,
                COUNT(DISTINCT model) as models,
                COUNT(CASE WHEN msrp IS NOT NULL THEN 1 END) as with_msrp,
                ROUND(AVG(msrp)) as avg_msrp
            FROM sofia.carsxe_vehicles
        `);

        console.log('\n' + '='.repeat(60));
        console.log(`✅ Coletados: ${totalCollected} veículos do CarsXE`);
        console.log('\n📊 Estatísticas CarsXE:');
        console.log(`   Total de veículos: ${stats.rows[0].total}`);
        console.log(`   Fabricantes: ${stats.rows[0].makes}`);
        console.log(`   Modelos: ${stats.rows[0].models}`);
        console.log(`   Com MSRP: ${stats.rows[0].with_msrp}`);
        if (stats.rows[0].avg_msrp) {
            console.log(`   MSRP médio: $${stats.rows[0].avg_msrp.toLocaleString()}`);
        }
        console.log('='.repeat(60));

    } catch (error: any) {
        console.error('❌ Erro fatal:', error.message);
    } finally {
        await client.end();
    }
}

if (require.main === module) {
    collectCarsXEData()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Erro fatal:', err);
            process.exit(1);
        });
}

export { collectCarsXEData };
