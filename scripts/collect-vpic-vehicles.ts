#!/usr/bin/env npx tsx
/**
 * VPIC (NHTSA) Vehicle Data Collector
 * API gratuita do governo dos EUA com dados de veículos
 * Não requer autenticação
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

const VPIC_BASE_URL = 'https://vpic.nhtsa.dot.gov/api/vehicles';

interface VPICMake {
    Make_ID: number;
    Make_Name: string;
}

interface VPICModel {
    Model_ID: number;
    Model_Name: string;
}

interface VPICVehicle {
    Make: string;
    Model: string;
    ModelYear: string;
    VehicleType: string;
    BodyClass: string;
    EngineModel: string;
    EngineCylinders: string;
    DisplacementL: string;
    FuelTypePrimary: string;
    Manufacturer: string;
}

async function collectVPICData() {
    console.log('🚗 VPIC (NHTSA) Vehicle Data Collector');
    console.log('='.repeat(60));

    const client = new Client(dbConfig);
    await client.connect();

    try {
        // Criar tabela se não existir
        await client.query(`
            CREATE TABLE IF NOT EXISTS sofia.vpic_vehicles (
                id SERIAL PRIMARY KEY,
                make VARCHAR(100),
                model VARCHAR(100),
                year INTEGER,
                vehicle_type VARCHAR(100),
                body_class VARCHAR(100),
                engine_model VARCHAR(100),
                engine_cylinders VARCHAR(50),
                displacement_l VARCHAR(50),
                fuel_type VARCHAR(100),
                manufacturer VARCHAR(200),
                collected_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(make, model, year, body_class)
            );
        `);

        let totalCollected = 0;
        const currentYear = new Date().getFullYear();
        const yearsToCollect = [currentYear, currentYear - 1, currentYear - 2]; // Últimos 3 anos

        // Buscar fabricantes (makes)
        console.log('\n📋 Buscando fabricantes...');
        const makesResponse = await axios.get(`${VPIC_BASE_URL}/GetAllMakes?format=json`);
        const makes: VPICMake[] = makesResponse.data.Results.slice(0, 50); // Top 50 fabricantes
        console.log(`   Encontrados: ${makes.length} fabricantes`);

        for (const make of makes) {
            console.log(`\n🏭 ${make.Make_Name}`);

            for (const year of yearsToCollect) {
                try {
                    // Buscar modelos para cada fabricante e ano
                    const modelsResponse = await axios.get(
                        `${VPIC_BASE_URL}/GetModelsForMakeYear/make/${encodeURIComponent(make.Make_Name)}/modelyear/${year}?format=json`,
                        { timeout: 10000 }
                    );

                    const models: VPICModel[] = modelsResponse.data.Results;

                    if (models.length === 0) continue;

                    console.log(`   ${year}: ${models.length} modelos`);

                    for (const model of models.slice(0, 10)) { // Limitar a 10 modelos por ano
                        try {
                            // Buscar especificações detalhadas
                            const specsResponse = await axios.get(
                                `${VPIC_BASE_URL}/GetModelsForMakeYear/make/${encodeURIComponent(make.Make_Name)}/modelyear/${year}/model/${encodeURIComponent(model.Model_Name)}?format=json`,
                                { timeout: 10000 }
                            );

                            const specs = specsResponse.data.Results[0] || {};

                            await client.query(`
                                INSERT INTO sofia.vpic_vehicles (
                                    make, model, year, vehicle_type, body_class,
                                    engine_model, engine_cylinders, displacement_l,
                                    fuel_type, manufacturer
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                                ON CONFLICT (make, model, year, body_class) DO UPDATE SET
                                    collected_at = NOW()
                            `, [
                                make.Make_Name,
                                model.Model_Name,
                                year,
                                specs.VehicleType || null,
                                specs.BodyClass || null,
                                specs.EngineModel || null,
                                specs.EngineCylinders || null,
                                specs.DisplacementL || null,
                                specs.FuelTypePrimary || null,
                                make.Make_Name
                            ]);

                            totalCollected++;

                        } catch (err: any) {
                            console.error(`      ❌ Erro ao coletar ${model.Model_Name}:`, err.message);
                        }

                        // Rate limiting
                        await new Promise(resolve => setTimeout(resolve, 200));
                    }

                } catch (err: any) {
                    console.error(`   ❌ Erro ao buscar modelos ${year}:`, err.message);
                }

                // Rate limiting entre anos
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }

        // Estatísticas
        const stats = await client.query(`
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT make) as makes,
                COUNT(DISTINCT model) as models,
                COUNT(DISTINCT year) as years
            FROM sofia.vpic_vehicles
        `);

        console.log('\n' + '='.repeat(60));
        console.log(`✅ Coletados: ${totalCollected} veículos do VPIC`);
        console.log('\n📊 Estatísticas VPIC:');
        console.log(`   Total de veículos: ${stats.rows[0].total}`);
        console.log(`   Fabricantes: ${stats.rows[0].makes}`);
        console.log(`   Modelos: ${stats.rows[0].models}`);
        console.log(`   Anos: ${stats.rows[0].years}`);
        console.log('='.repeat(60));

    } catch (error: any) {
        console.error('❌ Erro fatal:', error.message);
    } finally {
        await client.end();
    }
}

if (require.main === module) {
    collectVPICData()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Erro fatal:', err);
            process.exit(1);
        });
}

export { collectVPICData };
