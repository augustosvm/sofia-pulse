
import { Pool, PoolClient } from 'pg';

export interface SignalData {
    source: string;
    external_id: string;
    title: string;
    summary: string | null;
    url: string | null;
    category: string;
    signal_type: string;
    impact_score: number | null;
    sentiment_score: number | null;
    metadata: Record<string, any>;
    published_at: Date;
}

export class IndustrySignalsInserter {
    private pool: Pool;

    constructor(pool: Pool) {
        this.pool = pool;
    }

    async insertSignal(signal: SignalData, client?: PoolClient): Promise<void> {
        const db = client || this.pool;

        const query = `
      INSERT INTO sofia.industry_signals (
        source, external_id, title, summary, url,
        category, signal_type, impact_score, sentiment_score,
        metadata, published_at, collected_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
      ON CONFLICT (source, external_id) DO UPDATE SET
        title = EXCLUDED.title,
        summary = EXCLUDED.summary,
        impact_score = EXCLUDED.impact_score,
        sentiment_score = EXCLUDED.sentiment_score,
        metadata = EXCLUDED.metadata,
        collected_at = NOW()
    `;

        await db.query(query, [
            signal.source,
            signal.external_id,
            signal.title,
            signal.summary,
            signal.url,
            signal.category,
            signal.signal_type,
            signal.impact_score,
            signal.sentiment_score,
            JSON.stringify(signal.metadata || {}),
            signal.published_at
        ]);
    }

    async batchInsert(signals: SignalData[]): Promise<void> {
        if (signals.length === 0) return;

        const client = await this.pool.connect();
        try {
            await client.query('BEGIN');
            for (const signal of signals) {
                await this.insertSignal(signal, client);
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
