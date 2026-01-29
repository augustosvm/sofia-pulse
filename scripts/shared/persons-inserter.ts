/**
 * Persons Inserter - Unified Version
 *
 * Inserts into the consolidated sofia.persons table.
 *
 * REGRA CRÍTICA: TODAS as pessoas físicas devem estar nesta tabela.
 * Diferenciadas por campo 'type': researcher, author, founder, ceo, etc.
 *
 * Features:
 * - Single unified table (persons)
 * - Deduplication via UNIQUE (normalized_name)
 * - ON CONFLICT handling
 * - Automatic name normalization
 */

import { Pool, PoolClient } from 'pg';

// ============================================================================
// TYPES
// ============================================================================

export type PersonType =
  | 'researcher'   // Pesquisadores de universidades (OpenAlex)
  | 'author'       // Autores de papers (ArXiv, OpenAlex, NIH)
  | 'founder'      // Fundadores de startups
  | 'ceo'          // CEOs de empresas
  | 'investor'     // Investidores
  | 'engineer';    // Engenheiros/desenvolvedores

export interface PersonData {
  // Required fields
  full_name: string;
  type: PersonType;

  // Identificadores
  orcid_id?: string;

  // Métricas acadêmicas
  h_index?: number;
  total_citations?: number;
  total_papers?: number;

  // Dados pessoais
  gender?: 'M' | 'F' | null;
  country?: string;
  city?: string;
  primary_affiliation?: string;  // Universidade/empresa principal

  // Metadata
  data_sources?: string[];       // ['openalex', 'arxiv', 'manual']
  metadata?: Record<string, any>; // Campos específicos por tipo
}

// ============================================================================
// PERSONS INSERTER
// ============================================================================

export class PersonsInserter {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  /**
   * Normalize person name for deduplication
   * LOWER(TRIM(REGEXP_REPLACE(full_name, '[^a-zA-Z0-9 ]', '', 'g')))
   */
  private normalizeName(name: string): string {
    return name
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9 ]/g, '')  // Remove special chars
      .replace(/\s+/g, ' ');        // Collapse multiple spaces
  }

  /**
   * Insert person into unified persons table(UPSERT)
  * Returns the person ID
  */
  async insertPerson(
    person: PersonData,
    client ?: PoolClient
  ): Promise<number> {
    const db = client || this.pool;

    // Validate required fields
    if(!person.full_name || !person.type) {
  throw new Error('Missing required fields: full_name, type');
}

const normalized_name = this.normalizeName(person.full_name);

// Try insert with ON CONFLICT DO UPDATE to ensure we get an ID
// We use a CTE or simple ON CONFLICT RETURNING
const query = `
      INSERT INTO sofia.persons (
        full_name,
        normalized_name,
        type,
        orcid_id,
        h_index,
        total_citations,
        total_papers,
        gender,
        country,
        city,
        primary_affiliation,
        data_sources,
        metadata,
        first_seen,
        last_updated
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW(), NOW())
      ON CONFLICT (normalized_name) DO UPDATE SET
        last_updated = NOW(),
        -- Update simple fields if they are null in DB but present in new data
        orcid_id = COALESCE(sofia.persons.orcid_id, EXCLUDED.orcid_id),
        country = COALESCE(sofia.persons.country, EXCLUDED.country),
        primary_affiliation = COALESCE(sofia.persons.primary_affiliation, EXCLUDED.primary_affiliation)
      RETURNING id
    `;

const result = await db.query(query, [
  person.full_name,
  normalized_name,
  person.type,
  person.orcid_id || null,
  person.h_index || 0,
  person.total_citations || 0,
  person.total_papers || 0,
  person.gender || null,
  person.country || null,
  person.city || null,
  person.primary_affiliation || null,
  person.data_sources || [],
  person.metadata ? JSON.stringify(person.metadata) : null,
]);

return result.rows[0].id;
  }

  /**
   * Batch insert persons (with transaction)
   */
  async batchInsert(persons: PersonData[]): Promise < void> {
  const client = await this.pool.connect();
  try {
    await client.query('BEGIN');
    for(const person of persons) {
      await this.insertPerson(person, client);
    }
      await client.query('COMMIT');
  } catch(error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

  /**
   * Get person ID by name (for creating relationships)
   */
  async getPersonId(full_name: string): Promise < number | null > {
  const normalized_name = this.normalizeName(full_name);

  const query = `
      SELECT id
      FROM sofia.persons
      WHERE normalized_name = $1
      LIMIT 1
    `;

  const result = await this.pool.query(query, [normalized_name]);
  return result.rows.length > 0 ? result.rows[0].id : null;
}

  /**
   * Get statistics by type
   */
  async getStats(): Promise < any[] > {
  const query = `
      SELECT
        type,
        COUNT(*) as total_persons,
        COUNT(CASE WHEN orcid_id IS NOT NULL THEN 1 END) as with_orcid,
        COUNT(CASE WHEN country IS NOT NULL THEN 1 END) as with_country,
        COUNT(CASE WHEN primary_affiliation IS NOT NULL THEN 1 END) as with_affiliation,
        AVG(h_index) as avg_h_index,
        AVG(total_citations) as avg_citations,
        AVG(total_papers) as avg_papers
      FROM sofia.persons
      GROUP BY type
      ORDER BY total_persons DESC;
    `;

  const result = await this.pool.query(query);
  return result.rows;
}

  /**
   * Get recent persons by type
   */
  async getRecentPersons(type ?: PersonType, days: number = 30, limit: number = 100): Promise < any[] > {
  const whereClause = type
    ? `WHERE type = $1 AND first_seen >= CURRENT_DATE - INTERVAL '${days} days'`
    : `WHERE first_seen >= CURRENT_DATE - INTERVAL '${days} days'`;

  const params = type ? [type, limit] : [limit];
  const paramIndex = type ? 2 : 1;

  const query = `
      SELECT
        id,
        full_name,
        type,
        orcid_id,
        h_index,
        total_citations,
        total_papers,
        country,
        primary_affiliation,
        first_seen
      FROM sofia.persons
      ${whereClause}
      ORDER BY first_seen DESC
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
const inserter = new PersonsInserter(pool);

// ArXiv author
await inserter.insertPerson({
  full_name: 'Ashish Vaswani',
  type: 'author',
  data_sources: ['arxiv'],
  primary_affiliation: 'Google Research',
});

// OpenAlex researcher
await inserter.insertPerson({
  full_name: 'Geoffrey Hinton',
  type: 'researcher',
  orcid_id: '0000-0002-5193-6595',
  h_index: 175,
  total_citations: 500000,
  total_papers: 350,
  country: 'Canada',
  primary_affiliation: 'University of Toronto',
  data_sources: ['openalex'],
});

// Startup founder
await inserter.insertPerson({
  full_name: 'Sam Altman',
  type: 'founder',
  country: 'United States',
  primary_affiliation: 'OpenAI',
  data_sources: ['crunchbase'],
  metadata: {
    companies_founded: ['Loopt', 'OpenAI'],
    y_combinator_president: true,
  },
});

// Stats
const stats = await inserter.getStats();
console.log(stats);
// Output:
// [
//   { type: 'researcher', total_persons: 130934, with_orcid: 85000, avg_h_index: 12.5 },
//   { type: 'author', total_persons: 91520, with_orcid: 15000, avg_h_index: 3.2 },
//   { type: 'founder', total_persons: 500, with_orcid: 0, avg_h_index: 0 },
// ]
*/
