/**
 * Generic Trends Inserter - TypeScript
 * Insere qualquer tipo de trend em tech_trends com um único método
 */

import { Pool, PoolClient } from 'pg';

export interface TrendData {
    source: 'github' | 'stackoverflow' | 'npm' | 'pypi' | string;
    name: string;
    category?: string;
    trend_type?: string;
    score?: number;
    rank?: number;
    stars?: number;
    forks?: number;
    views?: number;
    mentions?: number;
    growth_rate?: number;
    period_start?: Date;
    period_end?: Date;
    metadata?: Record<string, any>;
}

export class TrendsInserter {
    private pool: Pool;

    constructor(pool: Pool) {
        this.pool = pool;
    }

    /**
     * Insert genérico - aceita qualquer combinação de campos
     */
    async insert(trend: TrendData, client?: PoolClient): Promise<void> {
        const db = client || this.pool;

        // Campos base obrigatórios
        const fields: string[] = ['source', 'name'];
        const values: any[] = [trend.source, trend.name];
        const placeholders: string[] = ['$1', '$2'];
        let paramCount = 2;

        // Campos opcionais
        const optionalFields: (keyof TrendData)[] = [
            'category', 'trend_type', 'score', 'rank',
            'stars', 'forks', 'views', 'mentions', 'growth_rate',
            'period_start', 'period_end', 'metadata'
        ];

        // Adiciona campos que foram passados
        for (const field of optionalFields) {
            if (trend[field] !== undefined && trend[field] !== null) {
                fields.push(field);

                // Converte metadata para JSON
                if (field === 'metadata') {
                    values.push(JSON.stringify(trend[field]));
                } else {
                    values.push(trend[field]);
                }

                placeholders.push(`$${++paramCount}`);
            }
        }

        // Monta query dinamicamente
        const fieldsStr = fields.join(', ');
        const placeholdersStr = placeholders.join(', ');

        // Campos para UPDATE (todos exceto source, name, period_start)
        const updateFields = fields.filter(f => !['source', 'name', 'period_start'].includes(f));
        const updateStr = updateFields.map(f => `${f} = EXCLUDED.${f}`).join(', ');

        const query = `
      INSERT INTO sofia.tech_trends (${fieldsStr})
      VALUES (${placeholdersStr})
      ON CONFLICT (source, name, period_start) DO UPDATE SET
        ${updateStr},
        collected_at = NOW()
    `;

        await db.query(query, values);
    }

    /**
     * Batch insert de múltiplos trends
     */
    async batchInsert(trends: TrendData[]): Promise<void> {
        const client = await this.pool.connect();
        try {
            await client.query('BEGIN');
            for (const trend of trends) {
                await this.insert(trend, client);
            }
            await client.query('COMMIT');
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }
}

// Exemplo de uso:
/*
const inserter = new TrendsInserter(pool);

// GitHub
await inserter.insert({
  source: 'github',
  name: 'langchain',
  category: 'AI',
  stars: 50000,
  forks: 5000,
  period_start: new Date(),
  metadata: { language: 'Python' }
});

// StackOverflow
await inserter.insert({
  source: 'stackoverflow',
  name: 'python',
  views: 1000000,
  mentions: 500,
  period_start: new Date()
});

// NPM
await inserter.insert({
  source: 'npm',
  name: 'react',
  score: 95.5,
  mentions: 10000,
  period_start: new Date()
});

// Batch
await inserter.batchInsert([
  { source: 'github', name: 'pytorch', stars: 60000 },
  { source: 'npm', name: 'vue', score: 90 },
]);
*/
