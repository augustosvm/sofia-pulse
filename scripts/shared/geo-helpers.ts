/**
 * Geographic Normalization Helpers for TypeScript
 * Funções para obter/criar países, estados e cidades normalizados
 */

import { Pool } from 'pg';

/**
 * Obtém ou cria um país normalizado
 * Usa a função SQL get_or_create_country()
 */
export async function getOrCreateCountry(
    pool: Pool,
    countryName: string | null | undefined
): Promise<number | null> {
    if (!countryName || countryName.trim() === '') {
        return null;
    }

    try {
        const result = await pool.query(
            'SELECT get_or_create_country($1) as country_id',
            [countryName.trim()]
        );
        return result.rows[0]?.country_id || null;
    } catch (error) {
        console.error(`Erro ao normalizar país "${countryName}":`, error);
        return null;
    }
}

/**
 * Obtém ou cria um estado normalizado
 * Usa a função SQL get_or_create_state()
 */
export async function getOrCreateState(
    pool: Pool,
    stateName: string | null | undefined,
    countryId: number | null
): Promise<number | null> {
    if (!stateName || stateName.trim() === '' || !countryId) {
        return null;
    }

    try {
        const result = await pool.query(
            'SELECT get_or_create_state($1, $2) as state_id',
            [stateName.trim(), countryId]
        );
        return result.rows[0]?.state_id || null;
    } catch (error) {
        console.error(`Erro ao normalizar estado "${stateName}":`, error);
        return null;
    }
}

/**
 * Obtém ou cria uma cidade normalizada
 * Usa a função SQL get_or_create_city()
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

    try {
        const result = await pool.query(
            'SELECT get_or_create_city($1, $2, $3) as city_id',
            [cityName.trim(), stateId, countryId]
        );
        return result.rows[0]?.city_id || null;
    } catch (error) {
        console.error(`Erro ao normalizar cidade "${cityName}":`, error);
        return null;
    }
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
