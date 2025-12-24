/**
 * Papers Inserter - TypeScript
 *
 * Insere research papers em múltiplas tables especializadas:
 * - arxiv_ai_papers (ArXiv AI/ML papers)
 * - openalex_papers (OpenAlex research papers)
 * - nih_grants (NIH grants - futuro)
 *
 * Usa inserção dinâmica baseada no tipo de paper.
 */

import { Pool, PoolClient } from 'pg';

// ============================================================================
// TYPES
// ============================================================================

export interface ArxivPaperData {
  arxiv_id: string;
  title: string;
  authors: string[];
  categories: string[];
  abstract: string;
  published_date: string;
  updated_date?: string;
  pdf_url: string;
  primary_category: string;
  keywords?: string[];
  is_breakthrough?: boolean;
}

export interface OpenAlexPaperData {
  openalex_id: string;
  doi?: string;
  title: string;
  publication_date: string;
  publication_year: number;
  authors: string[];
  author_institutions?: string[];
  author_countries?: string[];
  concepts: string[];
  primary_concept: string;
  cited_by_count: number;
  referenced_works_count: number;
  is_open_access: boolean;
  journal?: string;
  publisher?: string;
  abstract?: string;
}

export interface NIHGrantData {
  grant_id: string;
  title: string;
  investigators: string[];
  institution: string;
  award_amount?: number;
  fiscal_year: number;
  start_date?: string;
  end_date?: string;
  abstract?: string;
}

export type PaperData = ArxivPaperData | OpenAlexPaperData | NIHGrantData;

// ============================================================================
// PAPERS INSERTER
// ============================================================================

export class PapersInserter {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  /**
   * Insere ArXiv AI paper
   */
  async insertArxivPaper(paper: ArxivPaperData, client?: PoolClient): Promise<void> {
    const db = client || this.pool;

    const query = `
      INSERT INTO arxiv_ai_papers (
        arxiv_id, title, authors, categories, abstract,
        published_date, updated_date, pdf_url,
        primary_category, keywords, is_breakthrough
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
      ON CONFLICT (arxiv_id)
      DO UPDATE SET
        updated_date = EXCLUDED.updated_date,
        collected_at = NOW()
    `;

    await db.query(query, [
      paper.arxiv_id,
      paper.title,
      paper.authors,
      paper.categories,
      paper.abstract,
      paper.published_date,
      paper.updated_date || null,
      paper.pdf_url,
      paper.primary_category,
      paper.keywords || [],
      paper.is_breakthrough || false,
    ]);
  }

  /**
   * Insere OpenAlex paper
   */
  async insertOpenAlexPaper(paper: OpenAlexPaperData, client?: PoolClient): Promise<void> {
    const db = client || this.pool;

    const query = `
      INSERT INTO openalex_papers (
        openalex_id, doi, title, publication_date, publication_year,
        authors, author_institutions, author_countries,
        concepts, primary_concept, cited_by_count, referenced_works_count,
        is_open_access, journal, publisher, abstract
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
      ON CONFLICT (openalex_id)
      DO UPDATE SET
        cited_by_count = EXCLUDED.cited_by_count,
        collected_at = NOW()
    `;

    await db.query(query, [
      paper.openalex_id,
      paper.doi || null,
      paper.title,
      paper.publication_date,
      paper.publication_year,
      paper.authors,
      paper.author_institutions || null,
      paper.author_countries || null,
      paper.concepts,
      paper.primary_concept,
      paper.cited_by_count,
      paper.referenced_works_count,
      paper.is_open_access,
      paper.journal || null,
      paper.publisher || null,
      paper.abstract || null,
    ]);
  }

  /**
   * Insere NIH grant (futuro)
   */
  async insertNIHGrant(grant: NIHGrantData, client?: PoolClient): Promise<void> {
    const db = client || this.pool;

    const query = `
      INSERT INTO nih_grants (
        grant_id, title, investigators, institution,
        award_amount, fiscal_year, start_date, end_date, abstract
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
      ON CONFLICT (grant_id)
      DO UPDATE SET
        award_amount = EXCLUDED.award_amount,
        collected_at = NOW()
    `;

    await db.query(query, [
      grant.grant_id,
      grant.title,
      grant.investigators,
      grant.institution,
      grant.award_amount || null,
      grant.fiscal_year,
      grant.start_date || null,
      grant.end_date || null,
      grant.abstract || null,
    ]);
  }

