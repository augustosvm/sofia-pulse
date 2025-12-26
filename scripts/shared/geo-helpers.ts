/**
 * Geographic Normalization Helpers for TypeScript
 * Funções para obter países, estados e cidades normalizados
 *
 * UPDATED 2025-12-23: Now uses normalized lookup functions instead of get_or_create
 * This prevents duplicates and ensures referential integrity with normalized tables.
 *
 * UPDATED 2025-12-26: Added intelligent fallbacks for common mismatches
 */

import { Pool } from 'pg';
import { getCountryId, getStateId, getCityId } from './geo-id-helpers.js';

// ============================================================================
// INTELLIGENT FALLBACKS - Maps common mistakes to correct countries
// ============================================================================

const CITY_TO_COUNTRY: Record<string, string> = {
  'berlin': 'Germany', 'munich': 'Germany', 'hamburg': 'Germany',
  'dublin': 'Ireland', 'london': 'United Kingdom', 'manchester': 'United Kingdom',
  'paris': 'France', 'amsterdam': 'Netherlands', 'barcelona': 'Spain',
  'bangalore': 'India', 'bengaluru': 'India', 'mumbai': 'India',
  'singapore': 'Singapore', 'tokyo': 'Japan', 'seoul': 'South Korea',
  'sydney': 'Australia', 'melbourne': 'Australia',
  'são paulo': 'Brazil', 'sao paulo': 'Brazil', 'rio de janeiro': 'Brazil',
  'buenos aires': 'Argentina', 'santiago': 'Chile',
  'toronto': 'Canada', 'vancouver': 'Canada',
  'new york': 'United States', 'los angeles': 'United States',
  'san francisco': 'United States', 'chicago': 'United States',
};

const STATE_TO_COUNTRY: Record<string, string> = {
  'california': 'United States', 'texas': 'United States',
  'florida': 'United States', 'new york': 'United States',
};

const COUNTRY_ALIASES: Record<string, string> = {
  'brasil': 'Brazil', 'usa': 'United States', 'us': 'United States',
  'uk': 'United Kingdom', 'uae': 'United Arab Emirates',
};

/**
 * Aplica fallbacks inteligentes para corrigir erros comuns
 */
function applyIntelligentFallbacks(countryName: string): string {
    const normalized = countryName.toLowerCase().trim();

    // Ignore "Remote" and similar
    if (/^(remote|anywhere|worldwide|global)$/i.test(normalized)) {
        return '';
    }

    // Try alias first
    if (COUNTRY_ALIASES[normalized]) {
        return COUNTRY_ALIASES[normalized];
    }

    // Try city to country
    if (CITY_TO_COUNTRY[normalized]) {
        return CITY_TO_COUNTRY[normalized];
    }

    // Try state to country
    if (STATE_TO_COUNTRY[normalized]) {
        return STATE_TO_COUNTRY[normalized];
    }

    // Return original if no fallback found
    return countryName;
}

/**
 * Obtém um país normalizado da tabela sofia.countries
 * Tenta múltiplas estratégias: ISO codes, nome comum, fallbacks inteligentes
 * NÃO cria novos registros - apenas faz lookup
 */
export async function getOrCreateCountry(
    pool: Pool,
    countryName: string | null | undefined
): Promise<number | null> {
    if (!countryName || countryName.trim() === '') {
        return null;
    }

    // Apply intelligent fallbacks first
    const correctedName = applyIntelligentFallbacks(countryName.trim());
    if (!correctedName) {
        return null; // "Remote" etc
    }

    // Use new lookup function that tries ISO codes and names
    return await getCountryId(pool, correctedName);
}

/**
 * Obtém um estado normalizado da tabela sofia.states
 * Busca por código (2 letras) ou nome dentro do país especificado
 * NÃO cria novos registros - apenas faz lookup
 */
export async function getOrCreateState(
    pool: Pool,
    stateName: string | null | undefined,
    countryId: number | null
): Promise<number | null> {
    if (!stateName || stateName.trim() === '' || !countryId) {
        return null;
    }

    // Use new lookup function that tries state code and name
    return await getStateId(pool, stateName.trim(), countryId);
}

/**
 * Obtém uma cidade normalizada da tabela sofia.cities
 * Busca por nome dentro do estado/país especificado
 * NÃO cria novos registros - apenas faz lookup
 */
export async function getOrCreateCity(
    pool: Pool,
    cityName: string | null | undefined,
    stateId: number | null,
    countryId: number | null
): Promise<number | null> {
    if (!cityName || cityName.trim() === '' || !countryId) {
        return null;
    }

    // Use new lookup function that tries with state_id and country_id
    return await getCityId(pool, cityName.trim(), stateId, countryId);
}

/**
 * Normaliza uma localização completa (país, estado, cidade)
 * Retorna os IDs normalizados
 */
export async function normalizeLocation(
    pool: Pool,
    location: {
        country?: string | null;
        state?: string | null;
        city?: string | null;
    }
): Promise<{
    countryId: number | null;
    stateId: number | null;
    cityId: number | null;
}> {
    const countryId = await getOrCreateCountry(pool, location.country);
    const stateId = await getOrCreateState(pool, location.state, countryId);
    const cityId = await getOrCreateCity(pool, location.city, stateId, countryId);
    return { countryId, stateId, cityId };
}
