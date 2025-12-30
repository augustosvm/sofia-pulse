
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

        // Get columns
        const cols = await client.query(`
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'sofia' AND table_name = 'data_sources'
    `);
        console.log('Columns:', cols.rows.map(r => r.column_name).join(', '));

        // Get current rows
        const res = await client.query('SELECT source_id, source_name, source_category, update_frequency FROM sofia.data_sources ORDER BY source_id');
        console.log('\nCurrent Sources:');
        res.rows.forEach(r => console.log(`- [${r.source_id}] ${r.source_name} (${r.source_category}) - ${r.update_frequency}`));

    } catch (err) {
        console.error(err);
    } finally {
        client.end();
    }
}

run();
