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
  // Germany
  'berlin': 'Germany', 'munich': 'Germany', 'hamburg': 'Germany', 'cologne': 'Germany',
  'frankfurt': 'Germany', 'stuttgart': 'Germany', 'dortmund': 'Germany', 'düsseldorf': 'Germany',
  'mannheim': 'Germany', 'nuremberg': 'Germany', 'bremen': 'Germany', 'leipzig': 'Germany',
  'dresden': 'Germany', 'hannover': 'Germany', 'duisburg': 'Germany', 'essen': 'Germany',
  'köln': 'Germany', 'nürnberg': 'Germany', 'frankfurt am main': 'Germany',
  // UK & Ireland
  'dublin': 'Ireland', 'london': 'United Kingdom', 'manchester': 'United Kingdom', 'birmingham': 'United Kingdom',
  // France
  'paris': 'France', 'lyon': 'France', 'marseille': 'France', 'toulouse': 'France',
  'bordeaux': 'France', 'lille': 'France', 'nantes': 'France', 'nice': 'France',
  'strasbourg': 'France', 'grenoble': 'France', 'montpellier': 'France',
  // Netherlands
  'amsterdam': 'Netherlands', 'rotterdam': 'Netherlands', 'utrecht': 'Netherlands',
  'eindhoven': 'Netherlands', 'groningen': 'Netherlands', 'delft': 'Netherlands',
  'arnhem': 'Netherlands', 'maastricht': 'Netherlands',
  // Spain
  'barcelona': 'Spain', 'madrid': 'Spain', 'valencia': 'Spain', 'sevilla': 'Spain',
  'seville': 'Spain', 'bilbao': 'Spain', 'málaga': 'Spain', 'zaragoza': 'Spain',
  // Switzerland
  'zürich': 'Switzerland', 'zurich': 'Switzerland', 'geneva': 'Switzerland', 'basel': 'Switzerland',
  'bern': 'Switzerland', 'lausanne': 'Switzerland', 'lucerne': 'Switzerland', 'zug': 'Switzerland',
  // Austria
  'vienna': 'Austria', 'wien': 'Austria', 'salzburg': 'Austria', 'graz': 'Austria', 'linz': 'Austria',
  // Italy
  'rome': 'Italy', 'milan': 'Italy', 'naples': 'Italy', 'turin': 'Italy', 'florence': 'Italy',
  // Poland
  'warsaw': 'Poland', 'kraków': 'Poland', 'krakow': 'Poland', 'gdańsk': 'Poland', 'wrocław': 'Poland',
  // India
  'bangalore': 'India', 'bengaluru': 'India', 'mumbai': 'India', 'delhi': 'India',
  'pune': 'India', 'hyderabad': 'India', 'chennai': 'India', 'kolkata': 'India',
  'noida': 'India', 'gurgaon': 'India', 'ahmedabad': 'India', 'jaipur': 'India',
  'kochi': 'India', 'trivandrum': 'India', 'thiruvananthapuram': 'India', 'madurai': 'India',
  'coimbatore': 'India', 'navi mumbai': 'India',
  // Asia-Pacific
  'singapore': 'Singapore', 'tokyo': 'Japan', 'seoul': 'South Korea', 'beijing': 'China',
  'shanghai': 'China', 'hong kong': 'Hong Kong', 'bangkok': 'Thailand', 'ho chi minh': 'Vietnam',
  'manila': 'Philippines', 'jakarta': 'Indonesia', 'kuala lumpur': 'Malaysia',
  // Australia
  'sydney': 'Australia', 'melbourne': 'Australia', 'brisbane': 'Australia',
  'perth': 'Australia', 'adelaide': 'Australia', 'canberra': 'Australia',
  'melbourne cbd': 'Australia', 'perth cbd': 'Australia', 'adelaide cbd': 'Australia',
  // New Zealand
  'auckland': 'New Zealand', 'wellington': 'New Zealand', 'christchurch': 'New Zealand',
  // Brazil
  'são paulo': 'Brazil', 'sao paulo': 'Brazil', 'rio de janeiro': 'Brazil',
  'brasilia': 'Brazil', 'brasília': 'Brazil', 'porto alegre': 'Brazil',
  'curitiba': 'Brazil', 'recife': 'Brazil', 'fortaleza': 'Brazil',
  'belo horizonte': 'Brazil', 'salvador': 'Brazil', 'manaus': 'Brazil',
  'campinas': 'Brazil', 'florianópolis': 'Brazil', 'goiânia': 'Brazil',
  // Latin America
  'buenos aires': 'Argentina', 'santiago': 'Chile', 'mexico city': 'Mexico',
  'bogotá': 'Colombia', 'lima': 'Peru', 'caracas': 'Venezuela', 'montevideo': 'Uruguay',
  // Canada
  'toronto': 'Canada', 'vancouver': 'Canada', 'montreal': 'Canada', 'montréal': 'Canada',
  'calgary': 'Canada', 'edmonton': 'Canada', 'ottawa': 'Canada', 'halifax': 'Canada',
  'winnipeg': 'Canada', 'québec city': 'Canada', 'quebec city': 'Canada',
  // United States
  'new york': 'United States', 'los angeles': 'United States', 'san francisco': 'United States',
  'chicago': 'United States', 'boston': 'United States', 'seattle': 'United States',
  'austin': 'United States', 'atlanta': 'United States', 'denver': 'United States',
  'miami': 'United States', 'philadelphia': 'United States', 'phoenix': 'United States',
  'dallas': 'United States', 'houston': 'United States', 'san diego': 'United States',
  'portland': 'United States', 'las vegas': 'United States', 'detroit': 'United States',
  'washington': 'United States', 'minneapolis': 'United States', 'pittsburgh': 'United States',
  // City abbreviations
  'nyc': 'United States', 'sf': 'United States', 'la': 'United States',
  'sea': 'United States', 'atl': 'United States', 'chi': 'United States',
  'phx': 'United States', 'pdx': 'United States',
  // South Africa
  'johannesburg': 'South Africa', 'cape town': 'South Africa', 'durban': 'South Africa', 'pretoria': 'South Africa',
};

