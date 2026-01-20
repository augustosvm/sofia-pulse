#!/usr/bin/env npx tsx
/**
 * Findwork Jobs Collector
 * Coleta vagas remote da Findwork (sem API key - scraping leve)
 * URL: https://findwork.dev/
 */

import axios from 'axios';
import { Pool } from 'pg';
import dotenv from 'dotenv';
import { normalizeLocation } from './shared/geo-helpers.js';
import { getOrCreateOrganization } from './shared/org-helpers.js';
import { getKeywordsByLanguage } from './shared/keywords-config.js';

dotenv.config();

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

// Search for remote tech jobs
const SEARCH_QUERIES = [
    'software-engineer',
    'frontend-developer',
    'backend-developer',
    'full-stack',
    'devops',
    'data-scientist',
    'machine-learning',
    'python-developer'
];

interface FindworkJob {
    id: string;
    role: string;
    company_name: string;
    location: string;
    remote: boolean;
    url: string;
    date_posted: string;
    employment_type?: string;
}

async function collectFindworkJobs() {
    console.log('🔍 Findwork Jobs Collector');
    console.log('='.repeat(60));

    const pool = new Pool(dbConfig);

    let totalCollected = 0;

    // Use centralized keywords (English) because findwork is global/English
    const englishKeywords = getKeywordsByLanguage('en');

    for (const query of englishKeywords) {
        try {
            // Format query for URL (spaces to dashes)
            const formattedQuery = query.toLowerCase().replace(/\s+/g, '-');
            console.log(`\n🔍 Query: "${formattedQuery}" (original: "${query}")...`);

            // Findwork URL structure: /[keyword]-jobs
            // Supports simple pagination with ?page=2 usually (Django)
            let page = 1;
            let hasMore = true;
            let consecutiveErrors = 0;

            while (hasMore && page <= 5) { // Cap at 5 pages per keyword (approx 100 jobs)
                try {
                    const url = `https://findwork.dev/${formattedQuery}-jobs/` + (page > 1 ? `?page=${page}` : '');

                    const response = await axios.get(url, {
                        headers: {
                            'User-Agent': 'Mozilla/5.0 (compatible; Sofia-Pulse/1.0)',
                            'Accept': 'text/html'
                        },
                        timeout: 10000
                    });

                    const jobPattern = /href="\/([A-Za-z0-9]+)\/([^"]+)"/g;
                    const jobs: Array<{ id: string; slug: string }> = [];

                    let match;
                    // Collect all matches on the page
                    while ((match = jobPattern.exec(response.data)) !== null) {
                        const [_, id, slug] = match;
                        if (id.length >= 5 && id.length <= 10 && !slug.includes('/')) {
                            jobs.push({ id, slug });
                        }
                    }

                    if (jobs.length === 0) {
                        hasMore = false;
                        break;
                    }

                    console.log(`   Page ${page}: Found ${jobs.length} jobs`);

                    for (const job of jobs) {
                        try {
                            // Extract location from slug (e.g., "senior-developer-at-company")
                            const parts = job.slug.split('-at-');
                            const title = parts[0]?.replace(/-/g, ' ') || 'Tech Position';
                            const company = parts[1]?.replace(/-/g, ' ') || 'Unknown';

                            // Findwork is primarily remote jobs
                            const location = 'Remote';
                            const country = 'United States'; // Fallback
                            const city = null;

                            // Normalize geographic data
                            const { countryId, stateId, cityId } = await normalizeLocation(pool, {
                                country: country,
                                state: null,
                                city: city
                            });

                            // Get or create organization
                            const organizationId = await getOrCreateOrganization(
                                pool,
                                company,
                                null,
                                location,
                                country,
                                'findwork'
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
                                `findwork-${job.id}`,
                                'findwork',
                                'findwork',
                                title,
                                company,
                                location,
                                city,
                                null, // state
                                country,
                                countryId,
                                stateId,
                                cityId,
                                'remote',
                                `https://findwork.dev/${job.id}/${job.slug}`,
                                query,
                                organizationId
                            ]);

                            totalCollected++;

                        } catch (err: any) {
                            if (err.code !== '23505') {
                                console.error(`   ❌ Error inserting  ${job.id}:`, err.message);
                            }
                        }
                    }

                    page++;
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    consecutiveErrors = 0;

                } catch (error: any) {
                    consecutiveErrors++;
                    if (axios.isAxiosError(error) && error.response?.status === 404) {
                        hasMore = false; // Page not found = end of results
                    } else if (consecutiveErrors >= 3) {
                        // console.error(`   ❌ Too many errors for "${query}", skipping...`);
                        hasMore = false;
                    } else {
                        await new Promise(resolve => setTimeout(resolve, 3000));
                    }
                }
            }

        } catch (error: any) {
            console.error(`Error processing query ${query}`, error);
        }
    } // End of for loop

    // Statistics
    const stats = await pool.query(`
        SELECT
            COUNT(*) as total,
            COUNT(DISTINCT company) as companies,
            COUNT(CASE WHEN remote_type = 'remote' THEN 1 END) as remote_jobs,
            COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as last_week
        FROM sofia.jobs
        WHERE platform = 'findwork'
    `);

    await pool.end();

    console.log('\n' + '='.repeat(60));
    console.log(`✅ Collected: ${totalCollected} new jobs from Findwork`);
    console.log('\n📊 Findwork Statistics:');
    console.log(`   Total jobs in DB: ${stats.rows[0].total}`);
    console.log(`   Companies: ${stats.rows[0].companies}`);
    console.log(`   Remote jobs: ${stats.rows[0].remote_jobs}`);
    console.log(`   Posted last 7 days: ${stats.rows[0].last_week}`);
    console.log('='.repeat(60));

    return totalCollected;
}

if (require.main === module) {
    collectFindworkJobs()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Fatal error:', err);
            process.exit(1);
        });
}

export { collectFindworkJobs };
