#!/usr/bin/env tsx
/**
 * NGOs Collector - GlobalGiving Bulk Download
 *
 * FONTE REAL: GlobalGiving API - Official "Get All Organizations (Bulk Download)" method
 * Docs: https://www.globalgiving.org/api/methods/get-all-organizations-download/
 *
 * FLUXO:
 * 1. GET /api/public/orgservice/all/organizations/download?api_key=KEY
 * 2. Extract signed S3 URL from XML response
 * 3. Download organizations.xml from S3 (16MB, ~6,271 organizations)
 * 4. Parse XML and extract organizations
 * 5. Insert/upsert into sofia.organizations with proper foreign keys
 *
 * REGRAS:
 * - API key OBRIGATÓRIO (GLOBALGIVING_API_KEY env var)
 * - Se ausente: log claro + fail hard (exit code != 0)
 * - Proibido fallback que insere dados inventados
 * - Se fetched == 0 OU saved == 0 → FAIL (exceto se API retorna realmente vazio)
 * - collector_runs: status=failed com error_message exato
 */

import axios from 'axios';
import { Pool } from 'pg';
import * as dotenv from 'dotenv';
import { parseStringPromise } from 'xml2js';

dotenv.config();

// ============================================================================
// DATABASE CONFIG
// ============================================================================

const dbConfig = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'sofia',
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DB || 'sofia_db',
};

// ============================================================================
// TYPES
// ============================================================================

interface GlobalGivingOrganization {
  id: string[];
  name: string[];
  mission?: string[];
  addressLine1?: string[];
  addressLine2?: string[];
  city?: string[];
  state?: string[];
  country?: string[];
  iso3166CountryCode?: string[];
  postal?: string[];
  ein?: string[];
  url?: string[];
  logoUrl?: string[];
  activeProjects?: string[];
  totalProjects?: string[];
  countries?: Array<{
    country: Array<{
      iso3166CountryCode: string[];
      name: string[];
    }>;
  }>;
  themes?: Array<{
    theme: Array<{
      id: string[];
      name: string[];
    }>;
  }>;
}

interface OrganizationInsertData {
  organization_id: string;
  name: string;
  type: string;
  country_id: number | null;
  city_id: number | null;
  metadata: any;
}

// ============================================================================
// NGOS COLLECTOR
// ============================================================================

export class NGOsCollector {
  private pool: Pool;

  constructor() {
    this.pool = new Pool(dbConfig);
  }