  /**
   * Insert genérico - detecta tipo automaticamente baseado nos campos
   */
  async insert(paper: any, table?: string): Promise<void> {
    // Se table foi especificada, usa ela
    if (table) {
      switch (table) {
        case 'arxiv_ai_papers':
          return this.insertArxivPaper(paper as ArxivPaperData);
        case 'openalex_papers':
          return this.insertOpenAlexPaper(paper as OpenAlexPaperData);
        case 'nih_grants':
          return this.insertNIHGrant(paper as NIHGrantData);
        default:
          throw new Error(`Unknown table: ${table}`);
      }
    }

    // Detecta automaticamente baseado nos campos
    if ('arxiv_id' in paper) {
      return this.insertArxivPaper(paper as ArxivPaperData);
    } else if ('openalex_id' in paper) {
      return this.insertOpenAlexPaper(paper as OpenAlexPaperData);
    } else if ('grant_id' in paper) {
      return this.insertNIHGrant(paper as NIHGrantData);
    } else {
      throw new Error('Cannot detect paper type - missing ID field');
    }
  }

  /**
   * Batch insert de múltiplos papers (com transação)
   */
  async batchInsert(papers: any[], table?: string): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      for (const paper of papers) {
        await this.insert(paper, table);
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
   * Batch insert específico para ArXiv
   */
  async batchInsertArxiv(papers: ArxivPaperData[]): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      for (const paper of papers) {
        await this.insertArxivPaper(paper, client);
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
   * Batch insert específico para OpenAlex
   */
  async batchInsertOpenAlex(papers: OpenAlexPaperData[]): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      for (const paper of papers) {
        await this.insertOpenAlexPaper(paper, client);
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
   * Batch insert específico para NIH
   */
  async batchInsertNIH(grants: NIHGrantData[]): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      for (const grant of grants) {
        await this.insertNIHGrant(grant, client);
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
// EXEMPLO DE USO
// ============================================================================

/*
const inserter = new PapersInserter(pool);

// ArXiv Paper
await inserter.insertArxivPaper({
  arxiv_id: '2024.11234',
  title: 'Attention Is All You Need',
  authors: ['Vaswani Ashish', 'Shazeer Noam'],
  categories: ['cs.AI', 'cs.LG'],
  abstract: 'The dominant sequence transduction models...',
  published_date: '2024-06-15',
  pdf_url: 'https://arxiv.org/pdf/2024.11234.pdf',
  primary_category: 'cs.AI',
  keywords: ['LLM', 'Transformers'],
  is_breakthrough: true,
});

// OpenAlex Paper
await inserter.insertOpenAlexPaper({
  openalex_id: 'W4385820562',
  doi: '10.1038/s41586-024-07234-5',
  title: 'AlphaFold: Protein Structure Prediction',
  publication_date: '2024-05-20',
  publication_year: 2024,
  authors: ['Jumper John', 'Hassabis Demis'],
  author_institutions: ['DeepMind', 'Google'],
  author_countries: ['UK', 'USA'],
  concepts: ['Protein Folding', 'Deep Learning'],
  primary_concept: 'Protein Folding',
  cited_by_count: 12845,
  referenced_works_count: 125,
  is_open_access: false,
  journal: 'Nature',
  publisher: 'Springer Nature',
});

// Batch insert
await inserter.batchInsertArxiv([
  { arxiv_id: '2024.001', title: 'Paper 1', ... },
  { arxiv_id: '2024.002', title: 'Paper 2', ... },
]);

// Auto-detect
await inserter.insert({
  arxiv_id: '2024.003',
  title: 'Auto-detected ArXiv paper',
  ...
});
*/
