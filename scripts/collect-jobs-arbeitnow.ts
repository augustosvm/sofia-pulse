#!/usr/bin/env npx tsx
/**
 * Arbeitnow Jobs Collector
 * Coleta vagas de tech da Europa (API pública, sem auth)
 * Cobertura: Alemanha, Holanda, UK, França, Espanha
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

const ARBEITNOW_API = 'https://www.arbeitnow.com/api/job-board-api';

interface ArbeitnowJob {
    slug: string;
    company_name: string;
    title: string;
    description: string;
    remote: boolean;
    url: string;
    tags: string[];
    job_types: string[];
    location: string;
    created_at: number;
}

async function collectArbeitnowJobs() {
    console.log('🇪🇺 Arbeitnow Jobs Collector (Europe)');
    console.log('='.repeat(60));

    const client = new Client(dbConfig);
    await client.connect();

    let totalCollected = 0;

    try {
        console.log('\n🔍 Fetching jobs from Arbeitnow...');

        const response = await axios.get<{ data: ArbeitnowJob[] }>(ARBEITNOW_API, {
            timeout: 15000
        });

        const jobs = response.data?.data || [];
        console.log(`   Found: ${jobs.length} jobs`);

        for (const job of jobs) {
            try {
                // Extract location details
                const locationParts = job.location.split(',').map(s => s.trim());
                const city = locationParts[0] || null;
                const country = locationParts[locationParts.length - 1] || null;

                // Determine remote type
                let remoteType = 'onsite';
                if (job.remote) {
                    remoteType = 'remote';
                } else if (job.location.toLowerCase().includes('hybrid')) {
                    remoteType = 'hybrid';
                }

                // Extract skills from tags
                const skills = job.tags.filter(tag =>
                    !['remote', 'onsite', 'hybrid', 'full-time', 'part-time'].includes(tag.toLowerCase())
                );

                // Determine employment type
                const employmentType = job.job_types.includes('full_time') ? 'full-time' :
                    job.job_types.includes('part_time') ? 'part-time' :
                        'contract';

                await client.query(`
          INSERT INTO sofia.tech_jobs (
            job_id, platform, title, company,
            location, city, country, remote_type,
            description, posted_date, url,
            employment_type, skills_required, collected_at
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW())
          ON CONFLICT (job_id, platform) DO UPDATE SET
            collected_at = NOW(),
            description = EXCLUDED.description
        `, [
                    job.slug,
                    'arbeitnow',
                    job.title,
                    job.company_name,
                    job.location,
                    city,
                    country,
                    remoteType,
                    job.description,
                    new Date(job.created_at * 1000), // Unix timestamp to Date
                    job.url,
                    employmentType,
                    skills.length > 0 ? skills : null
                ]);

                totalCollected++;

            } catch (err) {
                console.error(`   ❌ Error inserting job ${job.slug}:`, err.message);
            }
        }

    } catch (error) {
        if (axios.isAxiosError(error)) {
            console.error(`❌ API Error: ${error.response?.status} ${error.message}`);
        } else {
            console.error(`❌ Error:`, error.message);
        }
    }

    // Get statistics
    const stats = await client.query(`
    SELECT 
      COUNT(*) as total,
      COUNT(DISTINCT company) as companies,
      COUNT(CASE WHEN remote_type = 'remote' THEN 1 END) as remote_jobs,
      COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as last_week
    FROM sofia.tech_jobs
    WHERE platform = 'arbeitnow'
  `);

    await client.end();

    console.log('\n' + '='.repeat(60));
    console.log(`✅ Collected: ${totalCollected} new jobs from Arbeitnow`);
    console.log('\n📊 Arbeitnow Statistics:');
    console.log(`   Total jobs in DB: ${stats.rows[0].total}`);
    console.log(`   Companies: ${stats.rows[0].companies}`);
    console.log(`   Remote jobs: ${stats.rows[0].remote_jobs}`);
    console.log(`   Posted last 7 days: ${stats.rows[0].last_week}`);
    console.log('='.repeat(60));

    return totalCollected;
}

if (require.main === module) {
    collectArbeitnowJobs()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Fatal error:', err);
            process.exit(1);
        });
}

export { collectArbeitnowJobs };