  /**
   * Main collection flow
   */
  async collect(): Promise<{
    success: boolean;
    fetched: number;
    saved: number;
    errors: number;
    duration: number;
  }> {
    const startTime = Date.now();

    console.log('');
    console.log('='.repeat(70));
    console.log('🌍 GlobalGiving NGOs - Bulk Download');
    console.log('='.repeat(70));
    console.log('');

    let fetched = 0;
    let saved = 0;
    let errors = 0;
    let runId: number | null = null;

    try {
      // 1. VALIDATE API KEY (MANDATORY)
      const apiKey = process.env.GLOBALGIVING_API_KEY;
      if (!apiKey) {
        const errorMsg = 'GLOBALGIVING_API_KEY is required but not set in .env';
        console.error('');
        console.error('❌ FATAL ERROR:', errorMsg);
        console.error('');
        console.error('Get FREE API key at: https://www.globalgiving.org/api/keys/new/');
        console.error('Then add to .env: GLOBALGIVING_API_KEY=<your-key>');
        console.error('');

        // Track failed run
        await this.trackRun('failed', 0, 0, 1, errorMsg);

        return {
          success: false,
          fetched: 0,
          saved: 0,
          errors: 1,
          duration: Date.now() - startTime,
        };
      }

      // Start tracking
      const hostname = require('os').hostname();
      const result = await this.pool.query(
        'SELECT sofia.start_collector_run($1, $2) as run_id',
        ['ngos', hostname]
      );
      runId = result.rows[0]?.run_id;
      console.log(`🔍 Run ID: ${runId}`);
      console.log('');

      // 2. GET SIGNED URL from GlobalGiving API
      console.log('📡 Step 1/4: Requesting signed download URL...');
      const downloadEndpoint = `https://api.globalgiving.org/api/public/orgservice/all/organizations/download?api_key=${apiKey}`;

      const downloadResponse = await axios.get(downloadEndpoint, {
        timeout: 30000,
        validateStatus: (status) => status >= 200 && status < 500,
      });

      if (downloadResponse.status !== 200) {
        throw new Error(`API returned status ${downloadResponse.status}`);
      }

      // API returns JSON: {"download": {"url": "https://..."}}
      const downloadData =
        typeof downloadResponse.data === 'string'
          ? JSON.parse(downloadResponse.data)
          : downloadResponse.data;

      const signedUrl = downloadData?.download?.url;

      if (!signedUrl) {
        throw new Error('No signed URL found in API response');
      }

      console.log(`   ✅ Signed URL received (valid for ~1 hour)`);
      console.log('');

      // 3. DOWNLOAD organizations.xml from S3
      console.log('📥 Step 2/4: Downloading organizations.xml from S3...');
      const xmlResponse = await axios.get(signedUrl, {
        timeout: 120000, // 2 minutes (16MB file)
        validateStatus: (status) => status >= 200 && status < 500,
      });

      if (xmlResponse.status !== 200) {
        throw new Error(`S3 returned status ${xmlResponse.status}`);
      }

      const fileSizeMB = (Buffer.byteLength(xmlResponse.data, 'utf8') / (1024 * 1024)).toFixed(2);
      console.log(`   ✅ Downloaded ${fileSizeMB} MB`);
      console.log('');

      // 4. PARSE XML
      console.log('🔄 Step 3/4: Parsing XML...');
      const xml = await parseStringPromise(xmlResponse.data);

      const organizations: GlobalGivingOrganization[] = xml.organizations?.organization || [];
      const numberFound = parseInt(xml.organizations?.$?.numberFound || '0');

      fetched = organizations.length;
      console.log(`   ✅ Parsed ${fetched} organizations (reported: ${numberFound})`);
      console.log('');

      // VALIDATION: If fetched == 0, this is suspicious (unless API truly empty)
      if (fetched === 0) {
        throw new Error('Parsed 0 organizations - this is unexpected for GlobalGiving bulk download');
      }

      // 5. INSERT INTO DATABASE
      console.log('💾 Step 4/4: Inserting into database...');

      for (const org of organizations) {
        try {
          await this.insertOrganization(org);
          saved++;

          // Progress indicator every 500 orgs
          if (saved % 500 === 0) {
            console.log(`   ... ${saved}/${fetched} saved`);
          }
        } catch (error: any) {
          console.error(`   ❌ Error inserting org ID ${org.id?.[0]}:`, error.message);
          errors++;
        }
      }

      console.log(`   ✅ Saved ${saved} organizations`);
      if (errors > 0) {
        console.log(`   ⚠️  ${errors} errors during insertion`);
      }
      console.log('');

      // VALIDATION: If saved == 0, FAIL
      if (saved === 0) {
        throw new Error(`Fetched ${fetched} organizations but saved 0 - database insertion failed`);
      }

      const duration = Date.now() - startTime;

      // Finish tracking (success)
      if (runId) {
        await this.pool.query(
          'SELECT sofia.finish_collector_run($1, $2, $3, $4)',
          [runId, 'success', saved, errors]
        );
      }

      console.log('='.repeat(70));
      console.log('✅ Collection complete!');
      console.log(`   Run ID: ${runId}`);
      console.log(`   Fetched: ${fetched} organizations`);
      console.log(`   Saved: ${saved} organizations`);
      console.log(`   Errors: ${errors}`);
      console.log(`   Duration: ${(duration / 1000).toFixed(2)}s`);
      console.log('='.repeat(70));
      console.log('');

      return {
        success: true,
        fetched,
        saved,
        errors,
        duration,
      };
    } catch (error: any) {
      console.error('');
      console.error('❌ Collection FAILED:', error.message);
      console.error('');

      if (axios.isAxiosError(error)) {
        if (error.response?.status === 403 || error.response?.status === 401) {
          console.error('💡 Hint: Check if GLOBALGIVING_API_KEY is valid');
          console.error('   Get API key at: https://www.globalgiving.org/api/keys/new/');
        } else if (error.response?.status === 429) {
          console.error('💡 Hint: Rate limit exceeded, try again later');
        }
      }

      // Track failed run
      await this.trackRun('failed', fetched, saved, Math.max(errors, 1), error.message);

      return {
        success: false,
        fetched,
        saved,
        errors: Math.max(errors, 1),
        duration: Date.now() - startTime,
      };
    }
  }

