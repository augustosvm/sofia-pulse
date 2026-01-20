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
import { normalizeLocation } from './shared/geo-helpers.js';
import { getOrCreateOrganization } from './shared/org-helpers.js';

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
            for (const keyword of TECH_KEYWORDS) {
                console.log(`\n🔍 Searching for "${keyword}"...`);

                let page = 1;
                let hasMore = true;
                let consecutiveErrors = 0;

                while (hasMore && page <= 50) { // Safety cap of 50 pages (1000 jobs per keyword)
                    try {
                        const url = `https://api.adzuna.com/v1/api/jobs/${country.code}/search/${page}`;
                        const response = await axios.get<AdzunaResponse>(url, {
                            params: {
                                app_id: ADZUNA_APP_ID,
                                app_key: ADZUNA_API_KEY,
                                what: keyword,
                                results_per_page: 50, // Max allowed by Adzuna
                            },
                            timeout: 15000
                        });

                        const jobs = response.data.results || [];

                        if (jobs.length === 0) {
                            hasMore = false;
                            break;
                        }

                        console.log(`   Page ${page}: ${jobs.length} jobs`);

                        for (const job of jobs) {
                            try {
                                // Extract location details
                                // Adzuna API format varies by country:
                                // USA: ["US", "State", "County", "City"] (4 elements)
                                // UK: ["UK", "City"] (2 elements)
                                // France: ["France", "Region", "Dept", "Arr", "City"] (4-5 elements)
                                // Brazil: ["Brasil"] (1 element - country only)
                                const location = job.location.display_name;
                                const areaLength = job.location.area.length;

                                let city = null;
                                let state = null;

                                if (areaLength === 1) {
                                    // Only country (e.g., Brazil: ["Brasil"])
                                    city = null;
                                    state = null;
                                } else if (areaLength === 2) {
                                    // Country + City (e.g., UK: ["UK", "London"])
                                    city = job.location.area[1];
                                    state = null;
                                } else if (areaLength >= 3) {
                                    // Multiple levels - last is city, second might be state
                                    city = job.location.area[areaLength - 1]; // Last element
                                    state = job.location.area[1]; // Second element (state/region)
                                }

                                const countryName = country.name; // Use mapped country name

                                // Normalize geographic data
                                const { countryId, stateId, cityId } = await normalizeLocation(pool, {
                                    country: countryName,
                                    state: state,
                                    city: city
                                });

                                // Get or create organization
                                const organizationId = await getOrCreateOrganization(
                                    pool,
                                    job.company.display_name,
                                    null,
                                    location,
                                    countryName,
                                    'adzuna'
                                );

                                await pool.query(`
                                INSERT INTO sofia.jobs (
                                    job_id, platform, source, title, company,
                                    raw_location, raw_city, raw_state, country, country_id, state_id, city_id, remote_type,
                                    url, search_keyword, organization_id, collected_at
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, NOW())
                                ON CONFLICT (job_id) DO UPDATE SET
                                    collected_at = NOW(),
                                    source = EXCLUDED.source,
                                    organization_id = COALESCE(EXCLUDED.organization_id, sofia.jobs.organization_id),
                                    country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
                                    state_id = COALESCE(EXCLUDED.state_id, sofia.jobs.state_id),
                                    city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id)
                            `, [
                                    `adzuna-${job.id}`, // job_id
                                    'adzuna', // platform
                                    'adzuna', // source
                                    job.title, // title
                                    job.company.display_name, // company
                                    location, // raw_location
                                    city, // raw_city
                                    state, // raw_state
                                    countryName, // country
                                    countryId, // country_id
                                    stateId, // state_id
                                    cityId, // city_id
                                    'remote', // remote_type (placeholder, Adzuna doesn't explicitly provide this)
                                    job.redirect_url, // url
                                    keyword, // search_keyword
                                    organizationId // organization_id
                                ]);

                                totalCollected++;

                            } catch (err: any) {
                                if (err.code !== '23505') {
                                    console.error(`   ❌ Error inserting job ${job.id}:`, err.message);
                                }
                            }
                        }

                        // Rate limiting: aguardar 1s entre requests
                        await new Promise(resolve => setTimeout(resolve, 1500));
                        page++;
                        consecutiveErrors = 0;

                    } catch (error: any) {
                        consecutiveErrors++;
                        if (axios.isAxiosError(error) && error.response?.status === 400) {
                            // End of results or invalid page
                            hasMore = false;
                        } else if (consecutiveErrors >= 3) {
                            console.error(`   ❌ Too many errors for "${keyword}", skipping...`);
                            hasMore = false;
                        } else {
                            if (axios.isAxiosError(error)) {
                                console.error(`   ❌ API Error for "${keyword}" p${page}: ${error.response?.status} ${error.message}`);
                            } else {
                                console.error(`   ❌ Error for "${keyword}" p${page}:`, error.message);
                            }
                            await new Promise(resolve => setTimeout(resolve, 5000)); // Backoff
                        }
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
