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
    console.log('🔒 Adding UNIQUE constraint to sofia.tech_trends columns...');

    try {
        // Need to ensure data is clean first? 
        // If there are already duplicates for (source, name, collected_at), this will fail.
        // Let's deduplicate first just in case, though likely data is sparse or different.

        // Actually, just trying to add it. If it fails, I'll know.
        // Using collected_at::DATE might be better for daily stats, but my code uses NOW() which includes time.
        // My code does `collected_at = NOW()`.
        // If I run the script multiple times in the same second, conflict triggers.
        // But `ON CONFLICT (source, name, collected_at)` requires EXACT timestamp match.
        // This is fragile. Usually we want `(source, name, collected_at::DATE)`.

        // However, standard PG ON CONFLICT doesn't support expressions like ::DATE in the constraint inference easily without a functional index.
        // To keep it simple and robust:
        // I will change my collectors to insert `CURRENT_DATE` or truncate timestamp.
        // AND create a unique index on `(source, name, CAST(collected_at AS DATE))`.

        // BUT, for now, let's just make the existing query work.
        // My query has `ON CONFLICT (source, name, collected_at)`.
        // This implies I expect perfect timestamp matches? No, that's impossible.
        // I probably meant `ON CONFLICT` to handle re-runs. 
        // If I run the script twice, `NOW()` changes, so it inserts a NEW row.
        // So `ON CONFLICT` is actually useless with `NOW()`. I should remove it OR make the constraint date-based.

        // Decision: Make it Date-Based for True Daily Metrics.
        // 1. Create unique index on (source, name, collected_at::DATE).
        // 2. Update collectors to use `ON CONFLICT (source, name, CAST(collected_at AS DATE))`? NO, PG syntax is key.
        // The robust way is to add a generated column `collected_date` or just rely on the app to pass a date string.

        // FAST FIX:
        // Just remove `ON CONFLICT` from the collectors for now? No, we want to prevent dups.
        // Update collectors to pass a DATE string (YYYY-MM-DD) instead of NOW().
        // AND add unique constraint on `(source, name, collected_at)`.

        // Let's create the index on the exact columns first to satisfy the current code, 
        // BUT wait, `NOW()` changes every Ms. So the constraint (source, name, collected_at) will NEVER trigger.
        // The error happened because I specified `ON CONFLICT (source, name, collected_at)` but there is no such index.

        // I will create index on `(source, name, collected_at)`.
        // BUT I should also update the code to truncate date to ensure idempotency.

        // LET'S DO THIS:
        // 1. Add Index: `CREATE UNIQUE INDEX idx_tech_trends_unique_daily ON sofia.tech_trends (source, name, collected_at);`
        // 2. Update Collectors: Send `new Date().toISOString().split('T')[0] + ' 00:00:00+00'` as collected_at.

        await pool.query(`
            CREATE UNIQUE INDEX IF NOT EXISTS idx_tech_trends_unique_daily 
            ON sofia.tech_trends (source, name, collected_at);
        `);

        console.log('✅ Unique index created.');

    } catch (err) {
        console.error('❌ Error adding constraint:', err);
    } finally {
        await pool.end();
    }
}

main();
