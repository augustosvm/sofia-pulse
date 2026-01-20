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
    console.log('📊 Checking recent job collections (last 1 hour)...');
    try {
        const res = await pool.query(`
            SELECT source, COUNT(*) as count
            FROM sofia.jobs
            WHERE collected_at > NOW() - INTERVAL '1 hour'
            GROUP BY source
            ORDER BY count DESC;
        `);

        console.log('\nJobs collected in the last hour:');
        console.table(res.rows);

        const total = res.rows.reduce((acc, r) => acc + parseInt(r.count), 0);
        console.log(`\nTotal: ${total}`);

    } catch (err) {
        console.error(err);
    } finally {
        await pool.end();
    }
}

main();
