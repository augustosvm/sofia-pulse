#!/usr/bin/env npx tsx
/**
 * Himalayas Jobs Collector
 * API pública com vagas remote e dados de salário
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

const HIMALAYAS_API = 'https://himalayas.app/jobs/api';

interface HimalayasJob {
    guid: string;
    title: string;
    companyName: string;
    companyLogo: string;
    locationRestrictions?: string[];
    employmentType: string;
    minSalary: number | null;
    maxSalary: number | null;
    currency: string;
    description: string;
    applicationLink: string;
    pubDate: number;
    categories?: string[];
}

async function collectHimalayasJobs() {
    console.log('🏔️ Himalayas Jobs Collector');
    console.log('='.repeat(60));

    const pool = new Pool(dbConfig);

    let totalCollected = 0;

    try {
        console.log('\n🔍 Fetching jobs from Himalayas...');

        const response = await axios.get<{ jobs: HimalayasJob[] }>(HIMALAYAS_API, {
            timeout: 15000,
            headers: {
                'User-Agent': 'Sofia-Pulse-Jobs-Collector/1.0'
            }
        });

        const jobs = response.data?.jobs || [];
        console.log(`   Found: ${jobs.length} jobs`);

        for (const job of jobs) {
            try {
                // Validate required fields
                if (!job.companyName || !job.title) {
                    console.log(`   ⚠️ Skipping job with missing required fields`);
                    continue;
                }

                // Extract location details
                const locations = job.locationRestrictions || ['Remote'];
                const location = locations.join(', ');
                const country = locations[0] || 'REMOTE';
                const isRemote = locations.some(loc => /anywhere|worldwide|remote/i.test(loc));

                // Extract skills from categories
                const skills = job.categories?.filter(cat => cat.length > 0) || [];

                // Convert Unix timestamp to Date
                const postedDate = new Date(job.pubDate * 1000);

                // Normalize geographic data
                const { countryId } = await normalizeLocation(pool, {
                    country: country
                });

                await pool.query(`
          INSERT INTO sofia.jobs (
            job_id, platform, title, company,
            location, country, country_id, remote_type,
            description, posted_date, url,
            salary_min, salary_max, salary_currency, salary_period,
            employment_type, skills_required, collected_at
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, NOW())
          ON CONFLICT (job_id, platform) DO UPDATE SET
            collected_at = NOW(),
            description = EXCLUDED.description,
            country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
            salary_min = COALESCE(EXCLUDED.salary_min, sofia.jobs.salary_min),
            salary_max = COALESCE(EXCLUDED.salary_max, sofia.jobs.salary_max)
        `, [
                    job.guid,
                    'himalayas',
                    job.title,
                    job.companyName,
                    location,
                    country,
                    countryId,
                    isRemote ? 'remote' : 'onsite',
                    job.description,
                    postedDate,
                    job.applicationLink,
                    job.minSalary,
                    job.maxSalary,
                    job.currency || 'USD',
                    'yearly',
                    job.employmentType?.toLowerCase() || 'full-time',
                    skills.length > 0 ? skills : null
                ]);

                totalCollected++;

            } catch (err: any) {
                console.error(`   ❌ Error inserting job ${job.guid}:`, err.message);
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
      COUNT(CASE WHEN remote_type = 'remote' THEN 1 END) as remote_jobs,
      COUNT(CASE WHEN salary_min IS NOT NULL THEN 1 END) as with_salary,
      ROUND(AVG(salary_min)) as avg_min,
      ROUND(AVG(salary_max)) as avg_max
    FROM sofia.jobs
    WHERE platform = 'himalayas'
  `);

    await pool.end();

    console.log('\n' + '='.repeat(60));
    console.log(`✅ Collected: ${totalCollected} jobs from Himalayas`);
    console.log('\n📊 Himalayas Statistics:');
    console.log(`   Total jobs: ${stats.rows[0].total}`);
    console.log(`   Companies: ${stats.rows[0].companies}`);
    console.log(`   Remote jobs: ${stats.rows[0].remote_jobs}`);
    console.log(`   With salary: ${stats.rows[0].with_salary}`);
    if (stats.rows[0].avg_min) {
        console.log(`   Avg salary: $${stats.rows[0].avg_min.toLocaleString()} - $${stats.rows[0].avg_max.toLocaleString()}`);
    }
    console.log('='.repeat(60));

    return totalCollected;
}

if (require.main === module) {
    collectHimalayasJobs()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Fatal error:', err);
            process.exit(1);
        });
}

export { collectHimalayasJobs };
