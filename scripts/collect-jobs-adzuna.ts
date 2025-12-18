#!/usr/bin/env npx tsx
/**
 * Adzuna Jobs API Collector
 * 50k+ vagas/dia, 20+ países, API gratuita (5000 calls/mês)
 * Dados de salário incluídos
 */

import axios from 'axios';
import { Pool } from 'pg';
import dotenv from 'dotenv';
import { getKeywordsByLanguage } from './shared/keywords-config';
import { normalizeLocation } from './shared/geo-helpers';

dotenv.config();

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

const ADZUNA_APP_ID = process.env.ADZUNA_APP_ID;
const ADZUNA_API_KEY = process.env.ADZUNA_API_KEY;

// Países suportados pela Adzuna
const COUNTRIES = [
    { code: 'us', name: 'United States' },
    { code: 'gb', name: 'United Kingdom' },
    { code: 'br', name: 'Brazil' },
    { code: 'ca', name: 'Canada' },
    { code: 'au', name: 'Australia' },
    { code: 'de', name: 'Germany' },
    { code: 'fr', name: 'France' },
    { code: 'nl', name: 'Netherlands' },
    { code: 'in', name: 'India' },
    { code: 'sg', name: 'Singapore' },
];

// Usar keywords centralizadas em inglês
const TECH_KEYWORDS = getKeywordsByLanguage('en');

interface AdzunaJob {
    id: string;
    title: string;
    company: {
        display_name: string;
    };
    location: {
        display_name: string;
        area: string[];
    };
    description: string;
    created: string;
    redirect_url: string;
    salary_min?: number;
    salary_max?: number;
    salary_is_predicted?: string;
    contract_type?: string;
    category: {
        label: string;
    };
}

interface AdzunaResponse {
    results: AdzunaJob[];
    count: number;
}

async function collectAdzunaJobs() {
    console.log('💼 Adzuna Jobs API Collector');
    console.log('='.repeat(60));

    if (!ADZUNA_APP_ID || !ADZUNA_API_KEY) {
        console.error('❌ ADZUNA_APP_ID and ADZUNA_API_KEY are required!');
        console.log('\n📝 Get your free API key at: https://developer.adzuna.com/');
        process.exit(1);
    }

    const pool = new Pool(dbConfig);

    let totalCollected = 0;

    try {
        // Coletar de múltiplos países
        for (const country of COUNTRIES) {
            console.log(`\n🌍 Collecting from ${country.name}...`);

            // Coletar para cada keyword (para maximizar cobertura)
            for (const keyword of TECH_KEYWORDS.slice(0, 3)) { // Limitar a 3 keywords por país para não estourar rate limit
                try {
                    const url = `https://api.adzuna.com/v1/api/jobs/${country.code}/search/1`;
                    const response = await axios.get<AdzunaResponse>(url, {
                        params: {
                            app_id: ADZUNA_APP_ID,
                            app_key: ADZUNA_API_KEY,
                            what: keyword,
                            results_per_page: 20, // Limitar para não estourar rate limit
                        },
                        timeout: 15000
                    });

                    const jobs = response.data.results || [];
                    console.log(`   ${keyword}: ${jobs.length} jobs`);

                    for (const job of jobs) {
                        try {
                            // Extract location details
                            const location = job.location.display_name;
                            const city = job.location.area[0] || null;
                            const countryName = job.location.area[job.location.area.length - 1] || country.name;

                            // Normalize geographic data
                            const { countryId, stateId, cityId } = await normalizeLocation(pool, {
                                country: countryName,
                                city: city
                            });

                            await pool.query(`
                INSERT INTO sofia.jobs (
                  job_id, platform, title, company,
                  location, city, country,
                  country_id, city_id,
                  description, posted_date, url,
                  salary_min, salary_max, salary_currency, salary_period,
                  employment_type, search_keyword, collected_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, NOW())
                ON CONFLICT (job_id, platform) DO UPDATE SET
                  collected_at = NOW(),
                  description = EXCLUDED.description,
                  salary_min = COALESCE(EXCLUDED.salary_min, sofia.jobs.salary_min),
                  salary_max = COALESCE(EXCLUDED.salary_max, sofia.jobs.salary_max)
              `, [
                                job.id,
                                'adzuna',
                                job.title,
                                job.company.display_name,
                                location,
                                city,
                                countryName,
                                countryId,
                                cityId,
                                job.description,
                                new Date(job.created),
                                job.redirect_url,
                                job.salary_min || null,
                                job.salary_max || null,
                                'USD', // Adzuna normaliza para USD
                                'yearly',
                                job.contract_type?.toLowerCase() || 'full-time',
                                keyword
                            ]);

                            totalCollected++;

                        } catch (err: any) {
                            console.error(`   ❌ Error inserting job ${job.id}:`, err.message);
                        }
                    }

                    // Rate limiting: aguardar 1s entre requests
                    await new Promise(resolve => setTimeout(resolve, 1000));

                } catch (error: any) {
                    if (axios.isAxiosError(error)) {
                        console.error(`   ❌ API Error for "${keyword}": ${error.response?.status} ${error.message}`);
                    } else {
                        console.error(`   ❌ Error for "${keyword}":`, error.message);
                    }
                }
            }
        }

    } catch (error: any) {
        console.error(`❌ Fatal error:`, error.message);
    }

    // Statistics
    const stats = await pool.query(`
    SELECT 
      COUNT(*) as total,
      COUNT(DISTINCT company) as companies,
      COUNT(DISTINCT country) as countries,
      COUNT(CASE WHEN salary_min IS NOT NULL THEN 1 END) as with_salary,
      ROUND(AVG(salary_min)) as avg_min,
      ROUND(AVG(salary_max)) as avg_max
    FROM sofia.jobs
    WHERE platform = 'adzuna'
  `);

    await pool.end();

    console.log('\n' + '='.repeat(60));
    console.log(`✅ Collected: ${totalCollected} tech jobs from Adzuna`);
    console.log('\n📊 Adzuna Statistics:');
    console.log(`   Total jobs: ${stats.rows[0].total}`);
    console.log(`   Companies: ${stats.rows[0].companies}`);
    console.log(`   Countries: ${stats.rows[0].countries}`);
    console.log(`   With salary: ${stats.rows[0].with_salary}`);
    if (stats.rows[0].avg_min) {
        console.log(`   Avg salary: $${stats.rows[0].avg_min.toLocaleString()} - $${stats.rows[0].avg_max.toLocaleString()}`);
    }
    console.log('='.repeat(60));

    return totalCollected;
}

if (require.main === module) {
    collectAdzunaJobs()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Fatal error:', err);
            process.exit(1);
        });
}

export { collectAdzunaJobs };