const STATE_TO_COUNTRY: Record<string, string> = {
  // United States
  'california': 'United States', 'texas': 'United States', 'florida': 'United States',
  'new york': 'United States', 'washington': 'United States', 'massachusetts': 'United States',
  'illinois': 'United States', 'pennsylvania': 'United States', 'ohio': 'United States',
  'georgia': 'United States', 'colorado': 'United States', 'oregon': 'United States',
  // Brazil
  'minas gerais': 'Brazil', 'rio grande do sul': 'Brazil', 'pernambuco': 'Brazil',
  'ceará': 'Brazil', 'ceara': 'Brazil', 'distrito federal': 'Brazil', 'amazonas': 'Brazil',
  'santa catarina': 'Brazil', 'paraná': 'Brazil', 'parana': 'Brazil', 'bahia': 'Brazil',
  'rio de janeiro': 'Brazil', 'são paulo': 'Brazil', 'sao paulo': 'Brazil', 'goiás': 'Brazil',
  // India
  'maharashtra': 'India', 'telangana': 'India', 'tamil nadu': 'India', 'karnataka': 'India',
  'kerala': 'India', 'gujarat': 'India', 'uttar pradesh': 'India', 'rajasthan': 'India',
  'west bengal': 'India', 'madhya pradesh': 'India', 'haryana': 'India', 'punjab': 'India',
  // Canada
  'british columbia': 'Canada', 'ontario': 'Canada', 'quebec': 'Canada', 'québec': 'Canada',
  'alberta': 'Canada', 'manitoba': 'Canada', 'saskatchewan': 'Canada', 'nova scotia': 'Canada',
  'new brunswick': 'Canada', 'newfoundland': 'Canada',
  // Australia
  'new south wales': 'Australia', 'victoria': 'Australia', 'queensland': 'Australia',
  'south australia': 'Australia', 'western australia': 'Australia',
  'australian capital territory': 'Australia', 'tasmania': 'Australia', 'northern territory': 'Australia',
  // Germany
  'baden-württemberg': 'Germany', 'baden-wurttemberg': 'Germany', 'bayern': 'Germany', 'bavaria': 'Germany',
  'berlin': 'Germany', 'brandenburg': 'Germany', 'bremen': 'Germany', 'hamburg': 'Germany',
  'hessen': 'Germany', 'hesse': 'Germany', 'niedersachsen': 'Germany', 'lower saxony': 'Germany',
  'nordrhein-westfalen': 'Germany', 'north rhine-westphalia': 'Germany', 'rheinland-pfalz': 'Germany',
  'saarland': 'Germany', 'sachsen': 'Germany', 'saxony': 'Germany', 'schleswig-holstein': 'Germany',
  'thüringen': 'Germany', 'thuringia': 'Germany',
  // France
  'île-de-france': 'France', 'ile-de-france': 'France', 'provence-alpes-côte d\'azur': 'France',
  'auvergne-rhône-alpes': 'France', 'nouvelle-aquitaine': 'France', 'occitanie': 'France',
  'hauts-de-france': 'France', 'bretagne': 'France', 'brittany': 'France', 'normandie': 'France',
  // Italy
  'lombardia': 'Italy', 'lombardy': 'Italy', 'lazio': 'Italy', 'latium': 'Italy',
  'toscana': 'Italy', 'tuscany': 'Italy', 'emilia-romagna': 'Italy', 'veneto': 'Italy',
  'piemonte': 'Italy', 'piedmont': 'Italy', 'campania': 'Italy', 'sicilia': 'Italy', 'sicily': 'Italy',
  // Netherlands
  'noord-holland': 'Netherlands', 'zuid-holland': 'Netherlands', 'noord-brabant': 'Netherlands',
  'gelderland': 'Netherlands', 'overijssel': 'Netherlands', 'friesland': 'Netherlands',
  'provincie utrecht': 'Netherlands',
  // Poland
  'mazowieckie': 'Poland', 'śląskie': 'Poland', 'dolnośląskie': 'Poland',
  'małopolskie': 'Poland', 'wielkopolskie': 'Poland', 'pomorskie': 'Poland',
  // Mexico
  'nuevo león': 'Mexico', 'nuevo leon': 'Mexico', 'jalisco': 'Mexico', 'estado de méxico': 'Mexico',
  'mexico city': 'Mexico', 'ciudad de méxico': 'Mexico',
};

