
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

        const res = await client.query(`
        SELECT unnest(enum_range(NULL::sofia.license_type)) as license_type
    `);
        console.log('Valid License Types:', res.rows.map(r => r.license_type));

    } catch (err) {
        // If enum lookup fails, try checking distinct values from table
        console.error('Enum lookup failed (maybe type name is diff), checking table...', err.message);
        const res = await client.query('SELECT DISTINCT license_type FROM sofia.data_sources');
        console.log('Existing License Types:', res.rows.map(r => r.license_type));
    } finally {
        client.end();
    }
}

run();
