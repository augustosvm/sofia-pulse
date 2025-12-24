/**
 * Consolidated Tables Helper
 * 
 * Centraliza INSERTs para tabelas consolidadas:
 * - tech_trends (github, stackoverflow, npm, pypi)
 * - community_posts (hackernews, reddit, producthunt)
 * - patents (epo, wipo, uspto)
 */

import { Pool, PoolClient } from 'pg';

// ============================================================================
// TYPES
// ============================================================================

export interface TechTrend {
    source: 'github' | 'stackoverflow' | 'npm' | 'pypi';
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

export interface CommunityPost {
    source: 'hackernews' | 'reddit' | 'producthunt' | 'devto';
    external_id: string;
    title: string;
    url?: string;
    content?: string;
    author?: string;
    score?: number;
    comments_count?: number;
    upvotes?: number;
    category?: string;
    tags?: string[];
    posted_at?: Date;
    metadata?: Record<string, any>;
}

export interface Patent {
    source: 'epo' | 'wipo' | 'uspto';
    patent_number: string;
    title?: string;
    abstract?: string;
    applicant?: string;
    inventor?: string;
    ipc_classification?: string[];
    technology_field?: string;
    country_id?: number;
    applicant_country?: string;
    filing_date?: Date;
    publication_date?: Date;
    grant_date?: Date;
    metadata?: Record<string, any>;
}

// ============================================================================
// CONSOLIDATED TABLES HELPER CLASS
// ============================================================================

export class ConsolidatedTablesHelper {
    private pool: Pool;

    constructor(pool: Pool) {
        this.pool = pool;
    }

    /**
     * Insert/Update tech trend
     */
    async insertTechTrend(trend: TechTrend, client?: PoolClient): Promise<void> {
        const db = client || this.pool;

        const query = `
      INSERT INTO sofia.tech_trends (
        source, name, category, trend_type,
        score, rank, stars, forks, views, mentions, growth_rate,
        period_start, period_end, metadata
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
      ON CONFLICT (source, name, period_start) DO UPDATE SET
        score = EXCLUDED.score,
        rank = EXCLUDED.rank,
        stars = EXCLUDED.stars,
        forks = EXCLUDED.forks,
        views = EXCLUDED.views,
        mentions = EXCLUDED.mentions,
        growth_rate = EXCLUDED.growth_rate,
        metadata = EXCLUDED.metadata,
        collected_at = NOW()
    `;

        await db.query(query, [
            trend.source,
            trend.name,
            trend.category,
            trend.trend_type,
            trend.score,
            trend.rank,
            trend.stars,
            trend.forks,
            trend.views,
            trend.mentions,
            trend.growth_rate,
            trend.period_start,
            trend.period_end,
            trend.metadata ? JSON.stringify(trend.metadata) : null,
        ]);
    }

    /**
     * Insert/Update community post
     */
    async insertCommunityPost(post: CommunityPost, client?: PoolClient): Promise<void> {
        const db = client || this.pool;

        const query = `
      INSERT INTO sofia.community_posts (
        source, external_id, title, url, content,
        author, score, comments_count, upvotes,
        category, tags, posted_at, metadata
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
      ON CONFLICT (source, external_id) DO UPDATE SET
        title = EXCLUDED.title,
        score = EXCLUDED.score,
        comments_count = EXCLUDED.comments_count,
        upvotes = EXCLUDED.upvotes,
        metadata = EXCLUDED.metadata,
        collected_at = NOW()
    `;

        await db.query(query, [
            post.source,
            post.external_id,
            post.title,
            post.url,
            post.content,
            post.author,
            post.score,
            post.comments_count,
            post.upvotes,
            post.category,
            post.tags ? JSON.stringify(post.tags) : null,
            post.posted_at,
            post.metadata ? JSON.stringify(post.metadata) : null,
        ]);
    }

    /**
     * Insert/Update patent
     */
    async insertPatent(patent: Patent, client?: PoolClient): Promise<void> {
        const db = client || this.pool;

        const query = `
      INSERT INTO sofia.patents (
        source, patent_number, title, abstract,
        applicant, inventor,
        ipc_classification, technology_field,
        country_id, applicant_country,
        filing_date, publication_date, grant_date,
        metadata
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
      ON CONFLICT (source, patent_number) DO UPDATE SET
        title = EXCLUDED.title,
        abstract = EXCLUDED.abstract,
        metadata = EXCLUDED.metadata,
        collected_at = NOW()
    `;

        await db.query(query, [
            patent.source,
            patent.patent_number,
            patent.title,
            patent.abstract,
            patent.applicant,
            patent.inventor,
            patent.ipc_classification,
            patent.technology_field,
            patent.country_id,
            patent.applicant_country,
            patent.filing_date,
            patent.publication_date,
            patent.grant_date,
            patent.metadata ? JSON.stringify(patent.metadata) : null,
        ]);
    }

    /**
     * Batch insert tech trends
     */
    async batchInsertTechTrends(trends: TechTrend[]): Promise<void> {
        const client = await this.pool.connect();
        try {
            await client.query('BEGIN');
            for (const trend of trends) {
                await this.insertTechTrend(trend, client);
            }
            await client.query('COMMIT');
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * Batch insert community posts
     */
    async batchInsertCommunityPosts(posts: CommunityPost[]): Promise<void> {
        const client = await this.pool.connect();
        try {
            await client.query('BEGIN');
            for (const post of posts) {
                await this.insertCommunityPost(post, client);
            }
            await client.query('COMMIT');
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * Batch insert patents
     */
    async batchInsertPatents(patents: Patent[]): Promise<void> {
        const client = await this.pool.connect();
        try {
            await client.query('BEGIN');
            for (const patent of patents) {
                await this.insertPatent(patent, client);
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

// ============================================================================
// CONVENIENCE FUNCTIONS
// ============================================================================

/**
 * Create helper instance
 */
export function createConsolidatedTablesHelper(pool: Pool): ConsolidatedTablesHelper {
    return new ConsolidatedTablesHelper(pool);
}
