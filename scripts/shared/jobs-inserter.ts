/**
 * Jobs Inserter - TypeScript
 *
 * Insere vagas de emprego na tabela unificada sofia.jobs
 * Suporta múltiplas plataformas: LinkedIn, RemoteOK, Himalayas, etc.
 *
 * Normalização automática de:
 * - Localização (país, cidade, remote)
 * - Salário (conversão para USD, normalização de períodos)
 * - Skills (extração de keywords)
 * - Employment type (full-time, part-time, contract, etc.)
 */

import { Pool, PoolClient } from 'pg';

// ============================================================================
// TYPES
// ============================================================================

export interface JobData {
  // Required fields
  job_id: string;           // Unique ID (ex: 'linkedin-12345', 'remoteok-xyz')
  platform: string;         // Source platform (linkedin, remoteok, himalayas, etc.)
  title: string;
  company: string;

  // Location fields
  location?: string;        // Full location string (ex: 'San Francisco, CA, USA')
  city?: string;
  country?: string;
  country_id?: number;
  city_id?: number;
  remote_type?: 'remote' | 'hybrid' | 'onsite';

  // Job details
  description?: string;
  url?: string;
  posted_date?: string | Date;

  // Salary fields
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;  // USD, EUR, BRL, etc.
  salary_period?: 'yearly' | 'monthly' | 'hourly';

  // Additional fields
  employment_type?: string;  // full-time, part-time, contract, internship
  skills_required?: string[];
  search_keyword?: string;   // Which keyword was used to find this job
}

// ============================================================================
// JOBS INSERTER
// ============================================================================

export class JobsInserter {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  /**
   * Insere job na tabela sofia.jobs
   */
  async insertJob(job: JobData, client?: PoolClient): Promise<void> {
    const db = client || this.pool;

    // Validate required fields
    if (!job.job_id || !job.platform || !job.title || !job.company) {
      throw new Error('Missing required fields: job_id, platform, title, company');
    }

    const query = `
      INSERT INTO sofia.jobs (
        job_id, platform, title, company,
        location, city, country, country_id, city_id, remote_type,
        description, url, posted_date,
        salary_min, salary_max, salary_currency, salary_period,
        employment_type, skills_required, search_keyword,
        collected_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, NOW())
      ON CONFLICT (job_id, platform)
      DO UPDATE SET
        title = EXCLUDED.title,
        company = EXCLUDED.company,
        location = EXCLUDED.location,
        description = EXCLUDED.description,
        salary_min = COALESCE(EXCLUDED.salary_min, sofia.jobs.salary_min),
        salary_max = COALESCE(EXCLUDED.salary_max, sofia.jobs.salary_max),
        collected_at = NOW()
    `;

    await db.query(query, [
      job.job_id,
      job.platform,
      job.title,
      job.company,
      job.location || null,
      job.city || null,
      job.country || null,
      job.country_id || null,
      job.city_id || null,
      job.remote_type || null,
      job.description || null,
      job.url || null,
      job.posted_date || null,
      job.salary_min || null,
      job.salary_max || null,
      job.salary_currency || null,
      job.salary_period || null,
      job.employment_type || null,
      job.skills_required || null,
      job.search_keyword || null,
    ]);
  }

