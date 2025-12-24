/**
 * Geographic Normalization Helpers for TypeScript
 * Funções para obter países, estados e cidades normalizados
 *
 * UPDATED 2025-12-23: Now uses normalized lookup functions instead of get_or_create
 * This prevents duplicates and ensures referential integrity with normalized tables.
 */

import { Pool } from 'pg';
import { getCountryId, getStateId, getCityId } from './geo-id-helpers.js';

/**
 * Obtém um país normalizado da tabela sofia.countries
 * Tenta múltiplas estratégias: ISO codes, nome comum, etc.
 * NÃO cria novos registros - apenas faz lookup
 */
export async function getOrCreateCountry(
    pool: Pool,
    countryName: string | null | undefined
): Promise<number | null> {
    if (!countryName || countryName.trim() === '') {
        return null;
    }

    // Use new lookup function that tries ISO codes and names
    return await getCountryId(pool, countryName.trim());
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