const COUNTRY_ALIASES: Record<string, string> = {
  // Language variations
  'brasil': 'Brazil', 'deutschland': 'Germany', 'nederland': 'Netherlands',
  'schweiz': 'Switzerland', 'suisse': 'Switzerland', 'svizzera': 'Switzerland',
  'österreich': 'Austria', 'oesterreich': 'Austria', 'españa': 'Spain', 'espana': 'Spain',
  'méxico': 'Mexico', 'mexico': 'Mexico', 'polska': 'Poland', 'france': 'France',
  'italia': 'Italy', 'italy': 'Italy',
  // Common abbreviations
  'usa': 'United States', 'us': 'United States', 'uk': 'United Kingdom',
  'uae': 'United Arab Emirates', 'uae': 'United Arab Emirates',
  // ISO codes that might be misused
  'il': 'Israel', 'nz': 'New Zealand', 'au': 'Australia', 'ca': 'Canada',
  'de': 'Germany', 'fr': 'France', 'nl': 'Netherlands', 'ch': 'Switzerland',
  'at': 'Austria', 'es': 'Spain', 'mx': 'Mexico', 'pl': 'Poland',
  'it': 'Italy', 'in': 'India', 'br': 'Brazil', 'ar': 'Argentina',
  'cl': 'Chile', 'co': 'Colombia', 'pe': 'Peru', 'za': 'South Africa',
};

/**
 * Aplica fallbacks inteligentes para corrigir erros comuns
 */
function applyIntelligentFallbacks(countryName: string): string {
    const normalized = countryName.toLowerCase().trim();

    // Ignore "Remote" and similar patterns
    if (/^(remote|anywhere|worldwide|global|flexible|hybrid)/i.test(normalized)) {
        return '';
    }

    // Ignore remote work prefixes/suffixes
    if (/^(us|uk|ca|au|eu|apac|emea|latam|americas|europe|asia)[\s\-](remote|nationwide|national)/i.test(normalized)) {
        return '';
    }
    if (/^remote[\s\-](us|uk|ca|au|in|de|fr|nl|it|es)/i.test(normalized)) {
        return '';
    }

    // Ignore regional aggregations
    if (/^(emea|apac|latam|americas|europe|asia|oceania|north america|south america|central america)$/i.test(normalized)) {
        return '';
    }

    // Ignore non-specific location markers
    if (/^(n\/a|tbd|tba|various|multiple|na)$/i.test(normalized)) {
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
