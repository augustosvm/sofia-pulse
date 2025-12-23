
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

        // Check Countries
        console.log('--- Countries Schema ---');
        const countries = await client.query(`
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'sofia' AND table_name = 'countries'
    `);
        countries.rows.forEach(r => console.log(`${r.column_name} (${r.data_type})`));

        // Check Cities
        console.log('\n--- Cities Schema ---');
        const cities = await client.query(`
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'sofia' AND table_name = 'cities'
    `);
        cities.rows.forEach(r => console.log(`${r.column_name} (${r.data_type})`));

    } catch (err) {
        console.error(err);
    } finally {
        client.end();
    }
}

run();
