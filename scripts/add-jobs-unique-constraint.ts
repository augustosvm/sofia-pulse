#!/usr/bin/env npx tsx
/**
 * Add UNIQUE constraint to sofia.jobs table
 */

import { Client } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

async function addConstraint() {
    const client = new Client(dbConfig);
    await client.connect();

    try {
        // Check if constraint exists
        const check = await client.query(`
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_schema = 'sofia' 
            AND table_name = 'jobs' 
            AND constraint_name = 'jobs_unique_job_platform'
        `);

        if (check.rows.length > 0) {
            console.log('✅ Constraint "jobs_unique_job_platform" already exists');
        } else {
            console.log('Adding UNIQUE constraint on (job_id, platform)...');
            await client.query(`
                ALTER TABLE sofia.jobs 
                ADD CONSTRAINT jobs_unique_job_platform 
                UNIQUE (job_id, platform)
            `);
            console.log('✅ Constraint added successfully!');
        }
    } catch (error: any) {
        console.error('❌ Error:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

addConstraint()
    .then(() => process.exit(0))
    .catch(err => {
        console.error('Fatal error:', err);
        process.exit(1);
    });
