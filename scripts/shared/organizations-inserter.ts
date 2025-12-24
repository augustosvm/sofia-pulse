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
   * ADAPTADO para schema atual: (id, name, normalized_name, type, source_id, metadata, created_at)
   */
  async insertOrganization(org: OrganizationData, client?: PoolClient): Promise<void> {
    const db = client || this.pool;

    // Validate required fields
    if (!org.name || !org.type) {
      throw new Error('Missing required fields: name, type');
    }

    // Normalizar nome para usar como chave única
    const normalizedName = org.org_id || this.normalizeName(org.name);

    // Colocar TODOS os campos extras no metadata
    const fullMetadata = {
      ...(org.metadata || {}),
      org_id: org.org_id,
      source: org.source,
      industry: org.industry,
      location: org.location,
      city: org.city,
      country: org.country,
      country_code: org.country_code,
      founded_date: org.founded_date,
      website: org.website,
      description: org.description,
      employee_count: org.employee_count,
      revenue_range: org.revenue_range,
      tags: org.tags,
      sources: org.sources || [org.source],
    };

    // Remover campos null/undefined
    Object.keys(fullMetadata).forEach(key => {
      if (fullMetadata[key] === null || fullMetadata[key] === undefined) {
        delete fullMetadata[key];
      }
    });

    const query = `
      INSERT INTO sofia.organizations (
        name, normalized_name, type, metadata
      )
      VALUES ($1, $2, $3, $4)
      ON CONFLICT (normalized_name)
      DO UPDATE SET
        name = EXCLUDED.name,
        type = EXCLUDED.type,
        metadata = sofia.organizations.metadata || EXCLUDED.metadata
    `;

    await db.query(query, [
      org.name,
      normalizedName,
      org.type,
      JSON.stringify(fullMetadata),
    ]);
  }

  /**
   * Normaliza nome para usar como chave única
   */
  private normalizeName(name: string): string {
    return name
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '-')
      .replace(/[^a-z0-9-]/g, '');
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
