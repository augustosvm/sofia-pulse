const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
    host: process.env.POSTGRES_HOST,
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER,
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB,
});

(async () => {
    try {
        console.log('Connecting to database...');
        const res = await pool.query(`
            SELECT DISTINCT ON (collector_name) 
                collector_name, 
                status, 
                started_at, 
                completed_at, 
                duration_seconds 
            FROM sofia.collector_runs 
            ORDER BY collector_name, started_at DESC;
        `);

        console.log('\n📊 LATEST COLLECTOR RUNS:');
        console.table(res.rows.map(r => ({
            Collector: r.collector_name,
            Status: r.status,
            Started: r.started_at ? new Date(r.started_at).toLocaleString() : 'N/A',
            Duration: r.duration_seconds + 's'
        })));

    } catch (err) {
        console.error('❌ Error:', err.message);
    } finally {
        await pool.end();
    }
})();
