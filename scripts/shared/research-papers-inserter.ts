/**
 * Research Papers Inserter - Unified Version
 *
 * Inserts into the consolidated sofia.research_papers table.
 * Replaces: papers-inserter.ts (old, used arxiv_ai_papers, openalex_papers, bdtd_theses)
 *
 * Features:
 * - Single unified table (research_papers)
 * - Deduplication via UNIQUE (source, source_id)
 * - Supports all paper sources: arxiv, openalex, bdtd
 * - ON CONFLICT handling
 * - AUTO-INSERT AUTHORS into sofia.persons (with PersonsInserter)
 */

import { Pool, PoolClient } from 'pg';
import { PersonsInserter } from './persons-inserter';

// ============================================================================
// TYPES
// ============================================================================

export interface ResearchPaperData {
  // Required fields
  title: string;
  source: 'arxiv' | 'openalex' | 'bdtd';
  source_id: string; // arxiv_id, openalex_id, thesis_id

  // Common fields
  abstract?: string;
  authors?: string[]; // Array of author names
  keywords?: string[]; // Array of keywords/concepts
  publication_date?: Date | string;
  publication_year?: number;

  // Source-specific IDs
  doi?: string;

  // Categories and classification
  primary_category?: string;
  categories?: string[]; // Array of categories/concepts
  area?: string[]; // Research area (for theses)

  // URLs and access
  pdf_url?: string;
  journal?: string;
  publisher?: string;
  is_open_access?: boolean;

  // Academic metadata (for theses)
  university?: string;
  program?: string;
  degree_type?: string;
  language?: string;

  // Author details
  author_institutions?: string[];
  author_countries?: string[];

  // Impact metrics
  cited_by_count?: number;
  referenced_works_count?: number;
  is_breakthrough?: boolean;
}

// ============================================================================
// RESEARCH PAPERS INSERTER
// ============================================================================

export class ResearchPapersInserter {
  private pool: Pool;
  private personsInserter: PersonsInserter;
  private insertAuthors: boolean;

  constructor(pool: Pool, options?: { insertAuthors?: boolean }) {
    this.pool = pool;
    this.personsInserter = new PersonsInserter(pool);
    this.insertAuthors = options?.insertAuthors !== false; // Default: true
  }

  /**
   * Insert research paper into unified research_papers table
   * Also inserts authors into sofia.persons if insertAuthors is enabled
   */
  async insertPaper(
    paper: ResearchPaperData,
    client?: PoolClient
  ): Promise<void> {
    const db = client || this.pool;

    // Validate required fields
    if (!paper.title || !paper.source || !paper.source_id) {
      throw new Error('Missing required fields: title, source, source_id');
    }

    // Prepare publication_date
    let publicationDate: Date | null = null;
    if (paper.publication_date) {
      publicationDate = typeof paper.publication_date === 'string'
        ? new Date(paper.publication_date)
        : paper.publication_date;
    }

    // INSERT AUTHORS into sofia.persons FIRST (if enabled)
    if (this.insertAuthors && paper.authors && paper.authors.length > 0) {
      for (const authorName of paper.authors) {
        if (!authorName || authorName === 'Unknown') continue;

        try {
          await this.personsInserter.insertPerson({
            full_name: authorName,
            type: 'author',
            data_sources: [paper.source],
            country: paper.author_countries?.[0],  // First country if available
            primary_affiliation: paper.author_institutions?.[0],  // First institution
          }, client);
        } catch (error) {
          console.error(`Failed to insert author ${authorName}:`, error);
          // Continue even if author insert fails
        }
      }
    }

    const query = `
      INSERT INTO sofia.research_papers (
        title,
        abstract,
        authors,
        keywords,
        publication_date,
        publication_year,
        source,
        source_id,
        doi,
        primary_category,
        categories,
        area,
        pdf_url,
        journal,
        publisher,
        is_open_access,
        university,
        program,
        degree_type,
        language,
        author_institutions,
        author_countries,
        cited_by_count,
        referenced_works_count,
        is_breakthrough,
        collected_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, NOW())
      ON CONFLICT (source, source_id)
      DO UPDATE SET
        title = EXCLUDED.title,
        abstract = COALESCE(EXCLUDED.abstract, sofia.research_papers.abstract),
        keywords = COALESCE(EXCLUDED.keywords, sofia.research_papers.keywords),
        publication_date = COALESCE(EXCLUDED.publication_date, sofia.research_papers.publication_date),
        publication_year = COALESCE(EXCLUDED.publication_year, sofia.research_papers.publication_year),
        cited_by_count = EXCLUDED.cited_by_count,
        referenced_works_count = EXCLUDED.referenced_works_count,
        is_breakthrough = COALESCE(EXCLUDED.is_breakthrough, sofia.research_papers.is_breakthrough),
        is_open_access = COALESCE(EXCLUDED.is_open_access, sofia.research_papers.is_open_access),
        collected_at = NOW(),
        updated_at = NOW()
    `;

    await db.query(query, [
      paper.title,
      paper.abstract || null,
      paper.authors || null,
      paper.keywords || null,
      publicationDate,
      paper.publication_year || (publicationDate ? publicationDate.getFullYear() : null),
      paper.source,
      paper.source_id,
      paper.doi || null,
      paper.primary_category || null,
      paper.categories || null,
      paper.area || null,
      paper.pdf_url || null,
      paper.journal || null,
      paper.publisher || null,
      paper.is_open_access !== undefined ? paper.is_open_access : false,
      paper.university || null,
      paper.program || null,
      paper.degree_type || null,
      paper.language || null,
      paper.author_institutions || null,
      paper.author_countries || null,
      paper.cited_by_count || 0,
      paper.referenced_works_count || 0,
      paper.is_breakthrough !== undefined ? paper.is_breakthrough : false,
    ]);
  }

