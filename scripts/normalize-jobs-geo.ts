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

async function normalizeJobsGeo() {
    console.log('🌍 Starting Job Location Normalization...');
    const client = new Client(DB_CONFIG);
    await client.connect();

    try {
        // Ensure extension exists
        await client.query('CREATE EXTENSION IF NOT EXISTS unaccent');

        // 1. Get stats
        const stats = await client.query(`
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN city_id IS NOT NULL THEN 1 END) as normalized
            FROM sofia.jobs
        `);
        console.log(`📊 Status: ${stats.rows[0].normalized} / ${stats.rows[0].total} jobs normalized.`);

        // 2. Fetch jobs needing normalization
        const batchSize = 5000;
        // Fetch jobs that have NO city_id but HAVE some text location data
        const result = await client.query(`
            SELECT id, raw_city, raw_state, raw_location 
            FROM sofia.jobs 
            WHERE city_id IS NULL 
            AND (raw_city IS NOT NULL OR raw_location IS NOT NULL)
            LIMIT $1
        `, [batchSize]);

        const jobs = result.rows;

        if (jobs.length === 0) {
            console.log('✅ No pending jobs to normalize.');
            process.exit(0);
        }

        console.log(`🔄 Processing batch of ${jobs.length} jobs...`);

        let matched = 0;

        for (const job of jobs) {
            let cityId = null;
            let stateId = null;
            let countryId = null;

            // Strategy A: Direct Match on raw_city/raw_state
            if (job.raw_city && job.raw_state) {
                const cityMatch = await client.query(`
                    SELECT c.id, c.state_id, s.country_id 
                    FROM sofia.cities c
                    JOIN sofia.states s ON c.state_id = s.id
                    WHERE LOWER(UNACCENT(c.name)) = LOWER(UNACCENT($1::text))
                    AND (
                        LOWER(UNACCENT(s.name)) = LOWER(UNACCENT($2::text))
                        OR LOWER(s.code) = LOWER($2::text)
                    )
                    LIMIT 1
                `, [job.raw_city, job.raw_state]);

                if (cityMatch.rows.length > 0) {
                    cityId = cityMatch.rows[0].id;
                    stateId = cityMatch.rows[0].state_id;
                    countryId = cityMatch.rows[0].country_id;
                }
            }

            // Strategy B: Parse from raw_location "City, State, Country" or "City, State"
            if (!cityId && job.raw_location) {
                const parts = job.raw_location.split(',').map((s: string) => s.trim());
                if (parts.length >= 2) {
                    const potentialCity = parts[0];
                    const potentialState = parts[1];

                    const locMatch = await client.query(`
                        SELECT c.id, c.state_id, s.country_id 
                        FROM sofia.cities c
                        JOIN sofia.states s ON c.state_id = s.id
                        WHERE LOWER(UNACCENT(c.name)) = LOWER(UNACCENT($1::text))
                        AND (
                            LOWER(UNACCENT(s.name)) = LOWER(UNACCENT($2::text))
                            OR LOWER(s.code) = LOWER($2::text)
                        )
                        LIMIT 1
                     `, [potentialCity, potentialState]);

                    if (locMatch.rows.length > 0) {
                        cityId = locMatch.rows[0].id;
                        stateId = locMatch.rows[0].state_id;
                        countryId = locMatch.rows[0].country_id;
                    }
                }
            }

            // Update if matched
            if (cityId) {
                await client.query(`
                    UPDATE sofia.jobs 
                    SET city_id = $1, state_id = $2, country_id = $3
                    WHERE id = $4
                `, [cityId, stateId, countryId, job.id]);
                matched++;
                process.stdout.write('.');
            } else {
                process.stdout.write('x');
            }
        }

        console.log(`\n\n✅ Batch complete. Normalized: ${matched} / ${jobs.length}`);

    } catch (e) {
        console.error("Error:", e);
    } finally {
        await client.end();
    }
}

normalizeJobsGeo();
