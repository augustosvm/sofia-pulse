#!/usr/bin/env npx tsx
/**
 * Stack Exchange Trends Collector
 * Métrica: "Developer Pain" / Uso Real
 * 
 * Coleta estatísticas diárias para tags de tecnologia selecionadas:
 * - Total Questions
 * - Answer Rate
 * - Week-over-Week Growth (calculado via DB depois)
 * 
 * Fonte: Stack Exchange API (https://api.stackexchange.com/docs)
 * Quota: 300 requests/dia (sem key) ou 10k (com key)
 * Estratégia: Usar rota /tags/{tags}/info para pegar stats acumulados.
 */

import axios from 'axios';
import { Pool } from 'pg';
import dotenv from 'dotenv';
import { getKeywordsByLanguage } from './shared/keywords-config';

dotenv.config();

const dbConfig = {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
    user: process.env.POSTGRES_USER || 'sofia',
    password: process.env.POSTGRES_PASSWORD,
    database: process.env.POSTGRES_DB || 'sofia_db',
};

// Techs to track (Core list + Expansion)
// Mapeando keywords do config para tags do StackOverflow
// Ex: "react" -> "reactjs", "node" -> "node.js"
const TAG_MAPPING: Record<string, string> = {
    'react': 'reactjs',
    'react-native': 'react-native',
    'vue': 'vue.js',
    'angular': 'angular',
    'node': 'node.js',
    'python': 'python',
    'java': 'java',
    'javascript': 'javascript',
    'typescript': 'typescript',
    'golang': 'go',
    'rust': 'rust',
    'csharp': 'c#',
    'php': 'php',
    'ruby': 'ruby',
    'swift': 'swift',
    'kotlin': 'kotlin',
    'flutter': 'flutter',
    'docker': 'docker',
    'kubernetes': 'kubernetes',
    'aws': 'amazon-web-services',
    'azure': 'azure',
    'tensorflow': 'tensorflow',
    'pytorch': 'pytorch',
    'django': 'django',
    'flask': 'flask',
    'spring': 'spring',
    'laravel': 'laravel',
    'rails': 'ruby-on-rails',
    'nextjs': 'next.js',
    'postgresql': 'postgresql',
    'mongodb': 'mongodb',
    'redis': 'redis',
    'elasticsearch': 'elasticsearch',
    'git': 'git',
    'linux': 'linux',
    'jenkins': 'jenkins',
    'terraform': 'terraform',
    'scikit-learn': 'scikit-learn',
    'pandas': 'pandas',
    'numpy': 'numpy'
};

interface StackTagInfo {
    name: string;
    count: number;        // Total questions
    is_required: boolean;
    is_moderator_only: boolean;
    has_synonyms: boolean;
}

interface StackApiResponse {
    items: StackTagInfo[];
    quota_max: number;
    quota_remaining: number;
}

async function collectStackExchangeTrends() {
    console.log('📈 Stack Exchange Trends Collector');
    console.log('='.repeat(60));

    const pool = new Pool(dbConfig);
    const tags = Object.values(TAG_MAPPING);

    // Split tags into chunks of 100 (API limit per request)
    const chunkSize = 100;
    const chunks = [];
    for (let i = 0; i < tags.length; i += chunkSize) {
        chunks.push(tags.slice(i, i + chunkSize));
    }

    try {
        let totalUpdated = 0;
        const today = new Date().toISOString().split('T')[0] + ' 12:00:00+00'; // Noon UTC to avoid timezone edge cases

        for (const chunk of chunks) {
            const tagsString = chunk.join(';');
            console.log(`\n🔍 Fetching stats for ${chunk.length} tags...`);

            // https://api.stackexchange.com/docs/tags-by-name
            // site=stackoverflow
            const url = `https://api.stackexchange.com/2.3/tags/${encodeURIComponent(tagsString)}/info`;

            try {
                const response = await axios.get<StackApiResponse>(url, {
                    params: {
                        site: 'stackoverflow',
                        key: process.env.STACK_EXCHANGE_KEY // Optional if set
                    },
                    timeout: 10000
                });

                const items = response.data.items;
                console.log(`   ✅ Received data for ${items.length} tags.`);

                for (const item of items) {
                    // Map to existing tech_trends schema
                    // source='stack_overflow', name=tag, views=question_count
                    await pool.query(`
                        INSERT INTO sofia.tech_trends (
                            source, name, category, trend_type, 
                            score, views, metadata, collected_at,
                            period_start, period_end
                        ) VALUES (
                            'stack_overflow', $1, 'language_framework', 'daily_stats',
                            $2, $2, $3, $4,
                            $4, $4
                        )
                        ON CONFLICT (source, name, collected_at) 
                        DO UPDATE SET 
                            score = EXCLUDED.score,
                            views = EXCLUDED.views,
                            metadata = EXCLUDED.metadata;
                    `, [
                        item.name,
                        item.count, // Using 'score' and 'views' for question count as it's the primary metric
                        JSON.stringify({
                            is_required: item.is_required,
                            has_synonyms: item.has_synonyms
                        }),
                        today
                    ]);

                    totalUpdated++;
                }

                // Rate limiting check
                console.log(`   ⛽ Quota remaining: ${response.data.quota_remaining}`);

            } catch (error: any) {
                console.error(`   ❌ API Error:`, error.response?.data?.error_message || error.message);
            }

            // Respect polite rate limiting (even with batching)
            await new Promise(r => setTimeout(r, 2000));
        }

        console.log('\n' + '='.repeat(60));
        console.log(`✅ Collection complete. Updated ${totalUpdated} metrics.`);
        console.log('='.repeat(60));

    } catch (err: any) {
        console.error('❌ Fatal error:', err.message);
    } finally {
        await pool.end();
    }
}

// Run standalone
if (require.main === module) {
    collectStackExchangeTrends().catch(console.error);
}

export { collectStackExchangeTrends };
