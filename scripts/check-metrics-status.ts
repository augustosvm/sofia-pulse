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
    console.log('📊 Intelligence Metrics Status:');
    try {
        const res = await pool.query(`
            SELECT source, metric, COUNT(*) as count, MIN(value) as min_val, MAX(value) as max_val
            FROM sofia.tech_metrics
            GROUP BY source, metric
            ORDER BY source, metric;
        `);

        console.table(res.rows);

        // Show top 5 items for Docker to prove it's capturing different images
        const dockerTop = await pool.query(`
            SELECT technology, value 
            FROM sofia.tech_metrics 
            WHERE source = 'docker_hub' AND metric = 'pull_count' 
            ORDER BY value DESC 
            LIMIT 5;
        `);
        console.log('\n🐳 Top 5 Docker Images by Pulls:');
        console.table(dockerTop.rows);

    } catch (err) {
        console.error(err);
    } finally {
        await pool.end();
    }
}

main();