  /**
   * Insert organization with proper foreign keys
   */
  private async insertOrganization(org: GlobalGivingOrganization): Promise<void> {
    // Extract fields (GlobalGiving uses arrays for all fields)
    const orgId = `globalgiving-${org.id?.[0] || 'unknown'}`;
    const name = org.name?.[0] || 'Unknown Organization';
    const mission = org.mission?.[0];
    const addressLine1 = org.addressLine1?.[0];
    const addressLine2 = org.addressLine2?.[0];
    const city = org.city?.[0];
    const state = org.state?.[0];
    const country = org.country?.[0];
    const countryCode = org.iso3166CountryCode?.[0];
    const postal = org.postal?.[0];
    const ein = org.ein?.[0]; // Tax ID
    const url = org.url?.[0];
    const logoUrl = org.logoUrl?.[0];
    const activeProjects = parseInt(org.activeProjects?.[0] || '0');
    const totalProjects = parseInt(org.totalProjects?.[0] || '0');

    // Extract operating countries
    const operatingCountries =
      org.countries?.[0]?.country?.map((c) => ({
        code: c.iso3166CountryCode?.[0],
        name: c.name?.[0],
      })) || [];

    // Extract themes
    const themes =
      org.themes?.[0]?.theme?.map((t) => ({
        id: t.id?.[0],
        name: t.name?.[0],
      })) || [];

    // Resolve country_id (headquarters)
    let countryId: number | null = null;
    if (country || countryCode) {
      const countryResult = await this.pool.query(
        `SELECT id FROM sofia.countries
         WHERE common_name = $1
            OR iso_alpha2 = $2
            OR iso_alpha3 = $2
            OR UPPER(common_name) = UPPER($1)
         LIMIT 1`,
        [country || '', countryCode || '']
      );

      if (countryResult.rows.length > 0) {
        countryId = countryResult.rows[0].id;
      } else if (country) {
        // Auto-create country if not exists
        const insertResult = await this.pool.query(
          `INSERT INTO sofia.countries (common_name, iso_alpha2, iso_alpha3)
           VALUES ($1, $2, $3)
           ON CONFLICT (common_name) DO UPDATE SET common_name = EXCLUDED.common_name
           RETURNING id`,
          [country, countryCode?.substring(0, 2) || null, countryCode?.substring(0, 3) || null]
        );
        countryId = insertResult.rows[0].id;
      }
    }

    // Resolve city_id (only if country exists)
    let cityId: number | null = null;
    if (city && countryId) {
      let cityResult = await this.pool.query(
        `SELECT id FROM sofia.cities
         WHERE name = $1 AND country_id = $2
         LIMIT 1`,
        [city, countryId]
      );

      if (cityResult.rows.length > 0) {
        cityId = cityResult.rows[0].id;
      } else {
        // Auto-create city
        const insertResult = await this.pool.query(
          `INSERT INTO sofia.cities (name, state_id, country_id)
           VALUES ($1, NULL, $2)
           ON CONFLICT (name, state_id, country_id) DO UPDATE
           SET name = EXCLUDED.name
           RETURNING id`,
          [city, countryId]
        );
        cityId = insertResult.rows[0].id;
      }
    }

    // Build metadata (all extra fields)
    const metadata = {
      source: 'globalgiving',
      source_org_id: org.id?.[0],
      mission,
      addressLine1,
      addressLine2,
      state,
      postal,
      ein,
      website: url,
      logoUrl,
      activeProjects,
      totalProjects,
      operatingCountries,
      themes,
    };

    // Remove null/undefined
    Object.keys(metadata).forEach((key) => {
      if (metadata[key] === null || metadata[key] === undefined) {
        delete metadata[key];
      }
    });

    // INSERT/UPSERT
    const query = `
      INSERT INTO sofia.organizations (
        organization_id, name, type, country_id, city_id, metadata
      )
      VALUES ($1, $2, $3, $4, $5, $6)
      ON CONFLICT (organization_id)
      DO UPDATE SET
        name = EXCLUDED.name,
        type = EXCLUDED.type,
        country_id = EXCLUDED.country_id,
        city_id = EXCLUDED.city_id,
        metadata = sofia.organizations.metadata || EXCLUDED.metadata
    `;

    await this.pool.query(query, [
      orgId,
      name,
      'ngo',
      countryId,
      cityId,
      JSON.stringify(metadata),
    ]);
  }

  /**
   * Track run (for failed cases without runId)
   */
  private async trackRun(
    status: string,
    fetched: number,
    saved: number,
    errors: number,
    errorMessage?: string
  ): Promise<void> {
    try {
      const hostname = require('os').hostname();
      await this.pool.query(
        `INSERT INTO sofia.collector_runs (collector_name, status, records_inserted, error_message, metadata)
         VALUES ($1, $2, $3, $4, $5)`,
        ['ngos', status, saved, errorMessage || null, JSON.stringify({ fetched, errors, hostname })]
      );
    } catch (error) {
      console.error('Failed to track run:', error);
    }
  }

  async close(): Promise<void> {
    await this.pool.end();
  }
}

// ============================================================================
// CLI EXECUTION
// ============================================================================

if (require.main === module) {
  (async () => {
    const collector = new NGOsCollector();

    try {
      const result = await collector.collect();

      // Exit with proper code
      if (!result.success || result.saved === 0) {
        console.error('❌ Collection failed or saved 0 records - exiting with code 1');
        process.exit(1);
      }

      process.exit(0);
    } catch (error: any) {
      console.error('❌ Fatal error:', error.message);
      process.exit(1);
    } finally {
      await collector.close();
    }
  })();
}
