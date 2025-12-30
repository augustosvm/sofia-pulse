/**
 * Geographic ID Helpers
 *
 * Helper functions for collectors to lookup normalized geographic IDs
 * instead of inserting string values.
 *
 * USAGE in collectors:
 * ```typescript
 * import { getCountryId, getStateId, getCityId } from './shared/geo-id-helpers.js';
 *
 * const countryId = await getCountryId(pool, 'United States'); // or 'US' or 'USA'
 * const stateId = await getStateId(pool, 'California', countryId);
 * const cityId = await getCityId(pool, 'San Francisco', stateId, countryId);
 *
 * // Then INSERT with IDs:
 * INSERT INTO sofia.jobs (title, company, country_id, state_id, city_id)
 * VALUES ($1, $2, $3, $4, $5)
 * ```
 */

import { Pool } from 'pg';

/**
 * Get country ID from normalized countries table
 * Tries multiple strategies: ISO alpha2, ISO alpha3, common name
 */
export async function getCountryId(pool: Pool, countryInput: string | null): Promise<number | null> {
  if (!countryInput) return null;

  const country = countryInput.trim();

  try {
    // Strategy 1: Try ISO alpha2 (US, BR, GB, etc.)
    if (country.length === 2) {
      const result = await pool.query(
        'SELECT id FROM sofia.countries WHERE iso_alpha2 = $1',
        [country.toUpperCase()]
      );
      if (result.rows.length > 0) return result.rows[0].id;
    }

    // Strategy 2: Try ISO alpha3 (USA, BRA, GBR, etc.)
    if (country.length === 3) {
      const result = await pool.query(
        'SELECT id FROM sofia.countries WHERE iso_alpha3 = $1',
        [country.toUpperCase()]
      );
      if (result.rows.length > 0) return result.rows[0].id;
    }

    // Strategy 3: Try common name (case-insensitive)
    const result = await pool.query(
      'SELECT id FROM sofia.countries WHERE LOWER(common_name) = LOWER($1)',
      [country]
    );
    if (result.rows.length > 0) return result.rows[0].id;

    // Strategy 4: Try Eurostat-specific codes
    const eurostatMap: Record<string, string> = {
      'EL': 'GR',  // Greece
      'UK': 'GB',  // United Kingdom
    };

    if (eurostatMap[country.toUpperCase()]) {
      const mappedCode = eurostatMap[country.toUpperCase()];
      const result = await pool.query(
        'SELECT id FROM sofia.countries WHERE iso_alpha2 = $1',
        [mappedCode]
      );
      if (result.rows.length > 0) return result.rows[0].id;
    }

    console.warn(`⚠️  Country not found: "${country}"`);
    return null;
  } catch (error) {
    console.error(`❌ Error looking up country "${country}":`, error);
    return null;
  }
}

/**
 * Get state ID from normalized states table
 */
export async function getStateId(
  pool: Pool,
  stateName: string | null,
  countryId: number | null
): Promise<number | null> {
  if (!stateName || !countryId) return null;

  const state = stateName.trim();

  try {
    // Try by state code (e.g., "CA" for California)
    if (state.length === 2) {
      const result = await pool.query(
        'SELECT id FROM sofia.states WHERE code = $1 AND country_id = $2',
        [state.toUpperCase(), countryId]
      );
      if (result.rows.length > 0) return result.rows[0].id;
    }

    // Try by state name (case-insensitive)
    const result = await pool.query(
      'SELECT id FROM sofia.states WHERE LOWER(name) = LOWER($1) AND country_id = $2',
      [state, countryId]
    );
    if (result.rows.length > 0) return result.rows[0].id;

    console.warn(`⚠️  State not found: "${state}" in country ${countryId}`);
    return null;
  } catch (error) {
    console.error(`❌ Error looking up state "${state}":`, error);
    return null;
  }
}

/**
 * Get city ID from normalized cities table
 */
export async function getCityId(
  pool: Pool,
  cityName: string | null,
  stateId: number | null,
  countryId: number | null
): Promise<number | null> {
  if (!cityName) return null;

  const city = cityName.trim();

  try {
    // Try with state_id if available
    if (stateId) {
      const result = await pool.query(
        'SELECT id FROM sofia.cities WHERE LOWER(name) = LOWER($1) AND state_id = $2',
        [city, stateId]
      );
      if (result.rows.length > 0) return result.rows[0].id;
    }

    // Try with only country_id
    if (countryId) {
      const result = await pool.query(
        'SELECT id FROM sofia.cities WHERE LOWER(name) = LOWER($1) AND country_id = $2',
        [city, countryId]
      );
      if (result.rows.length > 0) return result.rows[0].id;
    }

    // Try without any parent (last resort)
    const result = await pool.query(
      'SELECT id FROM sofia.cities WHERE LOWER(name) = LOWER($1) LIMIT 1',
      [city]
    );
    if (result.rows.length > 0) return result.rows[0].id;

    console.warn(`⚠️  City not found: "${city}"`);
    return null;
  } catch (error) {
    console.error(`❌ Error looking up city "${city}":`, error);
    return null;
  }
}

/**
 * Get religion ID from normalized religions table
 */
export async function getReligionId(pool: Pool, religionName: string | null): Promise<number | null> {
  if (!religionName) return null;

  const religion = religionName.trim();

  try {
    const result = await pool.query(
      'SELECT id FROM sofia.religions WHERE LOWER(name) = LOWER($1)',
      [religion]
    );

    if (result.rows.length > 0) return result.rows[0].id;

    console.warn(`⚠️  Religion not found: "${religion}"`);
    return null;
  } catch (error) {
    console.error(`❌ Error looking up religion "${religion}":`, error);
    return null;
  }
}

/**
 * Batch lookup country IDs (more efficient for bulk operations)
 */
export async function getCountryIdsBatch(
  pool: Pool,
  countries: string[]
): Promise<Map<string, number>> {
  const map = new Map<string, number>();

  if (countries.length === 0) return map;

  try {
    const result = await pool.query(
      `SELECT iso_alpha2, iso_alpha3, LOWER(common_name) as name_lower, id
       FROM sofia.countries`
    );

    for (const row of result.rows) {
      map.set(row.iso_alpha2, row.id);
      map.set(row.iso_alpha3, row.id);
      map.set(row.name_lower, row.id);
    }

    return map;
  } catch (error) {
    console.error('❌ Error batch loading countries:', error);
    return map;
  }
}
