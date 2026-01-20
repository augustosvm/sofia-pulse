import { Client } from 'pg';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Load .env from project root
dotenv.config({ path: path.join(__dirname, '..', '.env') });

const DB_CONFIG = {
    host: process.env.POSTGRES_HOST || "91.98.158.19",
    port: parseInt(process.env.POSTGRES_PORT || "5432"),
    database: process.env.POSTGRES_DB || "sofia_db",
    user: process.env.POSTGRES_USER || "sofia",
    password: process.env.POSTGRES_PASSWORD || "SofiaPulse2025Secure@DB"
};

// Simple normalization: lowercase, remove special chars, trim
const clean = (str: string) => {
    if (!str) return '';
    return str.toLowerCase()
        .normalize("NFD").replace(/[\u0300-\u036f]/g, "") // remove accents
        .replace(/[^a-z0-9]/g, "") // remove non-alphanumeric
        .trim();
};

async function normalizeJobsOrgs() {
    console.log('🏢 Starting Job Organization Normalization...');
    const client = new Client(DB_CONFIG);
    await client.connect();

    try {
        // 1. Ensure unaccent extension (just in case)
        await client.query('CREATE EXTENSION IF NOT EXISTS unaccent');

        // 2. Load all organizations into memory (5k is small enough)
        console.log('📦 Loading organizations...');
        const orgsResult = await client.query('SELECT id, name FROM sofia.organizations');
        const orgMap = new Map<string, number>();

        orgsResult.rows.forEach(row => {
            const normalized = clean(row.name);
            if (normalized) {
                orgMap.set(normalized, row.id);
            }
        });
        console.log(`✅ Loaded ${orgMap.size} unique normalized organizations.`);

        // 3. Fetch jobs needing normalization
        // Only fetch those where we actually have a company name
        const result = await client.query(`
            SELECT id, company 
            FROM sofia.jobs 
            WHERE organization_id IS NULL 
            AND company IS NOT NULL 
            AND company != ''
        `);

        const jobs = result.rows;
        if (jobs.length === 0) {
            console.log('✅ No pending jobs to normalize.');
            process.exit(0);
        }

        console.log(`🔄 Processing ${jobs.length} jobs...`);

        let matched = 0;
        let created = 0; // We won't create for now, just track match

        for (const job of jobs) {
            const normalizedCompany = clean(job.company);

            if (orgMap.has(normalizedCompany)) {
                const orgId = orgMap.get(normalizedCompany);
                await client.query('UPDATE sofia.jobs SET organization_id = $1 WHERE id = $2', [orgId, job.id]);
                matched++;
                process.stdout.write('.');
            } else {
                // If we were creating, we'd do it here. 
                // For now, just mark progress sans match
                process.stdout.write('x');
            }
        }

        console.log(`\n\n✅ Complete. Matched: ${matched} / ${jobs.length}`);

        // Final stats
        const finalStats = await client.query(`
            SELECT 
                COUNT(*) as total,
                COUNT(organization_id) as normalized
            FROM sofia.jobs
        `);
        console.log(`📊 Final Status: ${finalStats.rows[0].normalized} / ${finalStats.rows[0].total} jobs have organization_id.`);

    } catch (e) {
        console.error("Error:", e);
    } finally {
        await client.end();
    }
}

normalizeJobsOrgs();
