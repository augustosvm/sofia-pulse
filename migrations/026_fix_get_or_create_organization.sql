-- Migration 026: Fix get_or_create_organization for real schema
-- Created: 2025-12-24
-- Purpose: Adapt function to match production organizations table structure

DROP FUNCTION IF EXISTS sofia.get_or_create_organization(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR);

CREATE OR REPLACE FUNCTION sofia.get_or_create_organization(
    p_company_name VARCHAR(500),
    p_company_url VARCHAR(500) DEFAULT NULL,
    p_location VARCHAR(500) DEFAULT NULL,
    p_country VARCHAR(100) DEFAULT NULL,
    p_source VARCHAR(100) DEFAULT 'jobs-collector'
) RETURNS INTEGER AS $$
DECLARE
    v_org_id INTEGER;
    v_normalized_name VARCHAR(500);
    v_metadata JSONB;
BEGIN
    -- Skip if company name is empty, null, or generic
    IF p_company_name IS NULL OR
       TRIM(p_company_name) = '' OR
       LOWER(TRIM(p_company_name)) IN ('não informado', 'confidential', 'n/a', 'unknown', 'undisclosed') THEN
        RETURN NULL;
    END IF;

    -- Normalize company name for matching (remove special chars, lowercase)
    v_normalized_name := LOWER(TRIM(REGEXP_REPLACE(p_company_name, '[^a-zA-Z0-9\s]', '', 'g')));
    v_normalized_name := REGEXP_REPLACE(v_normalized_name, '\s+', ' ', 'g'); -- collapse spaces

    -- Try to find existing organization by normalized_name
    SELECT id INTO v_org_id
    FROM sofia.organizations
    WHERE normalized_name = v_normalized_name
    LIMIT 1;

    -- If found, update metadata and return existing ID
    IF v_org_id IS NOT NULL THEN
        -- Update metadata with additional info
        UPDATE sofia.organizations
        SET metadata = metadata || jsonb_build_object(
            'company_url', COALESCE(p_company_url, metadata->>'company_url'),
            'location', COALESCE(p_location, metadata->>'location'),
            'country', COALESCE(p_country, metadata->>'country'),
            'last_seen', NOW()
        )
        WHERE id = v_org_id;

        RETURN v_org_id;
    END IF;

    -- Build metadata
    v_metadata := jsonb_build_object(
        'source', p_source,
        'company_url', p_company_url,
        'location', p_location,
        'country', p_country,
        'first_seen', NOW(),
        'last_seen', NOW()
    );

    -- Create new organization
    INSERT INTO sofia.organizations (
        name,
        normalized_name,
        type,
        metadata
    ) VALUES (
        p_company_name,
        v_normalized_name,
        'employer',
        v_metadata
    )
    ON CONFLICT (normalized_name) DO UPDATE SET
        metadata = sofia.organizations.metadata || EXCLUDED.metadata
    RETURNING id INTO v_org_id;

    RETURN v_org_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sofia.get_or_create_organization IS
'Finds or creates an organization record using production schema. Returns organization_id or NULL for generic companies.
Usage: SELECT sofia.get_or_create_organization(''OpenAI'', ''https://openai.com'', ''San Francisco'', ''USA'', ''github-jobs'');';
