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
    console.log('📊 Final Intelligence Status (tech_trends):');
    try {
        const res = await pool.query(`
            SELECT source, trend_type, COUNT(*) as count
            FROM sofia.tech_trends
            GROUP BY source, trend_type
            ORDER BY source;
        `);
        console.table(res.rows);

        // Verify PWC data specifically
        const pwc = await pool.query(`
             SELECT name, score, metadata 
             FROM sofia.tech_trends 
             WHERE source='papers_with_code' 
             LIMIT 3;
        `);
        console.log('\n📜 PapersWithCode Sample:');
        console.table(pwc.rows);

        // Drop temporary table if exists
        await pool.query('DROP TABLE IF EXISTS sofia.tech_metrics CASCADE');
        console.log('\n🗑️ Dropped sofia.tech_metrics.');

    } catch (err) {
        console.error(err);
    } finally {
        await pool.end();
    }
}

main();
