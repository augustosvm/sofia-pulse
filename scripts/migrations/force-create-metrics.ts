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
    console.log('🔥 Force recreating sofia.tech_metrics table...');

    try {
        // Drop existing table to ensure clean slate
        await pool.query(`DROP TABLE IF EXISTS sofia.tech_metrics CASCADE;`);
        console.log('🗑️ Dropped existing table.');

        await pool.query(`
            CREATE TABLE sofia.tech_metrics (
                id SERIAL PRIMARY KEY,
                technology VARCHAR(255) NOT NULL,
                source VARCHAR(50) NOT NULL, -- 'stack_overflow', 'docker_hub', etc.
                metric VARCHAR(50) NOT NULL, -- 'question_count', 'pull_count', 'stars'
                value NUMERIC NOT NULL,
                metadata JSONB DEFAULT '{}', -- Extra details (e.g. 'unanswered_count')
                collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                -- Ensure daily uniqueness per metric to allow simple time-series analysis
                CONSTRAINT idx_metrics_daily_unique UNIQUE (technology, source, metric, collected_at)
            );

            -- Index for fast querying by technology and source
            CREATE INDEX idx_tech_metrics_lookup ON sofia.tech_metrics(technology, source);
            -- Index for time-range queries
            CREATE INDEX idx_tech_metrics_time ON sofia.tech_metrics(collected_at);
        `);

        console.log('✅ Table sofia.tech_metrics created successfully.');

    } catch (err) {
        console.error('❌ Error creating schema:', err);
    } finally {
        await pool.end();
    }
}

main();
