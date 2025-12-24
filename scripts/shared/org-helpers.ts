/**
 * Organization Helpers
 * Helper functions to link jobs to normalized organizations table.
 */

import { Pool, PoolClient } from 'pg';

/**
 * Get or create organization ID from company name.
 *
 * @param pool - PostgreSQL connection pool
 * @param companyName - Company name (required)
 * @param companyUrl - Company website (optional)
 * @param location - Company location (optional)
 * @param country - Company country (optional)
 * @param source - Data source name (default: 'jobs-collector')
 * @returns organization_id or null if company is generic/unknown
 *
 * @example
 * const orgId = await getOrCreateOrganization(
 *   pool,
 *   'OpenAI',
 *   'https://openai.com',
 *   'San Francisco, CA',
 *   'USA',
 *   'github-jobs'
 * );
 */
export async function getOrCreateOrganization(
    pool: Pool | PoolClient,
    companyName: string,
    companyUrl?: string | null,
    location?: string | null,
    country?: string | null,
    source: string = 'jobs-collector'
): Promise<number | null> {
    try {
        const result = await pool.query(`
            SELECT sofia.get_or_create_organization($1, $2, $3, $4, $5)
        `, [companyName, companyUrl, location, country, source]);

        return result.rows[0]?.get_or_create_organization || null;

    } catch (error) {
        console.error(`   ⚠️  Error getting/creating organization for '${companyName}':`, error);
        return null;
    }
}

/**
 * Find existing organization by name (fuzzy match).
 *
 * @param pool - PostgreSQL connection pool
 * @param companyName - Company name to search
 * @returns organization_id or null if not found
 */
export async function getOrganizationByName(
    pool: Pool | PoolClient,
    companyName: string
): Promise<number | null> {
    if (!companyName) {
        return null;
    }

    try {
        const result = await pool.query(`
            SELECT id
            FROM sofia.organizations
            WHERE LOWER(TRIM(REGEXP_REPLACE(name, '[^a-zA-Z0-9\\s]', '', 'g')))
                = LOWER(TRIM(REGEXP_REPLACE($1, '[^a-zA-Z0-9\\s]', '', 'g')))
            LIMIT 1
        `, [companyName]);

        return result.rows[0]?.id || null;

    } catch (error) {
        console.error(`   ⚠️  Error finding organization '${companyName}':`, error);
        return null;
    }
}

/**
 * Batch process to link existing jobs to organizations.
 * Processes jobs that have company name but no organization_id.
 *
 * @param pool - PostgreSQL connection pool
 * @param batchSize - Number of jobs to process per batch
 * @returns Statistics about the linking process
 */
export async function batchLinkJobsToOrganizations(
    pool: Pool | PoolClient,
    batchSize: number = 1000
): Promise<{
    total_to_process: number;
    total_processed: number;
    linked: number;
    skipped: number;
    errors: number;
}> {
    const stats = {
        total_to_process: 0,
        total_processed: 0,
        linked: 0,
        skipped: 0,
        errors: 0
    };

    try {
        // Get count of jobs to process
        const countResult = await pool.query(`
            SELECT COUNT(*)
            FROM sofia.jobs
            WHERE organization_id IS NULL
                AND company IS NOT NULL
                AND TRIM(company) != ''
                AND LOWER(TRIM(company)) NOT IN ('não informado', 'confidential', 'n/a', 'unknown')
        `);

        const total = parseInt(countResult.rows[0].count);
        stats.total_to_process = total;

        console.log(`   📊 Found ${total} jobs to link to organizations`);

        let offset = 0;

        while (offset < total) {
            // Process batch
            const jobsResult = await pool.query(`
                SELECT id, company, company_url, location, country, platform
                FROM sofia.jobs
                WHERE organization_id IS NULL
                    AND company IS NOT NULL
                    AND TRIM(company) != ''
                    AND LOWER(TRIM(company)) NOT IN ('não informado', 'confidential', 'n/a', 'unknown')
                ORDER BY id
                LIMIT $1 OFFSET $2
            `, [batchSize, offset]);

            for (const job of jobsResult.rows) {
                try {
                    const orgId = await getOrCreateOrganization(
                        pool,
                        job.company,
                        job.company_url,
                        job.location,
                        job.country,
                        job.platform || 'jobs-collector'
                    );

                    if (orgId) {
                        await pool.query(`
                            UPDATE sofia.jobs
                            SET organization_id = $1
                            WHERE id = $2
                        `, [orgId, job.id]);
                        stats.linked++;
                    } else {
                        stats.skipped++;
                    }

                    stats.total_processed++;

                } catch (error) {
                    console.error(`   ⚠️  Error processing job ${job.id}:`, error);
                    stats.errors++;
                }
            }

            offset += batchSize;

            if (stats.total_processed % 100 === 0) {
                console.log(`   📊 Processed ${stats.total_processed}/${total} jobs...`);
            }
        }

        console.log(`\n   ✅ Linking complete:`);
        console.log(`      - Processed: ${stats.total_processed}`);
        console.log(`      - Linked: ${stats.linked}`);
        console.log(`      - Skipped: ${stats.skipped}`);
        console.log(`      - Errors: ${stats.errors}`);

        return stats;

    } catch (error) {
        console.error(`   ❌ Batch linking failed:`, error);
        stats.errors++;
        return stats;
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get top hiring companies by job count in the last N days.
 */
export async function getTopHiringCompanies(
    pool: Pool | PoolClient,
    limit: number = 20,
    days: number = 30
): Promise<Array<{ name: string; country: string; job_count: number }>> {
    const result = await pool.query(`
        SELECT
            o.name,
            o.country,
            COUNT(j.id) as job_count
        FROM sofia.organizations o
        JOIN sofia.jobs j ON o.id = j.organization_id
        WHERE j.posted_date >= CURRENT_DATE - INTERVAL '${days} days'
            AND o.type = 'employer'
        GROUP BY o.name, o.country
        ORDER BY job_count DESC
        LIMIT $1
    `, [limit]);

    return result.rows;
}

/**
 * Get job posting history for a specific organization.
 */
export async function getCompanyJobHistory(
    pool: Pool | PoolClient,
    organizationId: number
): Promise<Array<{ title: string; location: string; posted_date: Date; url: string }>> {
    const result = await pool.query(`
        SELECT
            title,
            location,
            posted_date,
            url
        FROM sofia.jobs
        WHERE organization_id = $1
        ORDER BY posted_date DESC
    `, [organizationId]);

    return result.rows;
}