  /**
   * Batch insert de múltiplos jobs (com transação)
   */
  async batchInsert(jobs: JobData[]): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      for (const job of jobs) {
        await this.insertJob(job, client);
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
   * Get statistics for a platform
   */
  async getStats(platform?: string): Promise<any> {
    const whereClause = platform ? 'WHERE platform = $1' : '';
    const params = platform ? [platform] : [];

    const query = `
      SELECT
        COUNT(*) as total_jobs,
        COUNT(DISTINCT company) as total_companies,
        COUNT(CASE WHEN remote_type = 'remote' THEN 1 END) as remote_jobs,
        COUNT(CASE WHEN salary_min IS NOT NULL THEN 1 END) as jobs_with_salary,
        ROUND(AVG(salary_min)) as avg_min_salary,
        ROUND(AVG(salary_max)) as avg_max_salary,
        COUNT(CASE WHEN posted_date > NOW() - INTERVAL '7 days' THEN 1 END) as jobs_last_week,
        COUNT(CASE WHEN posted_date > NOW() - INTERVAL '30 days' THEN 1 END) as jobs_last_month
      FROM sofia.jobs
      ${whereClause}
    `;

    const result = await this.pool.query(query, params);
    return result.rows[0];
  }

  /**
   * Normalize location string into city, country components
   * Example: "San Francisco, CA, USA" -> { city: "San Francisco", country: "USA" }
   */
  static normalizeLocation(locationStr: string): { city?: string; country?: string } {
    if (!locationStr) return {};

    const parts = locationStr.split(',').map(s => s.trim()).filter(s => s.length > 0);

    if (parts.length === 0) return {};
    if (parts.length === 1) return { country: parts[0] };
    if (parts.length === 2) return { city: parts[0], country: parts[1] };

    // 3+ parts: first is city, last is country
    return {
      city: parts[0],
      country: parts[parts.length - 1],
    };
  }

  /**
   * Detect remote type from location or title
   */
  static detectRemoteType(location?: string, title?: string): 'remote' | 'hybrid' | 'onsite' {
    const text = `${location} ${title}`.toLowerCase();

    if (text.match(/\b(remote|anywhere|worldwide|work from home|wfh)\b/)) {
      return 'remote';
    }

    if (text.match(/\b(hybrid|flexible|remote-friendly)\b/)) {
      return 'hybrid';
    }

    return 'onsite';
  }

  /**
   * Normalize salary period
   */
  static normalizeSalaryPeriod(period?: string): 'yearly' | 'monthly' | 'hourly' | undefined {
    if (!period) return undefined;

    const p = period.toLowerCase();

    if (p.match(/year|annual|yr|pa/)) return 'yearly';
    if (p.match(/month|mo/)) return 'monthly';
    if (p.match(/hour|hr/)) return 'hourly';

    return undefined;
  }

  /**
   * Extract skills from description/title
   */
  static extractSkills(text: string): string[] {
    const skillsKeywords = [
      'javascript', 'typescript', 'python', 'java', 'go', 'rust', 'c++', 'ruby',
      'react', 'vue', 'angular', 'node.js', 'django', 'flask', 'spring',
      'aws', 'gcp', 'azure', 'docker', 'kubernetes', 'terraform',
      'sql', 'postgresql', 'mysql', 'mongodb', 'redis',
      'machine learning', 'deep learning', 'ai', 'nlp', 'computer vision',
      'devops', 'ci/cd', 'git', 'jenkins', 'github actions',
    ];

    const lowerText = text.toLowerCase();
    const found = skillsKeywords.filter(skill => lowerText.includes(skill));

    return [...new Set(found)]; // Deduplicate
  }
}

// ============================================================================
// EXEMPLO DE USO
// ============================================================================

/*
const inserter = new JobsInserter(pool);

// Single job
await inserter.insertJob({
  job_id: 'linkedin-12345',
  platform: 'linkedin',
  title: 'Senior Software Engineer',
  company: 'Google',
  location: 'Mountain View, CA, USA',
  remote_type: 'hybrid',
  salary_min: 150000,
  salary_max: 250000,
  salary_currency: 'USD',
  salary_period: 'yearly',
  employment_type: 'full-time',
  skills_required: ['javascript', 'react', 'node.js'],
  url: 'https://linkedin.com/jobs/view/12345',
});

// Batch insert
await inserter.batchInsert([
  { job_id: 'remoteok-001', platform: 'remoteok', title: 'Frontend Dev', company: 'Startup', ... },
  { job_id: 'remoteok-002', platform: 'remoteok', title: 'Backend Dev', company: 'BigCorp', ... },
]);

// Get stats
const stats = await inserter.getStats('linkedin');
console.log(stats);
// {
//   total_jobs: 1234,
//   total_companies: 567,
//   remote_jobs: 890,
//   jobs_with_salary: 345,
//   avg_min_salary: 120000,
//   avg_max_salary: 180000,
//   jobs_last_week: 56,
//   jobs_last_month: 234
// }
*/
