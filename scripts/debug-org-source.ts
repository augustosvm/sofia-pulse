
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

        // Check organizations source_id nullability
        const res = await client.query(`
      SELECT column_name, is_nullable 
      FROM information_schema.columns 
      WHERE table_schema = 'sofia' 
      AND table_name = 'organizations' 
      AND column_name = 'source_id';
    `);
        console.log('source_id nullable:', res.rows[0]);

        // Check data_sources content
        const sources = await client.query('SELECT * FROM sofia.data_sources');
        console.log('Data Sources:', sources.rows);

    } catch (err) {
        console.error(err);
    } finally {
        client.end();
    }
}

run();
