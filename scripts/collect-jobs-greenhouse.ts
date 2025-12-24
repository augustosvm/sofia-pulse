#!/usr/bin/env npx tsx
/**
 * Greenhouse Jobs Collector
 * Coleta vagas de múltiplas empresas tech via Greenhouse API
 * API: https://boards-api.greenhouse.io/v1/boards/{company}/jobs
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

// Top tech companies using Greenhouse
const COMPANIES = [
    'coinbase', 'gitlab', 'dropbox', 'airbnb', 'stripe', 'doordash',
    'robinhood', 'instacart', 'databricks', 'figma', 'notion',
    'plaid', 'airtable', 'reddit', 'discord', 'roblox',
    'cloudflare', 'benchling', 'gusto', 'convoy', 'rippling'
];

interface GreenhouseJob {
    id: number;
    title: string;
    company_name: string;
    absolute_url: string;
    location: {
        name: string;
    };
    updated_at: string;
    metadata?: Array<{
        name: string;
        value: string | { unit: string; amount: string };
        value_type: string;
    }>;
}

async function collectGreenhouseJobs() {
    console.log('🏢 Greenhouse Jobs Collector');
    console.log('='.repeat(60));

    const pool = new Pool(dbConfig);

    let totalCollected = 0;

    for (const company of COMPANIES) {
        try {
            console.log(`\n🔍 Company: "${company}"...`);

            const response = await axios.get<{ jobs: GreenhouseJob[] }>(
                `https://boards-api.greenhouse.io/v1/boards/${company}/jobs`,
                { timeout: 10000 }
            );

            const jobs = response.data?.jobs || [];
            console.log(`   Found: ${jobs.length} jobs`);

            for (const job of jobs) {
                try {
                    // Extract location details
                    const locationName = job.location?.name || 'Remote';
                    const locationParts = locationName.split(',').map(s => s.trim());

                    // Parse city and country
                    let city: string | null = null;
                    let country: string | null = null;

                    // Handle "Remote - USA", "San Francisco, CA", "New York", etc.
                    if (locationName.includes('Remote')) {
                        // Extract country from "Remote - USA" or "Remote - US"
                        const remoteMatch = locationName.match(/Remote\s*[-–]\s*([A-Z]{2,3}|[A-Z][a-z]+)/);
                        if (remoteMatch) {
                            country = remoteMatch[1];
                        }
                    } else if (locationParts.length > 1) {
                        // "San Francisco, CA" or "New York, USA"
                        city = locationParts[0];
                        country = locationParts[locationParts.length - 1];
                    } else if (locationParts.length === 1 && !locationName.match(/remote|worldwide|global/i)) {
                        // Single word: could be city or country
                        city = locationParts[0];
                        country = 'United States'; // Default for most Greenhouse jobs
                    }

                    // Determine remote type
                    const isRemote = /remote|anywhere|worldwide/i.test(locationName);
                    const remoteType = isRemote ? 'remote' : 'onsite';

                    // Extract employment type from metadata
                    const employmentMeta = job.metadata?.find(m => m.name === 'Employment Type');
                    const employmentType = employmentMeta?.value_type === 'single_select'
                        ? (employmentMeta.value as string)?.toLowerCase()
                        : 'full-time';

                    // Normalize geographic data
                    const { countryId, cityId } = await normalizeLocation(pool, {
                        country: country,
                        city: city
                    });

                    await pool.query(`
                        INSERT INTO sofia.jobs (
                            job_id, platform, title, company,
                            location, city, country, country_id, city_id, remote_type,
                            url, posted_date, employment_type, collected_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW())
                        ON CONFLICT (job_id, platform) DO UPDATE SET
                            collected_at = NOW(),
                            country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
                            city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id)
                    `, [
                        `greenhouse-${job.id}`,
                        'greenhouse',
                        job.title,
                        job.company_name,
                        locationName,
                        city,
                        country,
                        countryId,
                        cityId,
                        remoteType,
                        job.absolute_url,
                        new Date(job.updated_at),
                        employmentType
                    ]);

                    totalCollected++;

                } catch (err: any) {
                    console.error(`   ❌ Error inserting job ${job.id}:`, err.message);
                }
            }

            // Rate limit: 1 second between companies
            await new Promise(resolve => setTimeout(resolve, 1000));

        } catch (error: any) {
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
            COUNT(CASE WHEN remote_type = 'remote' THEN 1 END) as remote_jobs,
            COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as last_week
        FROM sofia.jobs
        WHERE platform = 'greenhouse'
    `);

    await pool.end();

    console.log('\n' + '='.repeat(60));
    console.log(`✅ Collected: ${totalCollected} new jobs from Greenhouse`);
    console.log('\n📊 Greenhouse Statistics:');
    console.log(`   Total jobs in DB: ${stats.rows[0].total}`);
    console.log(`   Companies: ${stats.rows[0].companies}`);
    console.log(`   Remote jobs: ${stats.rows[0].remote_jobs}`);
    console.log(`   Posted last 7 days: ${stats.rows[0].last_week}`);
    console.log('='.repeat(60));

    return totalCollected;
}

if (require.main === module) {
    collectGreenhouseJobs()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Fatal error:', err);
            process.exit(1);
        });
}

export { collectGreenhouseJobs };
