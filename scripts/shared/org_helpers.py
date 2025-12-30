#!/usr/bin/env python3
"""
Organization Helpers
Helper functions to link jobs to normalized organizations table.
"""


def get_or_create_organization(
    cursor, company_name, company_url=None, location=None, country=None, source="jobs-collector"
):
    """
    Get or create organization ID from company name.

    Args:
        cursor: psycopg2 cursor (NOT connection)
        company_name: Company name (required)
        company_url: Company website (optional)
        location: Company location (optional)
        country: Company country (optional)
        source: Data source name (default: 'jobs-collector')

    Returns:
        int: organization_id or None if company is generic/unknown

    Example:
        cursor = conn.cursor()
        org_id = get_or_create_organization(
            cursor,
            'OpenAI',
            'https://openai.com',
            'San Francisco, CA',
            'USA',
            'github-jobs'
        )
    """
    try:
        cursor.execute(
            """
            SELECT sofia.get_or_create_organization(
                %s, %s, %s, %s, %s
            )
        """,
            (company_name, company_url, location, country, source),
        )

        result = cursor.fetchone()
        return result[0] if result else None

    except Exception as e:
        print(f"   ⚠️  Error getting/creating organization for '{company_name}': {e}")
        return None


def get_organization_by_name(cursor, company_name):
    """
    Find existing organization by name (fuzzy match).

    Args:
        cursor: psycopg2 cursor
        company_name: Company name to search

    Returns:
        int: organization_id or None if not found
    """
    if not company_name:
        return None

    try:
        company_name.lower().strip()

        cursor.execute(
            """
            SELECT id
            FROM sofia.organizations
            WHERE LOWER(TRIM(REGEXP_REPLACE(name, '[^a-zA-Z0-9\s]', '', 'g')))
                = LOWER(TRIM(REGEXP_REPLACE(%s, '[^a-zA-Z0-9\s]', '', 'g')))
            LIMIT 1
        """,
            (company_name,),
        )

        result = cursor.fetchone()
        return result[0] if result else None

    except Exception as e:
        print(f"   ⚠️  Error finding organization '{company_name}': {e}")
        return None


def batch_link_jobs_to_organizations(cursor, batch_size=1000):
    """
    Batch process to link existing jobs to organizations.
    Processes jobs that have company name but no organization_id.

    Args:
        cursor: psycopg2 cursor
        batch_size: Number of jobs to process per batch

    Returns:
        dict: Statistics about the linking process
    """
    stats = {"total_processed": 0, "linked": 0, "skipped": 0, "errors": 0}

    try:
        # Get count of jobs to process
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM sofia.jobs
            WHERE organization_id IS NULL
                AND company IS NOT NULL
                AND TRIM(company) != ''
                AND LOWER(TRIM(company)) NOT IN ('não informado', 'confidential', 'n/a', 'unknown')
        """
        )
        total = cursor.fetchone()[0]
        stats["total_to_process"] = total

        print(f"   📊 Found {total} jobs to link to organizations")

        offset = 0
        while offset < total:
            # Process batch
            cursor.execute(
                """
                SELECT id, company, company_url, location, country, platform
                FROM sofia.jobs
                WHERE organization_id IS NULL
                    AND company IS NOT NULL
                    AND TRIM(company) != ''
                    AND LOWER(TRIM(company)) NOT IN ('não informado', 'confidential', 'n/a', 'unknown')
                ORDER BY id
                LIMIT %s OFFSET %s
            """,
                (batch_size, offset),
            )

            jobs = cursor.fetchall()

            for job in jobs:
                job_id, company, company_url, location, country, platform = job

                try:
                    org_id = get_or_create_organization(
                        cursor, company, company_url, location, country, platform or "jobs-collector"
                    )

                    if org_id:
                        cursor.execute(
                            """
                            UPDATE sofia.jobs
                            SET organization_id = %s
                            WHERE id = %s
                        """,
                            (org_id, job_id),
                        )
                        stats["linked"] += 1
                    else:
                        stats["skipped"] += 1

                    stats["total_processed"] += 1

                except Exception as e:
                    print(f"   ⚠️  Error processing job {job_id}: {e}")
                    stats["errors"] += 1

            offset += batch_size

            if stats["total_processed"] % 100 == 0:
                print(f"   📊 Processed {stats['total_processed']}/{total} jobs...")

        print(f"\n   ✅ Linking complete:")
        print(f"      - Processed: {stats['total_processed']}")
        print(f"      - Linked: {stats['linked']}")
        print(f"      - Skipped: {stats['skipped']}")
        print(f"      - Errors: {stats['errors']}")

        return stats

    except Exception as e:
        print(f"   ❌ Batch linking failed: {e}")
        stats["errors"] += 1
        return stats


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_top_hiring_companies(cursor, limit=20, days=30):
    """
    Get top hiring companies by job count in the last N days.

    Args:
        cursor: psycopg2 cursor
        limit: Number of companies to return
        days: Number of days to look back

    Returns:
        list: List of tuples (company_name, country, job_count)
    """
    cursor.execute(
        """
        SELECT
            o.name,
            o.country,
            COUNT(j.id) as job_count
        FROM sofia.organizations o
        JOIN sofia.jobs j ON o.id = j.organization_id
        WHERE j.posted_date >= CURRENT_DATE - INTERVAL '%s days'
            AND o.type = 'employer'
        GROUP BY o.name, o.country
        ORDER BY job_count DESC
        LIMIT %s
    """,
        (days, limit),
    )

    return cursor.fetchall()


def get_company_job_history(cursor, organization_id):
    """
    Get job posting history for a specific organization.

    Args:
        cursor: psycopg2 cursor
        organization_id: ID of the organization

    Returns:
        list: List of tuples (title, location, posted_date, url)
    """
    cursor.execute(
        """
        SELECT
            title,
            location,
            posted_date,
            url
        FROM sofia.jobs
        WHERE organization_id = %s
        ORDER BY posted_date DESC
    """,
        (organization_id,),
    )

    return cursor.fetchall()
