
import { Client } from 'pg';
import * as dotenv from 'dotenv';
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

        // Get all distinct collector names ever run
        const res = await client.query(`
        SELECT DISTINCT collector_name 
        FROM sofia.collector_runs 
        ORDER BY collector_name
    `);
        console.log('Distinct Collectors in History:', res.rows.length);
        res.rows.forEach(r => console.log(`- ${r.collector_name}`));

        // Also check data_sources again just in case
        const sources = await client.query('SELECT source_id FROM sofia.data_sources');
        console.log('\nSources in Data Sources Table:', sources.rows.length);

    } catch (err) {
        console.error(err);
    } finally {
        client.end();
    }
}

run();
