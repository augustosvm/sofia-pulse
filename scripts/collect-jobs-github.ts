#!/usr/bin/env npx tsx
/**
 * GitHub Jobs Collector
 * Coleta vagas de tech do GitHub Jobs (API pública, sem auth)
 */

import axios from 'axios';
import { Pool } from 'pg';
import dotenv from 'dotenv';
import { getKeywordsByLanguage } from './shared/keywords-config';
import { normalizeLocation } from './shared/geo-helpers.js';

dotenv.config();

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

const GITHUB_JOBS_API = 'https://jobs.github.com/positions.json';

interface GitHubJob {
    id: string;
    type: string;
    url: string;
    created_at: string;
    company: string;
    company_url: string;
    location: string;
    title: string;
    description: string;
    how_to_apply: string;
    company_logo: string;
}

async function collectGitHubJobs() {
    console.log('🔍 GitHub Jobs Collector');
    console.log('='.repeat(60));

    const pool = new Pool(dbConfig);

    let totalCollected = 0;
    const keywords = getKeywordsByLanguage('en');

    for (const keyword of keywords) {
        try {
            console.log(`\n🔍 Searching: "${keyword}"...`);

            const response = await axios.get<GitHubJob[]>(GITHUB_JOBS_API, {
                params: {
                    description: keyword,
                    full_time: true
                },
                timeout: 10000
            });

            const jobs = response.data || [];
            console.log(`   Found: ${jobs.length} jobs`);

            for (const job of jobs) {
                try {
                    // Extract location details
                    const locationParts = job.location.split(',').map(s => s.trim());
                    const city = locationParts[0] || null;
                    const country = locationParts[locationParts.length - 1] || null;

                    // Detect remote
                    const isRemote = /remote|anywhere|worldwide/i.test(job.location);
                    const remoteType = isRemote ? 'remote' : 'onsite';

                    // Normalize geographic data
                    const { countryId, cityId } = await normalizeLocation(pool, {
                        country: country,
                        city: city
                    });

                    await pool.query(`
            INSERT INTO sofia.jobs (
              job_id, platform, title, company, company_url,
              location, city, country, country_id, city_id, remote_type,
              description, posted_date, url, search_keyword,
              employment_type, collected_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, NOW())
            ON CONFLICT (job_id, platform) DO UPDATE SET
              collected_at = NOW()
          `, [
                        job.id,
                        'github',
                        job.title,
                        job.company,
                        job.company_url,
                        job.location,
                        city,
                        country,
                        countryId,
                        cityId,
                        remoteType,
                        job.description,
                        new Date(job.created_at),
                        job.url,
                        keyword,
                        job.type.toLowerCase()
                    ]);

                    totalCollected++;
                } catch (err: any) {
                    console.error(`   ❌ Error inserting job ${job.id}:`, err.message);
                }
            }

            // Rate limiting
            await new Promise(resolve => setTimeout(resolve, 1000));

        } catch (error: any) {
            if (axios.isAxiosError(error)) {
                console.error(`   ❌ API Error: ${error.response?.status} ${error.message}`);
            } else {
                console.error(`   ❌ Error:`, error.message);
            }
        }
    }

    await pool.end();

    console.log('\n' + '='.repeat(60));
    console.log(`✅ Total collected: ${totalCollected} jobs from GitHub`);
    console.log('='.repeat(60));

    return totalCollected;
}

if (require.main === module) {
    collectGitHubJobs()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Fatal error:', err);
            process.exit(1);
        });
}

export { collectGitHubJobs };
