#!/usr/bin/env npx tsx
/**
 * USAJOBS Government Jobs API Collector
 * 5k+ vagas tech do governo USA
 * Salários públicos sempre disponíveis
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

const USAJOBS_API_KEY = process.env.USAJOBS_API_KEY;
const USAJOBS_EMAIL = process.env.USAJOBS_EMAIL || process.env.SMTP_USER;

const USAJOBS_API = 'https://data.usajobs.gov/api/search';

// Ocupações tech no governo USA
const TECH_OCCUPATIONS = [
    '2210', // IT Specialist
    '1550', // Computer Scientist
    '0854', // Computer Engineer
    '1520', // Mathematics/Statistician (Data Science)
];

interface USAJobsJob {
    MatchedObjectId: string;
    MatchedObjectDescriptor: {
        PositionTitle: string;
        OrganizationName: string;
        PositionLocationDisplay: string;
        PositionLocation: Array<{
            LocationName: string;
            CityName: string;
            CountryCode: string;
        }>;
        PositionRemuneration: Array<{
            MinimumRange: string;
            MaximumRange: string;
            RateIntervalCode: string;
        }>;
        UserArea: {
            Details: {
                JobSummary: string;
                WhoMayApply: {
                    Name: string;
                };
                LowGrade?: string;
                HighGrade?: string;
            };
        };
        ApplicationCloseDate: string;
        PublicationStartDate: string;
        PositionURI: string;
        PositionSchedule: Array<{
            Name: string;
        }>;
        PositionOfferingType: Array<{
            Name: string;
        }>;
    };
}

interface USAJobsResponse {
    SearchResult: {
        SearchResultItems: Array<{
            MatchedObjectDescriptor: USAJobsJob['MatchedObjectDescriptor'];
            MatchedObjectId: string;
        }>;
        SearchResultCount: number;
    };
}

async function collectUSAJobs() {
    console.log('🏛️ USAJOBS Government Jobs Collector');
    console.log('='.repeat(60));

    if (!USAJOBS_API_KEY) {
        console.error('❌ USAJOBS_API_KEY is required!');
        console.log('\n📝 Get your free API key at: https://developer.usajobs.gov/');
        process.exit(1);
    }

    if (!USAJOBS_EMAIL) {
        console.error('❌ USAJOBS_EMAIL is required (use your email)!');
        process.exit(1);
    }

    const client = new Client(dbConfig);
    await client.connect();

    let totalCollected = 0;

    try {
        // Coletar para cada ocupação tech
        for (const occupation of TECH_OCCUPATIONS) {
            console.log(`\n🔍 Collecting occupation code ${occupation}...`);

            try {
                const response = await axios.get<USAJobsResponse>(USAJOBS_API, {
                    params: {
                        JobCategoryCode: occupation,
                        ResultsPerPage: 100
                    },
                    headers: {
                        'Host': 'data.usajobs.gov',
                        'User-Agent': USAJOBS_EMAIL,
                        'Authorization-Key': USAJOBS_API_KEY
                    },
                    timeout: 15000
                });

                const items = response.data.SearchResult?.SearchResultItems || [];
                console.log(`   Found: ${items.length} jobs`);

                for (const item of items) {
                    try {
                        const job = item.MatchedObjectDescriptor;

                        // Extract salary
                        const salary = job.PositionRemuneration?.[0];
                        const salaryMin = salary ? parseFloat(salary.MinimumRange.replace(/,/g, '')) : null;
                        const salaryMax = salary ? parseFloat(salary.MaximumRange.replace(/,/g, '')) : null;
                        const salaryPeriod = salary?.RateIntervalCode === 'PA' ? 'yearly' : 'hourly';

                        // Extract location
                        const location = job.PositionLocation?.[0];
                        const city = location?.CityName || null;
                        const locationDisplay = job.PositionLocationDisplay || 'Washington, DC';

                        // Determine if remote
                        const offeringTypes = job.PositionOfferingType?.map(t => t.Name) || [];
                        const isRemote = offeringTypes.some(t => /remote/i.test(t));
                        const remoteType = isRemote ? 'remote' : 'onsite';

                        // Employment type
                        const schedules = job.PositionSchedule?.map(s => s.Name) || [];
                        const employmentType = schedules.some(s => /full.time/i.test(s)) ? 'full-time' : 'part-time';

                        await client.query(`
              INSERT INTO sofia.jobs (
                job_id, platform, title, company,
                location, city, country, remote_type,
                description, posted_date, url,
                salary_min, salary_max, salary_currency, salary_period,
                employment_type, search_keyword, collected_at
              ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, NOW())
              ON CONFLICT (job_id, platform) DO UPDATE SET
                collected_at = NOW(),
                description = EXCLUDED.description,
                salary_min = COALESCE(EXCLUDED.salary_min, sofia.jobs.salary_min),
                salary_max = COALESCE(EXCLUDED.salary_max, sofia.jobs.salary_max)
            `, [
                            item.MatchedObjectId,
                            'usajobs',
                            job.PositionTitle,
                            job.OrganizationName,
                            locationDisplay,
                            city,
                            'United States',
                            remoteType,
                            job.UserArea?.Details?.JobSummary || '',
                            new Date(job.PublicationStartDate),
                            job.PositionURI,
                            salaryMin,
                            salaryMax,
                            'USD',
                            salaryPeriod,
                            employmentType,
                            `occupation-${occupation}`
                        ]);

                        totalCollected++;

                    } catch (err: any) {
                        console.error(`   ❌ Error inserting job ${item.MatchedObjectId}:`, err.message);
                    }
                }

                // Rate limiting: aguardar 1s entre requests
                await new Promise(resolve => setTimeout(resolve, 1000));

            } catch (error: any) {
                if (axios.isAxiosError(error)) {
                    console.error(`   ❌ API Error for occupation ${occupation}: ${error.response?.status} ${error.message}`);
                } else {
                    console.error(`   ❌ Error for occupation ${occupation}:`, error.message);
                }
            }
        }

    } catch (error: any) {
        console.error(`❌ Fatal error:`, error.message);
    }

    // Statistics
    const stats = await client.query(`
    SELECT 
      COUNT(*) as total,
      COUNT(DISTINCT company) as agencies,
      COUNT(CASE WHEN remote_type = 'remote' THEN 1 END) as remote_jobs,
      COUNT(CASE WHEN salary_min IS NOT NULL THEN 1 END) as with_salary,
      ROUND(AVG(salary_min)) as avg_min,
      ROUND(AVG(salary_max)) as avg_max
    FROM sofia.jobs
    WHERE platform = 'usajobs'
  `);

    await client.end();

    console.log('\n' + '='.repeat(60));
    console.log(`✅ Collected: ${totalCollected} government tech jobs from USAJOBS`);
    console.log('\n📊 USAJOBS Statistics:');
    console.log(`   Total jobs: ${stats.rows[0].total}`);
    console.log(`   Agencies: ${stats.rows[0].agencies}`);
    console.log(`   Remote jobs: ${stats.rows[0].remote_jobs}`);
    console.log(`   With salary: ${stats.rows[0].with_salary} (should be 100%)`);
    if (stats.rows[0].avg_min) {
        console.log(`   Avg salary: $${stats.rows[0].avg_min.toLocaleString()} - $${stats.rows[0].avg_max.toLocaleString()}`);
    }
    console.log('='.repeat(60));

    return totalCollected;
}

if (require.main === module) {
    collectUSAJobs()
        .then(() => process.exit(0))
        .catch(err => {
            console.error('Fatal error:', err);
            process.exit(1);
        });
}

export { collectUSAJobs };
