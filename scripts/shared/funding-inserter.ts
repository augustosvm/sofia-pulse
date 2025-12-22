/**
 * Funding Rounds Inserter - TypeScript
 *
 * Unified inserter for all funding data sources.
 * Inserts into sofia.funding_rounds table.
 *
 * Features:
 * - Deduplication via unique constraint
 * - ON CONFLICT handling
 * - Batch insert support
 * - Geographic normalization (country_id, city_id)
 */

import { Pool, PoolClient } from 'pg';

// ============================================================================
// TYPES
// ============================================================================

export interface FundingRoundData {
  company_name: string;
  round_type?: string | null;
  sector?: string | null;
  amount_usd?: number | null;
  valuation_usd?: number | null;
  announced_date?: Date | string | null;
  country?: string | null;
  city?: string | null;
  country_id?: number | null;
  city_id?: number | null;
  state_id?: number | null;
  website?: string | null;
  description?: string | null;
  investors?: string[] | string | null;
  funding_stage?: string | null;
  source?: string;
  metadata?: Record<string, any>;
}

// ============================================================================
// FUNDING INSERTER
// ============================================================================

export class FundingInserter {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  /**
   * Insert funding round into database
   */
  async insertFundingRound(
    round: FundingRoundData,
    client?: PoolClient
  ): Promise<void> {
    const db = client || this.pool;

    // Validate required fields
    if (!round.company_name) {
      throw new Error('Missing required field: company_name');
    }

    // Prepare investors (array or string)
    let investorsArray: string[] | null = null;
    if (Array.isArray(round.investors)) {
      investorsArray = round.investors;
    } else if (round.investors) {
      investorsArray = [round.investors];
    }

    // Prepare announced_date
    let announcedDate: Date | null = null;
    if (round.announced_date) {
      announcedDate = typeof round.announced_date === 'string'
        ? new Date(round.announced_date)
        : round.announced_date;
    }

    const query = `
      INSERT INTO sofia.funding_rounds (
        company_name,
        round_type,
        sector,
        amount_usd,
        valuation_usd,
        announced_date,
        country,
        country_id,
        city,
        city_id,
        investors,
        source,
        collected_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW())
      ON CONFLICT (company_name, round_type, announced_date)
      DO UPDATE SET
        sector = COALESCE(EXCLUDED.sector, sofia.funding_rounds.sector),
        amount_usd = COALESCE(EXCLUDED.amount_usd, sofia.funding_rounds.amount_usd),
        valuation_usd = COALESCE(EXCLUDED.valuation_usd, sofia.funding_rounds.valuation_usd),
        country = COALESCE(EXCLUDED.country, sofia.funding_rounds.country),
        country_id = COALESCE(EXCLUDED.country_id, sofia.funding_rounds.country_id),
        city = COALESCE(EXCLUDED.city, sofia.funding_rounds.city),
        city_id = COALESCE(EXCLUDED.city_id, sofia.funding_rounds.city_id),
        investors = COALESCE(EXCLUDED.investors, sofia.funding_rounds.investors),
        source = EXCLUDED.source,
        collected_at = NOW()
    `;

    await db.query(query, [
      round.company_name,
      round.round_type || null,
      round.sector || null,
      round.amount_usd || null,
      round.valuation_usd || null,
      announcedDate,
      round.country || null,
      round.country_id || null,
      round.city || null,
      round.city_id || null,
      investorsArray,
      round.source || 'unknown',
    ]);
  }

  /**
   * Batch insert funding rounds (with transaction)
   */
  async batchInsert(rounds: FundingRoundData[]): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      for (const round of rounds) {
        await this.insertFundingRound(round, client);
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
        COUNT(*) as total_rounds,
        COUNT(DISTINCT company_name) as unique_companies,
        SUM(amount_usd) as total_funding,
        AVG(amount_usd) as avg_funding,
        COUNT(CASE WHEN announced_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_30_days,
        COUNT(CASE WHEN announced_date >= CURRENT_DATE - INTERVAL '90 days' THEN 1 END) as last_90_days
      FROM sofia.funding_rounds;
    `;

    const result = await this.pool.query(query);
    return result.rows[0];
  }
}

// ============================================================================
// EXAMPLE USAGE
// ============================================================================

/*
const inserter = new FundingInserter(pool);

// Insert single round
await inserter.insertFundingRound({
  company_name: 'OpenAI',
  round_type: 'Series C',
  sector: 'Artificial Intelligence',
  amount_usd: 10000000000,
  announced_date: new Date('2023-01-23'),
  country: 'USA',
  investors: ['Microsoft', 'Khosla Ventures'],
});

// Batch insert
await inserter.batchInsert([
  { company_name: 'Anthropic', round_type: 'Series B', amount_usd: 450000000, country: 'USA' },
  { company_name: 'Mistral AI', round_type: 'Series A', amount_usd: 113000000, country: 'France' },
]);

// Get stats
const stats = await inserter.getStats();
console.log(stats);
*/
