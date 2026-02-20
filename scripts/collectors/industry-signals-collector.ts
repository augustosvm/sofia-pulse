
import { SignalCollectorConfig } from '../configs/industry-signals-config.js';
import { IndustrySignalsInserter } from './industry-signals-inserter.js';
import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

// Supports DB_*, POSTGRES_*, and DATABASE_URL env var conventions
function getDbConfig() {
    const databaseUrl = process.env.DATABASE_URL;
    if (databaseUrl) {
        try {
            const u = new URL(databaseUrl);
            return { host: u.hostname, port: parseInt(u.port||'5432'), user: u.username||'sofia',
                     password: decodeURIComponent(u.password||''), database: (u.pathname||'/sofia_db').slice(1) };
        } catch {}
    }
    return {
        host: process.env.DB_HOST || process.env.POSTGRES_HOST || 'localhost',
        port: parseInt(process.env.DB_PORT || process.env.POSTGRES_PORT || '5432'),
        user: process.env.DB_USER || process.env.POSTGRES_USER || 'sofia',
        password: process.env.DB_PASSWORD || process.env.POSTGRES_PASSWORD,
        database: process.env.DB_NAME || process.env.POSTGRES_DB || 'sofia_db',
    };
}
const dbConfig = getDbConfig();

export async function runIndustrySignalsCLI(collectors: Record<string, SignalCollectorConfig>) {
    const args = process.argv.slice(2);
    const collectorName = args[0];

    const config = collectors[collectorName];
    if (!config) {
        console.error(`❌ Unknown collector: ${collectorName}`);
        process.exit(1);
    }

    console.log(`🚀 Starting ${config.displayName}...`);
    console.log('='.repeat(60));

    const pool = new Pool(dbConfig);
    const inserter = new IndustrySignalsInserter(pool);

    try {
        let data = [];

        // Fetch
        if (config.url) {
            console.log(`📡 Fetching from ${config.url}...`);
            const response = await axios.get(config.url);
            data = response.data;
        } else {
            console.log(`📡 Running custom fetcher...`);
            // For custom logic (like GDELT), we could delegate here if needed
            data = {};
        }

        // Parse
        console.log('🔄 Parsing response...');
        const items = typeof config.parseResponse === 'function'
            ? await config.parseResponse(data)
            : [];

        console.log(`   ✅ Parsed ${items.length} items`);

        // Insert
        if (items.length > 0) {
            console.log('💾 Inserting into sofia.industry_signals...');
            await inserter.batchInsert(items);
            console.log(`✅ Collection complete: ${items.length} items (Unified Table).`);
        } else {
            console.log('ℹ️  No items to insert.');
        }

    } catch (error: any) {
        console.error('❌ Error:', error.message);
        process.exit(1);
    } finally {
        await pool.end();
    }
}
