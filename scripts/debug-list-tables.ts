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
    console.log('🔍 Listing tables in sofia schema...');
    try {
        const res = await pool.query(`
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'sofia' 
            ORDER BY table_name;
        `);

        console.log('Tables found:');
        console.log(res.rows.map(r => r.table_name).join(', '));

    } catch (err) {
        console.error(err);
    } finally {
        await pool.end();
    }
}

main();
