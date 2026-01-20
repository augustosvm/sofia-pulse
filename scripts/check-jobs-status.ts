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
    console.log('🔍 Verifying Job Collection Status...');

    try {
        // Check sofia.jobs
        const jobsCount = await pool.query(`
            SELECT COUNT(*) as count 
            FROM sofia.jobs 
            WHERE collected_at >= CURRENT_DATE;
        `);
        console.log(`💼 'sofia.jobs' collected today: ${jobsCount.rows[0].count}`);

        // Check sofia.tech_jobs (if distinct)
        const techJobsCount = await pool.query(`
            SELECT COUNT(*) as count 
            FROM sofia.tech_jobs 
            WHERE collected_at >= CURRENT_DATE;
        `);
        console.log(`💻 'sofia.tech_jobs' collected today: ${techJobsCount.rows[0].count}`);

        // Check source breakdown for today
        const sourceBreakdown = await pool.query(`
            SELECT source, COUNT(*) as count
            FROM sofia.jobs
            WHERE collected_at >= CURRENT_DATE
            GROUP BY source
            ORDER BY count DESC;
        `);

        console.log('\n📊 Breakdown by Source (Today):');
        if (sourceBreakdown.rows.length === 0) {
            console.log('   (No jobs collected today)');
        } else {
            sourceBreakdown.rows.forEach(r => {
                console.log(`   • ${r.source}: ${r.count}`);
            });
        }

    } catch (err) {
        console.error('❌ Error checking jobs:', err.message);
    } finally {
        await pool.end();
    }
}

main();
