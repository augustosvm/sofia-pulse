#!/usr/bin/env npx tsx
/**
 * The Muse Jobs Collector
 * API pública com dados de salário e benefícios
 */

import axios from 'axios';
import { Pool } from 'pg';
import dotenv from 'dotenv';
import { normalizeLocation } from './shared/geo-helpers.js';

dotenv.config();

// US State codes mapping (TheMuse is primarily US jobs)
const US_STATES = new Set([
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
]);

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

const THE_MUSE_API = 'https://www.themuse.com/api/public/jobs';

interface MuseJob {
    id: number;
    name: string;
    company: {
        id: number;
        name: string;
        short_name: string;
    };
    locations: Array<{
        name: string;
    }>;
    categories: Array<{
        name: string;
    }>;
    levels: Array<{
        name: string;
        short_name: string;
    }>;
    tags: string[];
    publication_date: string;
    refs: {
        landing_page: string;
    };
    contents: string;
}

function extractSalaryFromDescription(description: string): {
    min: number | null;
    max: number | null;
    currency: string;
    period: string;
} {
    // Patterns: $100k-$150k, $100,000-$150,000, 100k-150k USD, etc
    const patterns = [
        /\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|K)?\s*[-–]\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|K)?/,
        /(\d{1,3}(?:,\d{3})*)\s*[-–]\s*(\d{1,3}(?:,\d{3})*)\s*(USD|EUR|GBP|BRL)/i,
        /salary.*?\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|K)?\s*[-–]\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|K)?/i,
    ];

    for (const pattern of patterns) {
        const match = description.match(pattern);
        if (match) {
            let min = parseFloat(match[1].replace(/,/g, ''));
            let max = parseFloat(match[2].replace(/,/g, ''));

            // If values are in 'k' format (e.g., 100k), multiply by 1000
            if (match[0].toLowerCase().includes('k')) {
                min *= 1000;
                max *= 1000;
            }

            const currency = match[3]?.toUpperCase() || 'USD';

            // Detect period (yearly, monthly, hourly)
            const period = /hour|hr/i.test(description) ? 'hourly' :
                /month/i.test(description) ? 'monthly' : 'yearly';

            return { min, max, currency, period };
        }
    }

    return { min: null, max: null, currency: 'USD', period: 'yearly' };
}

async function collectTheMuseJobs() {
    console.log('🎨 The Muse Jobs Collector');
    console.log('='.repeat(60));

    const pool = new Pool(dbConfig);

    let totalCollected = 0;
    const categories = [
        'Software Engineering',
        'Data Science',
        'Product',
        'Design',
        'Engineering',
    ];

    for (const category of categories) {
        try {
            console.log(`\n🔍 Category: "${category}"...`);

            let page = 0;
            let hasMore = true;

            while (hasMore && page < 5) { // Max 5 pages per category
                const response = await axios.get<{ results: MuseJob[] }>(THE_MUSE_API, {
                    params: {
                        category: category,
                        page: page,
                        descending: true
                    },
                    timeout: 10000
                });

                const jobs = response.data?.results || [];

                if (jobs.length === 0) {
                    hasMore = false;
                    break;
                }

                console.log(`   Page ${page + 1}: ${jobs.length} jobs`);

                for (const job of jobs) {
                    try {
                        // Extract location
                        const location = job.locations[0]?.name || 'Remote';
                        const locationParts = location.split(',').map(s => s.trim());
                        const city = locationParts[0] || null;

                        // Determine country
                        let country = 'United States'; // Default for TheMuse (primarily US jobs)
                        if (locationParts.length > 1) {
                            const lastPart = locationParts[locationParts.length - 1];
                            // Check if last part is a US state code
                            if (US_STATES.has(lastPart.toUpperCase())) {
                                country = 'United States';
                            } else {
                                country = lastPart; // Assume it's a country name
                            }
                        } else if (location && US_STATES.has(location.toUpperCase())) {
                            // Single part is a US state code
                            country = 'United States';
                        } else if (!/remote|flexible|anywhere/i.test(location)) {
                            // Single part, not a state, not remote → might be a country
                            country = location;
                        }

                        // Detect remote
                        const isRemote = /remote|anywhere|flexible/i.test(location);
                        const remoteType = isRemote ? 'remote' : 'onsite';

                        // Extract seniority
                        const seniorityLevel = job.levels[0]?.short_name || null;

                        // Extract skills from tags and categories
                        const skills = [
                            ...job.tags,
                            ...job.categories.map(c => c.name)
                        ].filter(s => s.length > 0);

                        // Extract salary from description
                        const salary = extractSalaryFromDescription(job.contents);

                        // Normalize geographic data
                        const { countryId, cityId } = await normalizeLocation(pool, {
                            country: country,
                            city: city
                        });

                        await pool.query(`
              INSERT INTO sofia.jobs (
                job_id, platform, title, company,
                location, city, country, country_id, city_id, remote_type,
                description, posted_date, url,
                salary_min, salary_max, salary_currency, salary_period,
                seniority_level, skills_required, search_keyword,
                collected_at
              ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, NOW())
              ON CONFLICT (job_id, platform) DO UPDATE SET
                collected_at = NOW(),
                description = EXCLUDED.description,
                country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
                city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id),
                salary_min = COALESCE(EXCLUDED.salary_min, sofia.jobs.salary_min),
                salary_max = COALESCE(EXCLUDED.salary_max, sofia.jobs.salary_max)
            `, [
                            job.id.toString(),
                            'themuse',
                            job.name,
                            job.company.name,
                            location,
                            city,
                            country,
                            countryId,
                            cityId,
                            remoteType,
                            job.contents,
                            new Date(job.publication_date),
                            job.refs.landing_page,
                            salary.min,
                            salary.max,
                            salary.currency,
                            salary.period,
                            seniorityLevel,
                            skills.length > 0 ? skills : null,
                            category
                        ]);

                        totalCollected++;

                    } catch (err) {
                        console.error(`   ❌ Error inserting job ${job.id}:`, err.message);
                    }
                }

                page++;
                await new Promise(resolve => setTimeout(resolve, 1000)); // Rate limit
            }

        } catch (error) {
            if (axios.isAxiosError(error)) {
                console.error(`   ❌ API Error: ${error.response?.status} ${error.message}`);
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
      COUNT(CASE WHEN salary_min IS NOT NULL THEN 1 END) as with_salary,
      ROUND(AVG(salary_min)) as avg_min_salary,
      ROUND(AVG(salary_max)) as avg_max_salary
    FROM sofia.jobs
    WHERE platform = 'themuse'
  `);

    await pool.end();

    console.log('\n' + '='.repeat(60));
    console.log(`✅ Collected: ${totalCollected} jobs from The Muse`);
    console.log('\n📊 The Muse Statistics:');
    console.log(`   Total jobs: ${stats.rows[0].total}`);
    console.log(`   Companies: ${stats.rows[0].companies}`);
    console.log(`   With salary: ${stats.rows[0].with_salary} (${((stats.rows[0].with_salary / stats.rows[0].total) * 100).toFixed(1)}%)`);
    if (stats.rows[0].avg_min_salary) {
        console.log(`   Avg salary: $${stats.rows[0].avg_min_salary.toLocaleString()} - $${stats.rows[0].avg_max_salary.toLocaleString()}`);
    }
    console.log('='.repeat(60));

    return totalCollected;
}

if (require.main === module) {
    collectTheMuseJobs()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Fatal error:', err);
            process.exit(1);
        });
}

export { collectTheMuseJobs };
