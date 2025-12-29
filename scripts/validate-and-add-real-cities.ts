#!/usr/bin/env npx tsx
/**
 * Validate and Add REAL Cities Only
 *
 * Uses GeoNames API to verify cities exist before adding to database
 *
 * Run: npx tsx scripts/validate-and-add-real-cities.ts
 */

import { Pool } from 'pg';
import http from 'http';

const pool = new Pool({
  host: process.env.DB_HOST || '91.98.158.19',
  port: parseInt(process.env.DB_PORT || '5432'),
  user: process.env.DB_USER || 'sofia',
  password: process.env.DB_PASSWORD || 'sofia123strong',
  database: process.env.DB_NAME || 'sofia_db',
});

// GeoNames API (free, no key needed for basic search)
// Alternative: Use username for higher limits
const GEONAMES_USERNAME = 'demo';  // Replace with your username if you have one

interface CityCandidate {
  name: string;
  country_id: number;
  country_code: string;
  state_id: number | null;
  job_count: number;
}

/**
 * Validate city via GeoNames API
 */
async function validateCity(cityName: string, countryCode: string): Promise<boolean> {
  return new Promise((resolve) => {
    const url = `http://api.geonames.org/searchJSON?q=${encodeURIComponent(cityName)}&country=${countryCode}&maxRows=1&username=${GEONAMES_USERNAME}&featureClass=P`;

    http.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          // City is valid if GeoNames returns at least one result
          resolve(json.totalResultsCount > 0);
        } catch {
          resolve(false);
        }
      });
    }).on('error', () => {
      resolve(false);  // On error, assume invalid
    });
  });
}

/**
 * Get country code from country_id
 */
const countryCodeCache = new Map<number, string>();

async function getCountryCode(pool: Pool, countryId: number): Promise<string | null> {
  if (countryCodeCache.has(countryId)) {
    return countryCodeCache.get(countryId)!;
  }

  const result = await pool.query(
    'SELECT iso_alpha2 FROM sofia.countries WHERE id = $1',
    [countryId]
  );

  if (result.rows.length > 0) {
    const code = result.rows[0].iso_alpha2;
    countryCodeCache.set(countryId, code);
    return code;
  }

  return null;
}

async function main() {
  console.log('🌍 Validating cities via GeoNames API...\n');

  try {
    // Get city candidates (have country_id, no city_id, not Remote/placeholders)
    const candidates = await pool.query<CityCandidate>(`
      SELECT DISTINCT
        j.city as name,
        j.country_id,
        c.iso_alpha2 as country_code,
        j.state_id,
        COUNT(*) as job_count
      FROM sofia.jobs j
      JOIN sofia.countries c ON j.country_id = c.id
      WHERE j.city_id IS NULL
        AND j.city IS NOT NULL
        AND j.city != ''
        AND j.country_id IS NOT NULL
        -- Filter obvious invalids
        AND NOT (j.city ILIKE '%remote%' OR j.city ILIKE '%hybrid%' OR j.city ILIKE '%distributed%')
        AND j.city NOT IN ('In-Office', 'LOCATION', 'N/A', 'NA', 'TBD', 'LATAM', 'EMEA', 'APAC')
        AND LENGTH(j.city) >= 3  -- At least 3 characters
        AND NOT (j.city LIKE '%, %')  -- Not "City, State" format
      GROUP BY j.city, j.country_id, c.iso_alpha2, j.state_id
      HAVING COUNT(*) >= 2  -- At least 2 jobs
      ORDER BY COUNT(*) DESC
      LIMIT 200  -- Validate top 200
    `);

    console.log(`📊 Found ${candidates.rowCount} city candidates to validate\n`);

    const validated: CityCandidate[] = [];
    const rejected: string[] = [];
    let apiCalls = 0;

    for (const candidate of candidates.rows) {
      // Rate limit: 1 request per second (GeoNames free tier)
      await new Promise(resolve => setTimeout(resolve, 1100));

      const isValid = await validateCity(candidate.name, candidate.country_code);
      apiCalls++;

      if (isValid) {
        validated.push(candidate);
        console.log(`✅ [${apiCalls}/${candidates.rowCount}] ${candidate.name} | ${candidate.country_code} - VALID`);
      } else {
        rejected.push(`${candidate.name} | ${candidate.country_code}`);
        console.log(`❌ [${apiCalls}/${candidates.rowCount}] ${candidate.name} | ${candidate.country_code} - REJECTED`);
      }
    }

    console.log(`\n📈 Validation complete:`);
    console.log(`  Validated: ${validated.length}`);
    console.log(`  Rejected: ${rejected.length}`);
    console.log(`  Potential jobs: ${validated.reduce((sum, c) => sum + c.job_count, 0)}`);

    if (validated.length === 0) {
      console.log('\n⚠️  No cities validated. Exiting.');
      return;
    }

    // Insert validated cities
    console.log(`\n💾 Inserting ${validated.length} VALIDATED cities...`);

    for (const city of validated) {
      await pool.query(`
        INSERT INTO sofia.cities (name, state_id, country_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (name, state_id, country_id) DO NOTHING
      `, [city.name, city.state_id, city.country_id]);
    }

    // Update jobs
    await pool.query(`
      UPDATE sofia.jobs j
      SET city_id = c.id
      FROM sofia.cities c
      WHERE j.city_id IS NULL
        AND j.city = c.name
        AND j.country_id = c.country_id
        AND (j.state_id = c.state_id OR (j.state_id IS NULL AND c.state_id IS NULL))
    `);

    // Final stats
    const final = await pool.query(`
      SELECT
        COUNT(*) as total,
        COUNT(city_id) as with_city,
        ROUND(100.0 * COUNT(city_id) / COUNT(*), 1) as pct
      FROM sofia.jobs
    `);

    console.log(`\n========================================`);
    console.log(`FINAL RESULTS`);
    console.log(`========================================`);
    console.log(`Jobs with city_id: ${final.rows[0].with_city} (${final.rows[0].pct}%)`);
    console.log(`========================================\n`);

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    await pool.end();
  }
}

main().catch(console.error);
