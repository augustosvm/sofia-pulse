/**
 * Organizations Inserter - TypeScript
 *
 * Insere organizações na tabela unificada sofia.organizations
 * Suporta múltiplos tipos: AI Companies, NGOs, Universities, Startups, VCs, etc.
 *
 * Features:
 * - Schema unificado para todos os tipos de organizações
 * - Campos específicos por tipo armazenados em JSONB metadata
 * - Deduplicação automática via org_id único
 * - Batch insert com transações
 * - ON CONFLICT para updates automáticos
 */

import { Pool, PoolClient } from 'pg';

// ============================================================================
// TYPES
// ============================================================================

export type OrganizationType =
  | 'ai_company'
  | 'ngo'
  | 'university'
  | 'startup'
  | 'vc_firm'
  | 'research_lab'
  | 'government_agency'
  | 'corporation';

export interface OrganizationData {
  // Required fields
  org_id: string;           // Unique: 'source-identifier' (ex: 'aicompanies-openai')
  name: string;
  type: OrganizationType;
  source: string;           // Collector name (ex: 'ai-companies', 'world-ngos')

  // Common optional fields
  industry?: string;
  location?: string;
  city?: string;
  country?: string;
  country_code?: string;
  founded_date?: string | Date;
  website?: string;
  description?: string;

  // Size/Scale
  employee_count?: number;
  revenue_range?: string;

  // Arrays
  tags?: string[];          // ['AI', 'Healthcare', 'Research']
  sources?: string[];       // ['ai-companies-api', 'crunchbase']

  // Type-specific fields (JSONB)
  metadata?: Record<string, any>;
}

// ============================================================================
// ORGANIZATIONS INSERTER
// ============================================================================

export class OrganizationsInserter {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  /**
   * Insere organização na tabela sofia.organizations
   */
  async insertOrganization(org: OrganizationData, client?: PoolClient): Promise<void> {
    const db = client || this.pool;

    // Validate required fields
    if (!org.org_id || !org.name || !org.type || !org.source) {
      throw new Error('Missing required fields: org_id, name, type, source');
    }

    const query = `
      INSERT INTO sofia.organizations (
        org_id, name, type, source,
        industry, location, city, country, country_code,
        founded_date, website, description,
        employee_count, revenue_range,
        tags, sources, metadata,
        first_seen_at, last_updated_at, collected_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, NOW(), NOW(), NOW())
      ON CONFLICT (org_id)
      DO UPDATE SET
        name = EXCLUDED.name,
        description = COALESCE(EXCLUDED.description, sofia.organizations.description),
        website = COALESCE(EXCLUDED.website, sofia.organizations.website),
        tags = EXCLUDED.tags,
        sources = array_cat(sofia.organizations.sources, EXCLUDED.sources),
        metadata = sofia.organizations.metadata || EXCLUDED.metadata,  -- Merge JSONB
        last_updated_at = NOW(),
        collected_at = NOW()
    `;

    await db.query(query, [
      org.org_id,
      org.name,
      org.type,
      org.source,
      org.industry || null,
      org.location || null,
      org.city || null,
      org.country || null,
      org.country_code || null,
      org.founded_date || null,
      org.website || null,
      org.description || null,
      org.employee_count || null,
      org.revenue_range || null,
      org.tags || null,
      org.sources || [org.source],
      org.metadata ? JSON.stringify(org.metadata) : null,
    ]);
  }

