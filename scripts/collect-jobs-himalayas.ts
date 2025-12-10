#!/usr/bin/env npx tsx
/**
 * Himalayas Jobs Collector
 * API pública com vagas remote e dados de salário
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

const HIMALAYAS_API = 'https://himalayas.app/jobs/api';

interface HimalayasJob {
    id: string;
    title: string;
    company: {
        name: string;
        logo: string;
    };
    location: string;
    remote: boolean;
    salary: {
        min: number;
        max: number;
        currency: string;
    } | null;
    description: string;
    url: string;
    published_at: string;
    tags: string[];
}

async function collectHimalayasJobs() {
    console.log('🏔️ Himalayas Jobs Collector');
    console.log('='.repeat(60));

    const client = new Client(dbConfig);
    await client.connect();

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
                // Extract location details
                const locationParts = job.location?.split(',').map(s => s.trim()) || ['Remote'];
                const city = locationParts[0] || null;
                const country = locationParts[locationParts.length - 1] || 'REMOTE';

                const remoteType = job.remote ? 'remote' : 'onsite';

                // Extract skills from tags
                const skills = job.tags?.filter(tag => tag.length > 0) || [];

                await client.query(`
          INSERT INTO sofia.jobs (
            job_id, platform, title, company,
            location, city, country, remote_type,
            description, posted_date, url,
            salary_min, salary_max, salary_currency, salary_period,
            skills_required, collected_at
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, NOW())
          ON CONFLICT (job_id, platform) DO UPDATE SET
            collected_at = NOW(),
            description = EXCLUDED.description,
            salary_min = COALESCE(EXCLUDED.salary_min, sofia.jobs.salary_min),
            salary_max = COALESCE(EXCLUDED.salary_max, sofia.jobs.salary_max)
        `, [
                    job.id,
                    'himalayas',
                    job.title,
                    job.company.name,
                    job.location || 'Remote',
                    city,
                    country,
                    remoteType,
                    job.description,
                    new Date(job.published_at),
                    job.url,
                    job.salary?.min || null,
                    job.salary?.max || null,
                    job.salary?.currency || 'USD',
                    'yearly',
                    skills.length > 0 ? skills : null
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
    const stats = await client.query(`
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

    await client.end();

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
