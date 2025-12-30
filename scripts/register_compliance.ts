
import { Client } from 'pg';
import * as dotenv from 'dotenv';
import { collectors as legacyPythonCollectors } from './configs/legacy-python-config.js';
import { collectors as techTrendsCollectors } from './configs/tech-trends-config.js';
import { researchPapersCollectors } from './configs/research-papers-config.js';
import { jobsCollectors } from './configs/jobs-config.js';
import { organizationsCollectors } from './configs/organizations-config.js';
import { fundingCollectors } from './configs/funding-config.js';
import { developerToolsCollectors } from './configs/developer-tools-config.js';
import { techConferencesCollectors } from './configs/tech-conferences-config.js';
import { collectors as brazilCollectors } from './configs/brazil-config.js';
import { collectors as industrySignalsCollectors } from './configs/industry-signals-config.js';

dotenv.config();

const dbConfig = {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    user: process.env.DB_USER || 'sofia',
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME || 'sofia_db',
};

async function run() {
    const client = new Client(dbConfig);
    try {
        await client.connect();

        let added = 0;

        // Helper to register
        const register = async (id: string, name: string, cat: string, freq: string, url: string, desc: string, lic: string, prov: string) => {
            const query = `
            INSERT INTO sofia.data_sources (
                source_id, source_name, source_category, update_frequency,
                source_url, description, license_type, provider_name,
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
            ON CONFLICT (source_id) DO UPDATE SET
                source_name = EXCLUDED.source_name,
                source_category = EXCLUDED.source_category,
                update_frequency = EXCLUDED.update_frequency,
                source_url = EXCLUDED.source_url,
                description = EXCLUDED.description,
                license_type = EXCLUDED.license_type,
                provider_name = EXCLUDED.provider_name,
                updated_at = NOW();
        `;
            try {
                await client.query(query, [id, name, cat, freq, url, desc, lic, prov]);
                added++;
            } catch (e) {
                console.error(`Failed to register ${id}: ${e.message}`);
            }
        };

        // 1. Tech Trends
        for (const [k, v] of Object.entries(techTrendsCollectors)) {
            await register(k, v.displayName, 'tech', v.schedule.includes('* * * *') ? 'HOURLY' : 'DAILY', v.url, v.description, 'UNKNOWN', 'Various');
        }

        // 2. Papers
        for (const [k, v] of Object.entries(researchPapersCollectors)) {
            await register(k, v.displayName, 'science', 'DAILY', v.url, v.description, 'CC_BY', 'Various');
        }

        // 3. Jobs
        for (const [k, v] of Object.entries(jobsCollectors)) {
            await register(k, v.displayName, 'economic', 'DAILY', v.url, v.description, 'UNKNOWN', 'Various');
        }

        // 4. Orgs
        for (const [k, v] of Object.entries(organizationsCollectors)) {
            await register(k, v.displayName, 'business', 'MONTHLY', v.url, v.description, 'UNKNOWN', 'Various');
        }

        // 5. Funding
        for (const [k, v] of Object.entries(fundingCollectors)) {
            await register(k, v.displayName, 'business', 'WEEKLY', v.url, v.description, 'UNKNOWN', 'Various');
        }

        // 6. Legacy Python (MASS MIGRATION)
        console.log('Registering Legacy Python Collectors...');
        for (const [k, v] of Object.entries(legacyPythonCollectors)) {
            await register(k, v.description || v.name, v.category, 'DAILY', 'legacy-script', `Legacy Python: ${v.script}`, 'UNKNOWN', 'Legacy Bridge');
        }

        console.log(`✅ Registered/Updated ${added} sources total.`);

    } catch (err) {
        console.error('❌ Error:', err);
    } finally {
        client.end();
    }
}

run();
