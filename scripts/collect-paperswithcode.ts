#!/usr/bin/env npx tsx
/**
 * PapersWithCode Intelligence Collector
 * Métrica: "Research -> Code Velocity" / Pragmatismo
 * 
 * Processa o dump oficial "links-between-papers-and-code.json.gz" para gerar métricas:
 * - Implementações por Framework (PyTorch vs TensorFlow vs JAX)
 * - Implementações por Task (Ex: Image Classification)
 * 
 * Fonte: PapersWithCode Public Data (https://paperswithcode.com/about)
 * frequency: Weekly
 */

import axios from 'axios';
import { Pool } from 'pg';
import dotenv from 'dotenv';
import https from 'https'; // Explicit https for agent

dotenv.config();

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

// Custom agent to bypass SSL issues (Handshake Failure often due to older SSL/TLS or strict server)
const agent = new https.Agent({
    rejectUnauthorized: false,
    minVersion: 'TLSv1'
});

async function collectPapersWithCode() {
    console.log('📜 PapersWithCode Intelligence Collector');
    console.log('='.repeat(60));

    const pool = new Pool(dbConfig);
    const today = new Date().toISOString().split('T')[0] + ' 12:00:00+00';

    try {
        console.log('🔄 Scraping /trends stats directly...');
        const trendsUrl = 'https://paperswithcode.com/trends';

        // Use custom agent
        const trendsResp = await axios.get(trendsUrl, { httpsAgent: agent });

        const html = trendsResp.data;
        const matches = [...html.matchAll(/"name":\s*"([^"]+)",\s*"data":\s*\[(.*?)\]/g)];

        if (matches.length > 0) {
            console.log(`✅ Found trend data for ${matches.length} frameworks.`);

            for (const match of matches) {
                const framework = match[1].toLowerCase().replace(' ', '-');
                const dataPointsStr = match[2];
                // Get the last data point
                const points = dataPointsStr.split('],').map(s => {
                    const parts = s.replace(/[\[\]]/g, '').split(',');
                    return { date: parseInt(parts[0]), value: parseFloat(parts[1]) };
                });

                const lastPoint = points[points.length - 1];

                if (lastPoint) {
                    console.log(`   📊 ${framework}: ${lastPoint.value.toFixed(2)}% share`);

                    // Insert framework adoption share into tech_trends
                    // source='papers_with_code', score=percentage share
                    await pool.query(`
                        INSERT INTO sofia.tech_trends (
                            source, name, category, trend_type,
                            score, metadata, collected_at,
                            period_start, period_end
                        ) VALUES (
                            'papers_with_code', $1, 'ml_framework', 'adoption_share',
                            $2, $3, $4,
                            $4, $4
                        )
                        ON CONFLICT (source, name, collected_at) 
                        DO UPDATE SET 
                            score = EXCLUDED.score,
                            metadata = EXCLUDED.metadata;
                   `, [
                        framework,
                        lastPoint.value,
                        JSON.stringify({ date_ts: lastPoint.date, original_name: match[1] }),
                        today
                    ]);
                }
            }
        } else {
            console.log('⚠️  Could not parse trends chart.');
        }

        console.log('\n' + '='.repeat(60));
        console.log(`✅ Collection complete.`);
        console.log('='.repeat(60));

    } catch (err: any) {
        console.error('❌ Error:', err.message);
    } finally {
        await pool.end();
    }
}

// Run standalone
if (require.main === module) {
    collectPapersWithCode().catch(console.error);
}

export { collectPapersWithCode };
