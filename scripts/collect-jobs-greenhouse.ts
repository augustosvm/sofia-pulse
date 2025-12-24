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
import { getOrCreateOrganization } from './shared/org-helpers.js';

dotenv.config();

// US State codes mapping (Greenhouse has many US companies)
const US_STATES = new Set([
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
]);

// Country aliases
const COUNTRY_ALIASES: Record<string, string> = {
    'U.K.': 'United Kingdom',
    'UK': 'United Kingdom',
    'U.S.': 'United States',
    'U.S.A.': 'United States',
    'USA': 'United States',
};

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

// Top tech companies using Greenhouse
const COMPANIES = [
    'coinbase',
    'gitlab',
    'dropbox',
    'airbnb',
    'stripe',
    'doordash',
    'robinhood',
    'databricks',
    'figma',
    'notion',
    'plaid',
    'airtable',
    'reddit',
    'discord',
    'cloudflare',
    'gusto',
    'rippling',
    'lattice',
    'canva',
    'grammarly'
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
    let totalProcessed = 0;

    // Cache for normalized locations to avoid repeated queries
    const locationCache = new Map<string, { countryId: number | null; cityId: number | null }>();

    for (const company of COMPANIES) {
        try {
            console.log(`\n🔍 Company: "${company}"...`);

            const response = await axios.get<{ jobs: GreenhouseJob[] }>(
                `https://boards-api.greenhouse.io/v1/boards/${company}/jobs`,
                { timeout: 10000 }
            );

            const jobs = response.data?.jobs || [];
            console.log(`   Found: ${jobs.length} jobs`);

            // Process in batches of 100 for bulk insert
            const BATCH_SIZE = 100;
            for (let i = 0; i < jobs.length; i += BATCH_SIZE) {
                const batch = jobs.slice(i, Math.min(i + BATCH_SIZE, jobs.length));

                // Show progress
                const progress = Math.round((i / jobs.length) * 100);
                console.log(`   Progress: ${i}/${jobs.length} (${progress}%)`);

                // Prepare bulk insert data
                const values: any[] = [];
                const placeholders: string[] = [];
                let paramIndex = 1;

                for (const job of batch) {
                    try {
                        totalProcessed++;

                        // Extract location details
                        const locationName = job.location?.name || 'Remote';
                        const locationParts = locationName.split(',').map(s => s.trim());

                        // Parse city and country
                        let city: string | null = null;
                        let country: string | null = null;

                        // Handle "Remote - USA", "Hybrid - Luxembourg", etc.
                        if (locationName.includes('Remote') || locationName.includes('Hybrid')) {
                            const match = locationName.match(/(?:Remote|Hybrid)\s*[-–]\s*(.+)/);
                            if (match) {
                                const extracted = match[1].trim();

                                // Check if extracted part contains comma (e.g., "New York, NY")
                                if (extracted.includes(',')) {
                                    const parts = extracted.split(',').map(s => s.trim());
                                    city = parts[0];
                                    const lastPart = parts[parts.length - 1];

                                    if (US_STATES.has(lastPart.toUpperCase())) {
                                        country = 'United States';
                                    } else {
                                        country = COUNTRY_ALIASES[lastPart] || lastPart;
                                    }
                                } else if (US_STATES.has(extracted.toUpperCase())) {
                                    country = 'United States';
                                } else {
                                    country = COUNTRY_ALIASES[extracted] || extracted;
                                }
                            }
                        } else if (locationParts.length > 1) {
                            city = locationParts[0];
                            const lastPart = locationParts[locationParts.length - 1];

                            if (US_STATES.has(lastPart.toUpperCase())) {
                                country = 'United States';
                            } else {
                                country = COUNTRY_ALIASES[lastPart] || lastPart;
                            }
                        } else if (locationParts.length === 1 && !locationName.match(/remote|worldwide|global/i)) {
                            if (US_STATES.has(locationParts[0].toUpperCase())) {
                                country = 'United States';
                            } else {
                                city = locationParts[0];
                                country = 'United States';
                            }
                        }

                        // Determine remote type
                        const isRemote = /remote|anywhere|worldwide/i.test(locationName);
                        const remoteType = isRemote ? 'remote' : 'onsite';

                        // Extract employment type from metadata
                        const employmentMeta = job.metadata?.find(m => m.name === 'Employment Type');
                        const employmentType = employmentMeta?.value_type === 'single_select'
                            ? (employmentMeta.value as string)?.toLowerCase()
                            : 'full-time';

                        // Use cache for normalized locations
                        const cacheKey = `${country}|${city}`;
                        let normalizedLocation;

                        if (locationCache.has(cacheKey)) {
                            normalizedLocation = locationCache.get(cacheKey)!;
                        } else {
                            normalizedLocation = await normalizeLocation(pool, {
                                country: country,
                                city: city
                            });
                            locationCache.set(cacheKey, normalizedLocation);
                        }

                        const { countryId, cityId } = normalizedLocation;

                        // Get or create organization
                        const organizationId = await getOrCreateOrganization(
                            pool,
                            job.company_name,
                            null, // Greenhouse doesn't provide company URL
                            locationName,
                            country,
                            'greenhouse'
                        );

                        // Add to bulk insert
                        const jobValues = [
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
                            employmentType,
                            organizationId
                        ];

                        placeholders.push(`($${paramIndex}, $${paramIndex + 1}, $${paramIndex + 2}, $${paramIndex + 3}, $${paramIndex + 4}, $${paramIndex + 5}, $${paramIndex + 6}, $${paramIndex + 7}, $${paramIndex + 8}, $${paramIndex + 9}, $${paramIndex + 10}, $${paramIndex + 11}, $${paramIndex + 12}, $${paramIndex + 13}, NOW())`);
                        values.push(...jobValues);
                        paramIndex += 14;

                    } catch (err: any) {
                        // Skip this job on error
                        if (totalProcessed <= 10) {
                            console.error(`   ⚠️ Skipping job ${job.id}:`, err.message);
                        }
                    }
                }

                // Execute bulk insert (use DO NOTHING to handle both unique constraints)
                if (placeholders.length > 0) {
                    try {
                        const result = await pool.query(`
                            INSERT INTO sofia.jobs (
                                job_id, platform, title, company,
                                location, city, country, country_id, city_id, remote_type,
                                url, posted_date, employment_type, organization_id, collected_at
                            ) VALUES ${placeholders.join(', ')}
                            ON CONFLICT (job_id, platform) DO UPDATE SET
                                title = EXCLUDED.title,
                                location = EXCLUDED.location,
                                city = EXCLUDED.city,
                                organization_id = COALESCE(EXCLUDED.organization_id, sofia.jobs.organization_id),
                                country = EXCLUDED.country,
                                collected_at = NOW(),
                                country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
                                city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id),
                                remote_type = EXCLUDED.remote_type,
                                url = EXCLUDED.url,
                                posted_date = EXCLUDED.posted_date,
                                employment_type = EXCLUDED.employment_type
                        `, values);

                        totalCollected += result.rowCount || 0;
                    } catch (err: any) {
                        // If bulk insert fails (likely due to idx_jobs_unique_posting), try individual inserts
                        if (err.message.includes('idx_jobs_unique_posting')) {
                            console.log(`   ⚠️ Bulk insert conflict, using DO NOTHING approach`);

                            try {
                                const result = await pool.query(`
                                    INSERT INTO sofia.jobs (
                                        job_id, platform, title, company,
                                        location, city, country, country_id, city_id, remote_type,
                                        url, posted_date, employment_type, collected_at
                                    ) VALUES ${placeholders.join(', ')}
                                    ON CONFLICT DO NOTHING
                                `, values);

                                totalCollected += result.rowCount || 0;
                            } catch (err2: any) {
                                console.error(`   ❌ Fallback insert also failed:`, err2.message);
                            }
                        } else {
                            console.error(`   ❌ Bulk insert error:`, err.message);
                        }
                    }
                }
            }

            console.log(`   ✅ Completed: ${totalCollected} jobs inserted/updated`);
            console.log(`   📦 Location cache size: ${locationCache.size} unique locations`);

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