  /**
   * Batch insert de múltiplas organizações (com transação)
   */
  async batchInsert(orgs: OrganizationData[]): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      for (const org of orgs) {
        await this.insertOrganization(org, client);
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
   * Get statistics por tipo
   */
  async getStats(type?: OrganizationType): Promise<any> {
    const whereClause = type ? 'WHERE type = $1' : '';
    const params = type ? [type] : [];

    const query = `
      SELECT
        type,
        COUNT(*) as total,
        COUNT(DISTINCT country) as countries,
        COUNT(CASE WHEN website IS NOT NULL THEN 1 END) as with_website,
        COUNT(CASE WHEN metadata IS NOT NULL THEN 1 END) as with_metadata,
        array_agg(DISTINCT source) as sources
      FROM sofia.organizations
      ${whereClause}
      GROUP BY type
      ORDER BY total DESC;
    `;

    const result = await this.pool.query(query, params);
    return result.rows;
  }

  /**
   * Search organizations por nome ou tags
   */
  async search(query: string, type?: OrganizationType, limit: number = 100): Promise<any[]> {
    const typeFilter = type ? 'AND type = $2' : '';
    const params = type ? [query, type, limit] : [query, limit];

    const sql = `
      SELECT org_id, name, type, country, tags, website, description
      FROM sofia.organizations
      WHERE (
        name ILIKE $1
        OR tags && ARRAY[$1]::text[]
        OR to_tsvector('english', description) @@ plainto_tsquery('english', $1)
      )
      ${typeFilter}
      ORDER BY name
      LIMIT $${params.length};
    `;

    const result = await this.pool.query(sql, params);
    return result.rows;
  }

  /**
   * Get organizations by tags
   */
  async getByTags(tags: string[], type?: OrganizationType, limit: number = 100): Promise<any[]> {
    const typeFilter = type ? 'AND type = $2' : '';
    const params = type ? [tags, type, limit] : [tags, limit];

    const sql = `
      SELECT org_id, name, type, country, tags, website
      FROM sofia.organizations
      WHERE tags && $1::text[]
      ${typeFilter}
      ORDER BY name
      LIMIT $${params.length};
    `;

    const result = await this.pool.query(sql, params);
    return result.rows;
  }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Normaliza tipo de organização
 */
export function normalizeOrgType(type: string): OrganizationType {
  const normalized = type.toLowerCase().replace(/[^a-z]/g, '_');

  const typeMap: Record<string, OrganizationType> = {
    'ai_company': 'ai_company',
    'ai_startup': 'ai_company',
    'tech_company': 'ai_company',
    'ngo': 'ngo',
    'non_profit': 'ngo',
    'nonprofit': 'ngo',
    'university': 'university',
    'college': 'university',
    'startup': 'startup',
    'vc': 'vc_firm',
    'venture_capital': 'vc_firm',
    'research': 'research_lab',
    'lab': 'research_lab',
    'government': 'government_agency',
    'corporation': 'corporation',
    'company': 'corporation',
  };

  return typeMap[normalized] || 'corporation';
}

/**
 * Extrai tags de descrição
 */
export function extractTags(text: string): string[] {
  const keywords = [
    'AI', 'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision',
    'Healthcare', 'Education', 'Finance', 'Climate', 'Energy',
    'Research', 'Innovation', 'Startup', 'Enterprise',
    'Open Source', 'Cloud', 'SaaS', 'Platform',
  ];

  const lowerText = text.toLowerCase();
  const found = keywords.filter(keyword => lowerText.includes(keyword.toLowerCase()));

  return [...new Set(found)]; // Deduplicate
}

// ============================================================================
// EXEMPLO DE USO
// ============================================================================

/*
const inserter = new OrganizationsInserter(pool);

// AI Company
await inserter.insertOrganization({
  org_id: 'aicompanies-openai',
  name: 'OpenAI',
  type: 'ai_company',
  source: 'ai-companies',
  industry: 'Artificial Intelligence',
  location: 'San Francisco, CA',
  country: 'USA',
  website: 'https://openai.com',
  description: 'AI research and deployment company',
  tags: ['AI', 'LLM', 'Research'],
  metadata: {
    github_stars: 50000,
    models: ['GPT-4', 'DALL-E', 'Whisper'],
    papers_count: 100,
    funding_total: 11000000000,
  },
});

// NGO
await inserter.insertOrganization({
  org_id: 'worldngos-redcross',
  name: 'International Red Cross',
  type: 'ngo',
  source: 'world-ngos',
  industry: 'Humanitarian',
  location: 'Geneva',
  country: 'Switzerland',
  website: 'https://icrc.org',
  tags: ['Healthcare', 'Emergency', 'Global'],
  metadata: {
    beneficiaries: 100000000,
    countries_active: 192,
    volunteers: 450000,
  },
});

// Batch insert
await inserter.batchInsert([
  { org_id: '...', name: '...', type: 'university', source: '...', ... },
  { org_id: '...', name: '...', type: 'startup', source: '...', ... },
]);

// Search
const results = await inserter.search('OpenAI', 'ai_company');
const aiOrgs = await inserter.getByTags(['AI', 'Healthcare'], 'ai_company');

// Stats
const stats = await inserter.getStats('ai_company');
*/
