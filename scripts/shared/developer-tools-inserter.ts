/**
 * Developer Tools Inserter - TypeScript
 *
 * Unified inserter for all developer tools data sources.
 * Inserts into sofia.developer_tools table.
 *
 * Features:
 * - Deduplication via unique constraint (tool_id + platform)
 * - ON CONFLICT handling (updates stats on duplicates)
 * - Batch insert support
 * - Tracks download trends over time
 */

import { Pool, PoolClient } from 'pg';

// ============================================================================
// TYPES
// ============================================================================

export interface DeveloperToolData {
  tool_name: string;
  tool_id: string;
  platform: 'vscode' | 'chrome' | 'jetbrains' | 'npm' | 'pypi';
  category?: string | null;
  downloads?: number | null;
  rating?: number | null;
  rating_count?: number | null;
  version?: string | null;
  publisher?: string | null;
  description?: string | null;
  tags?: string | null;
  homepage_url?: string | null;
  repository_url?: string | null;
  source: string;
  metadata?: Record<string, any>;
}

// ============================================================================
// DEVELOPER TOOLS INSERTER
// ============================================================================

export class DeveloperToolsInserter {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  /**
   * Insert developer tool into database
   */
  async insertDeveloperTool(
    tool: DeveloperToolData,
    client?: PoolClient
  ): Promise<void> {
    const db = client || this.pool;

    // Validate required fields
    if (!tool.tool_name || !tool.tool_id || !tool.platform) {
      throw new Error('Missing required fields: tool_name, tool_id, platform');
    }

    const query = `
      INSERT INTO sofia.developer_tools (
        tool_name,
        tool_id,
        platform,
        category,
        downloads,
        rating,
        rating_count,
        version,
        publisher,
        description,
        tags,
        homepage_url,
        repository_url,
        source,
        collected_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW())
      ON CONFLICT (tool_id, platform)
      DO UPDATE SET
        tool_name = EXCLUDED.tool_name,
        category = COALESCE(EXCLUDED.category, sofia.developer_tools.category),
        downloads = EXCLUDED.downloads,
        rating = EXCLUDED.rating,
        rating_count = EXCLUDED.rating_count,
        version = EXCLUDED.version,
        publisher = COALESCE(EXCLUDED.publisher, sofia.developer_tools.publisher),
        description = COALESCE(EXCLUDED.description, sofia.developer_tools.description),
        tags = COALESCE(EXCLUDED.tags, sofia.developer_tools.tags),
        homepage_url = COALESCE(EXCLUDED.homepage_url, sofia.developer_tools.homepage_url),
        repository_url = COALESCE(EXCLUDED.repository_url, sofia.developer_tools.repository_url),
        source = EXCLUDED.source,
        collected_at = NOW()
    `;

    await db.query(query, [
      tool.tool_name,
      tool.tool_id,
      tool.platform,
      tool.category || null,
      tool.downloads || null,
      tool.rating || null,
      tool.rating_count || null,
      tool.version || null,
      tool.publisher || null,
      tool.description || null,
      tool.tags || null,
      tool.homepage_url || null,
      tool.repository_url || null,
      tool.source || 'unknown',
    ]);
  }

  /**
   * Batch insert developer tools (with transaction)
   */
  async batchInsert(tools: DeveloperToolData[]): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      for (const tool of tools) {
        await this.insertDeveloperTool(tool, client);
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
   * Get statistics
   */
  async getStats(): Promise<any> {
    const query = `
      SELECT
        platform,
        COUNT(*) as total_tools,
        AVG(downloads) as avg_downloads,
        MAX(downloads) as max_downloads,
        AVG(rating) as avg_rating,
        COUNT(CASE WHEN collected_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as last_7_days,
        COUNT(CASE WHEN collected_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_30_days
      FROM sofia.developer_tools
      GROUP BY platform
      ORDER BY total_tools DESC;
    `;

    const result = await this.pool.query(query);
    return result.rows;
  }

  /**
   * Get trending tools (by download growth)
   */
  async getTrendingTools(platform?: string, limit: number = 50): Promise<any[]> {
    const whereClause = platform ? 'WHERE platform = $1' : '';
    const params = platform ? [platform, limit] : [limit];
    const paramIndex = platform ? 2 : 1;

    const query = `
      WITH latest AS (
        SELECT DISTINCT ON (tool_id, platform)
          tool_id,
          platform,
          tool_name,
          downloads,
          rating,
          collected_at
        FROM sofia.developer_tools
        ${whereClause}
        ORDER BY tool_id, platform, collected_at DESC
      ),
      previous AS (
        SELECT DISTINCT ON (tool_id, platform)
          tool_id,
          platform,
          downloads as prev_downloads,
          collected_at as prev_collected_at
        FROM sofia.developer_tools
        WHERE collected_at < CURRENT_DATE - INTERVAL '7 days'
        ${whereClause ? 'AND platform = $1' : ''}
        ORDER BY tool_id, platform, collected_at DESC
      )
      SELECT
        l.tool_name,
        l.platform,
        l.downloads,
        l.rating,
        p.prev_downloads,
        CASE
          WHEN p.prev_downloads > 0 THEN
            ((l.downloads - p.prev_downloads)::float / p.prev_downloads * 100)
          ELSE 0
        END as growth_percentage
      FROM latest l
      LEFT JOIN previous p ON l.tool_id = p.tool_id AND l.platform = p.platform
      ORDER BY growth_percentage DESC NULLS LAST
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
const inserter = new DeveloperToolsInserter(pool);

// Insert single tool
await inserter.insertDeveloperTool({
  tool_name: 'Pylance',
  tool_id: 'ms-python.vscode-pylance',
  platform: 'vscode',
  category: 'Programming Languages',
  downloads: 50000000,
  rating: 4.7,
  rating_count: 1234,
  version: '2023.12.1',
  publisher: 'Microsoft',
  description: 'Python language server',
  tags: 'python, language-server, linting',
  homepage_url: 'https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance',
  source: 'vscode-marketplace',
});

// Batch insert
await inserter.batchInsert([
  { tool_name: 'ESLint', tool_id: 'dbaeumer.vscode-eslint', platform: 'vscode', downloads: 40000000, source: 'vscode-marketplace' },
  { tool_name: 'Prettier', tool_id: 'esbenp.prettier-vscode', platform: 'vscode', downloads: 35000000, source: 'vscode-marketplace' },
]);

// Get stats
const stats = await inserter.getStats();
console.log(stats);

// Get trending
const trending = await inserter.getTrendingTools('vscode', 20);
console.log(trending);
*/