  /**
   * Batch insert papers (with transaction)
   */
  async batchInsert(papers: ResearchPaperData[]): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      for (const paper of papers) {
        await this.insertPaper(paper, client);
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
   * Get statistics by source
   */
  async getStats(): Promise<any[]> {
    const query = `
      SELECT
        source,
        COUNT(*) as total_papers,
        COUNT(CASE WHEN publication_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_30_days,
        COUNT(CASE WHEN publication_date >= CURRENT_DATE - INTERVAL '90 days' THEN 1 END) as last_90_days,
        COUNT(CASE WHEN is_breakthrough THEN 1 END) as breakthrough_count,
        AVG(cited_by_count) as avg_citations,
        MAX(publication_date) as latest_paper
      FROM sofia.research_papers
      GROUP BY source
      ORDER BY total_papers DESC;
    `;

    const result = await this.pool.query(query);
    return result.rows;
  }

  /**
   * Get recent papers by source
   */
  async getRecentPapers(source?: string, days: number = 30, limit: number = 100): Promise<any[]> {
    const whereClause = source
      ? `WHERE source = $1 AND publication_date >= CURRENT_DATE - INTERVAL '${days} days'`
      : `WHERE publication_date >= CURRENT_DATE - INTERVAL '${days} days'`;

    const params = source ? [source, limit] : [limit];
    const paramIndex = source ? 2 : 1;

    const query = `
      SELECT
        source,
        source_id,
        title,
        authors,
        publication_date,
        primary_category,
        cited_by_count,
        is_breakthrough
      FROM sofia.research_papers
      ${whereClause}
      ORDER BY publication_date DESC
      LIMIT $${paramIndex};
    `;

    const result = await this.pool.query(query, params);
    return result.rows;
  }
}

// ============================================================================
// EXAMPLE USAGE
// ============================================================================

/*
const inserter = new ResearchPapersInserter(pool);

// ArXiv paper
await inserter.insertPaper({
  title: 'Attention Is All You Need',
  source: 'arxiv',
  source_id: '1706.03762',
  authors: ['Vaswani', 'Shazeer', 'Parmar'],
  abstract: 'The dominant sequence transduction models...',
  publication_date: '2017-06-12',
  primary_category: 'cs.CL',
  categories: ['cs.CL', 'cs.LG'],
  is_breakthrough: true,
  pdf_url: 'https://arxiv.org/pdf/1706.03762',
});

// OpenAlex paper
await inserter.insertPaper({
  title: 'BERT: Pre-training of Deep Bidirectional Transformers',
  source: 'openalex',
  source_id: 'W2964280417',
  doi: '10.18653/v1/N19-1423',
  authors: ['Devlin', 'Chang', 'Lee', 'Toutanova'],
  publication_date: '2019-06-02',
  publication_year: 2019,
  cited_by_count: 50000,
  is_open_access: true,
  journal: 'NAACL-HLT',
});

// Stats
const stats = await inserter.getStats();
console.log(stats);
*/
