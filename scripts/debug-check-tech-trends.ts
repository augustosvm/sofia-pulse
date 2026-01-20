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
    console.log('🔍 Checking tech_trends schema...');

    try {
        const res = await pool.query(`
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'sofia' 
            AND table_name = 'tech_trends' 
            ORDER BY ordinal_position;
        `);

        console.table(res.rows);

        // Preview data
        const sample = await pool.query('SELECT * FROM sofia.tech_trends LIMIT 3');
        console.log('\n📊 Sample Data:');
        console.log(sample.rows);

    } catch (err) {
        console.error(err);
    } finally {
        await pool.end();
    }
}

main();
