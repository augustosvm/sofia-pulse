
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

        const tables = ['tech_trends', 'comexstat_trade', 'fiesp_sensor', 'industry_signals'];

        for (const t of tables) {
            console.log(`\n--- ${t} Schema ---`);
            const res = await client.query(`
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' AND table_name = '${t}'
        `);
            res.rows.forEach(r => console.log(`${r.column_name} (${r.data_type})`));

            // Count rows
            const count = await client.query(`SELECT COUNT(*) FROM sofia.${t}`);
            console.log(`Rows: ${count.rows[0].count}`);
        }

    } catch (err) {
        console.error(err);
    } finally {
        client.end();
    }
}

run();
