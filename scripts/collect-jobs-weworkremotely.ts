#!/usr/bin/env npx tsx
/**
 * WeWorkRemotely Jobs Collector
 * API pública com vagas remote de qualidade
 */

import axios from 'axios';
import { Pool } from 'pg';
import dotenv from 'dotenv';
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

const WWR_API = 'https://weworkremotely.com/remote-jobs.json';

interface WWRJob {
    id: number;
    title: string;
    company_name: string;
    category_name: string;
    job_type: string;
    region_name: string;
    url: string;
    description: string;
    published_at: string;
}

function extractSalary(description: string) {
    const patterns = [
        /\$(\d{1,3}(?:,\d{3})*)\s*[-–]\s*\$?(\d{1,3}(?:,\d{3})*)/,
        /(\d{1,3})k\s*[-–]\s*(\d{1,3})k/i,
    ];

    for (const pattern of patterns) {
        const match = description.match(pattern);
        if (match) {
            let min = parseFloat(match[1].replace(/,/g, ''));
            let max = parseFloat(match[2].replace(/,/g, ''));

            if (match[0].toLowerCase().includes('k')) {
                min *= 1000;
                max *= 1000;
            }

            return { min, max, currency: 'USD', period: 'yearly' };
        }
    }

    return { min: null, max: null, currency: 'USD', period: 'yearly' };
}

async function collectWWRJobs() {
    console.log('💼 WeWorkRemotely Jobs Collector');
    console.log('='.repeat(60));

    const pool = new Pool(dbConfig);

    let totalCollected = 0;

    try {
        console.log('\n🔍 Fetching jobs from WeWorkRemotely...');

        const response = await axios.get<WWRJob[]>(WWR_API, {
            timeout: 15000,
            headers: {
                'User-Agent': 'Sofia-Pulse-Jobs-Collector/1.0'
            }
        });

        const jobs = response.data || [];
        console.log(`   Found: ${jobs.length} jobs`);

        for (const job of jobs) {
            try {
                // Determine if it's tech-related
                const isTech = /software|developer|engineer|devops|data|frontend|backend|fullstack|mobile|ai|ml/i.test(
                    job.title + ' ' + job.category_name
                );

                if (!isTech) continue; // Skip non-tech jobs

                const salary = extractSalary(job.description);

                // Extract location (WWR is mostly remote)
                const location = job.region_name || 'Anywhere';
                const isRemote = /anywhere|worldwide|remote/i.test(location);
                const country = isRemote ? null : job.region_name;

                // Normalize geographic data (remote jobs have null for city/state)
                const { countryId, stateId, cityId } = await normalizeLocation(pool, {
                    country: country,
                    state: null,
                    city: null
                });

                // Get or create organization
                const organizationId = await getOrCreateOrganization(
                    pool,
                    job.company_name,
                    null,
                    location,
                    country,
                    'weworkremotely'
                );

                await pool.query(`
          INSERT INTO sofia.jobs (
            job_id, platform, title, company,
            location, city, state, country, country_id, state_id, city_id, remote_type,
            description, posted_date, url,
            salary_min, salary_max, salary_currency, salary_period,
            employment_type, search_keyword, organization_id, collected_at
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, NOW())
          ON CONFLICT (job_id, platform) DO UPDATE SET
            collected_at = NOW(),
            description = EXCLUDED.description,
            organization_id = COALESCE(EXCLUDED.organization_id, sofia.jobs.organization_id),
            country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
            state_id = COALESCE(EXCLUDED.state_id, sofia.jobs.state_id),
            city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id),
            salary_min = COALESCE(EXCLUDED.salary_min, sofia.jobs.salary_min),
            salary_max = COALESCE(EXCLUDED.salary_max, sofia.jobs.salary_max)
        `, [
                    job.id.toString(),
                    'weworkremotely',
                    job.title,
                    job.company_name,
                    location,
                    null, // city (remote jobs)
                    null, // state (remote jobs)
                    country,
                    countryId,
                    stateId,
                    cityId,
                    isRemote ? 'remote' : 'onsite',
                    job.description,
                    new Date(job.published_at),
                    job.url,
                    salary.min,
                    salary.max,
                    salary.currency,
                    salary.period,
                    job.job_type.toLowerCase(),
                    job.category_name,
                    organizationId
                ]);

                totalCollected++;

            } catch (err: any) {
                console.error(`   ❌ Error inserting job ${job.id}:`, err.message);
            }
        }

    } catch (error: any) {
        if (axios.isAxiosError(error)) {
            console.error(`❌ API Error: ${error.response?.status} ${error.message}`);
        } else {
            console.error(`❌ Error:`, error.message);
        }
    }

    // Statistics
    const stats = await pool.query(`
    SELECT 
      COUNT(*) as total,
      COUNT(DISTINCT company) as companies,
      COUNT(CASE WHEN salary_min IS NOT NULL THEN 1 END) as with_salary,
      ROUND(AVG(salary_min)) as avg_min,
      ROUND(AVG(salary_max)) as avg_max
    FROM sofia.jobs
    WHERE platform = 'weworkremotely'
  `);

    await pool.end();

    console.log('\n' + '='.repeat(60));
    console.log(`✅ Collected: ${totalCollected} tech jobs from WeWorkRemotely`);
    console.log('\n📊 WeWorkRemotely Statistics:');
    console.log(`   Total jobs: ${stats.rows[0].total}`);
    console.log(`   Companies: ${stats.rows[0].companies}`);
    console.log(`   With salary: ${stats.rows[0].with_salary}`);
    if (stats.rows[0].avg_min) {
        console.log(`   Avg salary: $${stats.rows[0].avg_min.toLocaleString()} - $${stats.rows[0].avg_max.toLocaleString()}`);
    }
    console.log('='.repeat(60));

    return totalCollected;
}

if (require.main === module) {
    collectWWRJobs()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Fatal error:', err);
            process.exit(1);
        });
}

export { collectWWRJobs };
