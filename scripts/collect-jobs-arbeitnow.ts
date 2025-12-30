#!/usr/bin/env npx tsx
/**
 * Arbeitnow Jobs Collector
 * Coleta vagas de tech da Europa (API pública, sem auth)
 * Cobertura: Alemanha, Holanda, UK, França, Espanha
 */

import axios from 'axios';
import { Pool } from 'pg';
import dotenv from 'dotenv';
import { normalizeLocation } from './shared/geo-helpers.js';
import { getOrCreateOrganization } from './shared/org-helpers.js';

dotenv.config();

// Map of European cities to countries (Arbeitnow is mainly European jobs)
const CITY_TO_COUNTRY: Record<string, string> = {
    // Germany (most common in Arbeitnow)
    'Berlin': 'Germany', 'Munich': 'Germany', 'Hamburg': 'Germany', 'Frankfurt': 'Germany',
    'Cologne': 'Germany', 'Stuttgart': 'Germany', 'Düsseldorf': 'Germany', 'Dortmund': 'Germany',
    'Essen': 'Germany', 'Leipzig': 'Germany', 'Bremen': 'Germany', 'Dresden': 'Germany',
    'Hanover': 'Germany', 'Nuremberg': 'Germany', 'Duisburg': 'Germany', 'Bochum': 'Germany',
    'Wuppertal': 'Germany', 'Bielefeld': 'Germany', 'Bonn': 'Germany', 'Münster': 'Germany',
    'Karlsruhe': 'Germany', 'Mannheim': 'Germany', 'Augsburg': 'Germany', 'Wiesbaden': 'Germany',
    'Gelsenkirchen': 'Germany', 'Mönchengladbach': 'Germany', 'Braunschweig': 'Germany',
    'Chemnitz': 'Germany', 'Kiel': 'Germany', 'Aachen': 'Germany', 'Halle': 'Germany',
    'Magdeburg': 'Germany', 'Freiburg': 'Germany', 'Krefeld': 'Germany', 'Lübeck': 'Germany',
    'Mainz': 'Germany', 'Erfurt': 'Germany', 'Rostock': 'Germany', 'Kassel': 'Germany',
    'Hagen': 'Germany', 'Potsdam': 'Germany', 'Saarbrücken': 'Germany', 'Hamm': 'Germany',
    'Mülheim': 'Germany', 'Ludwigshafen': 'Germany', 'Oldenburg': 'Germany', 'Leverkusen': 'Germany',
    'Osnabrück': 'Germany', 'Solingen': 'Germany', 'Heidelberg': 'Germany', 'Darmstadt': 'Germany',
    'Regensburg': 'Germany', 'Ingolstadt': 'Germany', 'Würzburg': 'Germany', 'Fürth': 'Germany',
    'Wolfsburg': 'Germany', 'Ulm': 'Germany', 'Heilbronn': 'Germany', 'Pforzheim': 'Germany',
    'Göttingen': 'Germany', 'Bottrop': 'Germany', 'Trier': 'Germany', 'Recklinghausen': 'Germany',
    'Bremerhaven': 'Germany', 'Koblenz': 'Germany', 'Bergisch Gladbach': 'Germany',
    'Reutlingen': 'Germany', 'Jena': 'Germany', 'Remscheid': 'Germany', 'Erlangen': 'Germany',
    'Moers': 'Germany', 'Siegen': 'Germany', 'Hildesheim': 'Germany', 'Salzgitter': 'Germany',
    'Gütersloh': 'Germany', 'Ditzingen': 'Germany', 'Unterschleißheim': 'Germany',
    'Tübingen': 'Germany', 'Neuss': 'Germany',

    // Netherlands
    'Amsterdam': 'Netherlands', 'Rotterdam': 'Netherlands', 'The Hague': 'Netherlands',
    'Utrecht': 'Netherlands', 'Eindhoven': 'Netherlands', 'Tilburg': 'Netherlands',
    'Groningen': 'Netherlands', 'Almere': 'Netherlands', 'Breda': 'Netherlands',

    // UK
    'London': 'United Kingdom', 'Manchester': 'United Kingdom', 'Birmingham': 'United Kingdom',
    'Leeds': 'United Kingdom', 'Glasgow': 'United Kingdom', 'Liverpool': 'United Kingdom',
    'Edinburgh': 'United Kingdom', 'Bristol': 'United Kingdom', 'Cambridge': 'United Kingdom',
    'Oxford': 'United Kingdom',

    // France
    'Paris': 'France', 'Lyon': 'France', 'Marseille': 'France', 'Toulouse': 'France',
    'Nice': 'France', 'Nantes': 'France', 'Strasbourg': 'France', 'Montpellier': 'France',

    // Spain
    'Madrid': 'Spain', 'Barcelona': 'Spain', 'Valencia': 'Spain', 'Seville': 'Spain',
    'Bilbao': 'Spain', 'Malaga': 'Spain',

    // Others
    'Vienna': 'Austria', 'Zurich': 'Switzerland', 'Geneva': 'Switzerland',
    'Brussels': 'Belgium', 'Copenhagen': 'Denmark', 'Stockholm': 'Sweden',
    'Oslo': 'Norway', 'Helsinki': 'Finland', 'Dublin': 'Ireland',
    'Prague': 'Czech Republic', 'Warsaw': 'Poland', 'Budapest': 'Hungary',
};

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

    const pool = new Pool(dbConfig);

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

                // Determine country
                let country: string | null = null;
                if (locationParts.length > 1) {
                    // Has comma: last part is likely the country
                    country = locationParts[locationParts.length - 1];
                } else if (city && CITY_TO_COUNTRY[city]) {
                    // Single word: lookup in city map
                    country = CITY_TO_COUNTRY[city];
                } else {
                    // Unknown single-word location: assume Germany (Arbeitnow's main market)
                    country = 'Germany';
                }

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

                // Normalize geographic data (European jobs usually don't have states)
                const { countryId, stateId, cityId } = await normalizeLocation(pool, {
                    country: country,
                    state: null,
                    city: city
                });

                // Get or create organization
                const organizationId = await getOrCreateOrganization(
                    pool,
                    job.company_name,
                    null,
                    job.location,
                    country,
                    'arbeitnow'
                );

                await pool.query(`
          INSERT INTO sofia.jobs (
            job_id, platform, title, company,
            location, city, state, country, country_id, state_id, city_id, remote_type,
            description, posted_date, url,
            employment_type, skills_required, organization_id, collected_at
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, NOW())
          ON CONFLICT (job_id, platform) DO UPDATE SET
            collected_at = NOW(),
            description = EXCLUDED.description,
            organization_id = COALESCE(EXCLUDED.organization_id, sofia.jobs.organization_id),
            country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
            state_id = COALESCE(EXCLUDED.state_id, sofia.jobs.state_id),
            city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id)
        `, [
                    job.slug,
                    'arbeitnow',
                    job.title,
                    job.company_name,
                    job.location,
                    city,
                    null, // state (European jobs don't have states)
                    country,
                    countryId,
                    stateId,
                    cityId,
                    remoteType,
                    job.description,
                    new Date(job.created_at * 1000), // Unix timestamp to Date
                    job.url,
                    employmentType,
                    skills.length > 0 ? skills : null,
                    organizationId
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
    const stats = await pool.query(`
    SELECT 
      COUNT(*) as total,
      COUNT(DISTINCT company) as companies,
      COUNT(CASE WHEN remote_type = 'remote' THEN 1 END) as remote_jobs,
      COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as last_week
    FROM sofia.jobs
    WHERE platform = 'arbeitnow'
  `);

    await pool.end();

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
