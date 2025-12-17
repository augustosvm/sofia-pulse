#!/usr/bin/env npx tsx
/**
 * WeWorkRemotely Jobs Collector
 * API pública com vagas remote de qualidade
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

    const client = new Client(dbConfig);
    await client.connect();

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

                await client.query(`
          INSERT INTO sofia.jobs (
            job_id, platform, title, company,
            location, country, remote_type,
            description, posted_date, url,
            salary_min, salary_max, salary_currency, salary_period,
            employment_type, search_keyword, collected_at
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, NOW())
          ON CONFLICT (job_id, platform) DO UPDATE SET
            collected_at = NOW(),
            description = EXCLUDED.description,
            salary_min = COALESCE(EXCLUDED.salary_min, sofia.jobs.salary_min),
            salary_max = COALESCE(EXCLUDED.salary_max, sofia.jobs.salary_max)
        `, [
                    job.id.toString(),
                    'weworkremotely',
                    job.title,
                    job.company_name,
                    location,
                    isRemote ? 'REMOTE' : job.region_name,
                    isRemote ? 'remote' : 'onsite',
                    job.description,
                    new Date(job.published_at),
                    job.url,
                    salary.min,
                    salary.max,
                    salary.currency,
                    salary.period,
                    job.job_type.toLowerCase(),
                    job.category_name
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
      COUNT(CASE WHEN salary_min IS NOT NULL THEN 1 END) as with_salary,
      ROUND(AVG(salary_min)) as avg_min,
      ROUND(AVG(salary_max)) as avg_max
    FROM sofia.jobs
    WHERE platform = 'weworkremotely'
  `);

    await client.end();

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
