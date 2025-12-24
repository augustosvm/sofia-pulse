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

    for (const query of SEARCH_QUERIES) {
        try {
            console.log(`\n🔍 Query: "${query}"...`);

            // Findwork doesn't have a public API, but we can parse the job listings page
            // Alternative: use RSS feed or scrape carefully
            const response = await axios.get(
                `https://findwork.dev/${query}-jobs`,
                {
                    headers: {
                        'User-Agent': 'Mozilla/5.0 (compatible; Sofia-Pulse-Jobs-Collector/1.0)',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    },
                    timeout: 15000
                }
            );

            // Simple regex parsing (findwork has clean HTML structure)
            const jobPattern = /href="\/([A-Za-z0-9]+)\/([^"]+)"/g;
            const jobs: Array<{ id: string; slug: string }> = [];

            let match;
            while ((match = jobPattern.exec(response.data)) !== null && jobs.length < 20) {
                const [_, id, slug] = match;
                // Filter out non-job links
                if (id.length >= 5 && id.length <= 10 && !slug.includes('/')) {
                    jobs.push({ id, slug });
                }
            }

            console.log(`   Found: ${jobs.length} jobs`);

            for (const job of jobs) {
                try {
                    // Extract location from slug (e.g., "senior-developer-at-company")
                    const parts = job.slug.split('-at-');
                    const title = parts[0]?.replace(/-/g, ' ') || 'Tech Position';
                    const company = parts[1]?.replace(/-/g, ' ') || 'Unknown';

                    // Findwork is primarily remote jobs, but location may vary
                    // Default to Remote for now
                    const location = 'Remote';
                    const country = null; // Remote jobs - no specific country
                    const city = null;

                    // Normalize geographic data (will be NULL for remote)
                    const { countryId, cityId } = await normalizeLocation(pool, {
                        country: country,
                        city: city
                    });

                    await pool.query(`
                        INSERT INTO sofia.jobs (
                            job_id, platform, title, company,
                            location, city, country, country_id, city_id, remote_type,
                            url, search_keyword, collected_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW())
                        ON CONFLICT (job_id, platform) DO UPDATE SET
                            collected_at = NOW(),
                            country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
                            city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id)
                    `, [
                        `findwork-${job.id}`,
                        'findwork',
                        title,
                        company,
                        location,
                        city,
                        country,
                        countryId,
                        cityId,
                        'remote',
                        `https://findwork.dev/${job.id}/${job.slug}`,
                        query
                    ]);

                    totalCollected++;

                } catch (err: any) {
                    console.error(`   ❌ Error inserting job ${job.id}:`, err.message);
                }
            }

            // Rate limit: 2 seconds between queries
            await new Promise(resolve => setTimeout(resolve, 2000));

        } catch (error: any) {
            if (axios.isAxiosError(error)) {
                console.error(`   ❌ Error: ${error.response?.status || error.code} ${error.message}`);
            } else {
                console.error(`   ❌ Error:`, error.message);
            }
        }
    }

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
