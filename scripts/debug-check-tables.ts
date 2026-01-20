import { Pool } from 'pg';
import * as dotenv from 'dotenv';
dotenv.config();

const pool = new Pool({
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD || 'sofia123strong',
    database: process.env.POSTGRES_DB || 'sofia_db',
});

async function main() {
    console.log('🔍 Checking tech_* tables...');

    try {
        const res = await pool.query(`
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' 
            AND table_name LIKE 'tech_%' 
            ORDER BY table_name, ordinal_position;
        `);

        console.table(res.rows);

        // Also check if they have data
        const tables = [...new Set(res.rows.map(r => r.table_name))];
        for (const table of tables) {
            const count = await pool.query(`SELECT COUNT(*) FROM sofia.${table}`);
            console.log(`\n📊 Rows in ${table}: ${count.rows[0].count}`);
        }

    } catch (err) {
        console.error(err);
    } finally {
        await pool.end();
    }
}

main();
