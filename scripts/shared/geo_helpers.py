"""
Geographic Normalization Helpers for Python
Funções para obter países, estados e cidades normalizados

UPDATED 2025-12-23: Now uses normalized lookup functions instead of get_or_create
This prevents duplicates and ensures referential integrity with normalized tables.

UPDATED 2025-12-26: Added intelligent fallbacks for common mismatches
"""

from typing import Optional
import psycopg2
import re

# Support both relative and absolute imports
# Try different import methods to work in various contexts
try:
    # Method 1: Relative import (when used as package)
    from .geo_id_helpers import get_country_id, get_state_id, get_city_id
except (ImportError, ValueError):
    try:
        # Method 2: Absolute import from shared package
        from shared.geo_id_helpers import get_country_id, get_state_id, get_city_id
    except ImportError:
        # Method 3: Direct import (when script in same directory)
        from geo_id_helpers import get_country_id, get_state_id, get_city_id


# ============================================================================
# INTELLIGENT FALLBACKS - Maps common mistakes to correct countries
# ============================================================================

CITY_TO_COUNTRY = {
    # Germany
    'berlin': 'Germany', 'munich': 'Germany', 'hamburg': 'Germany', 'cologne': 'Germany',
    'frankfurt': 'Germany', 'stuttgart': 'Germany', 'dortmund': 'Germany', 'düsseldorf': 'Germany',
    'mannheim': 'Germany', 'nuremberg': 'Germany', 'bremen': 'Germany', 'leipzig': 'Germany',
    'dresden': 'Germany', 'hannover': 'Germany', 'duisburg': 'Germany', 'essen': 'Germany',
    'köln': 'Germany', 'nürnberg': 'Germany', 'frankfurt am main': 'Germany',
    # UK & Ireland
    'dublin': 'Ireland', 'london': 'United Kingdom', 'manchester': 'United Kingdom', 'birmingham': 'United Kingdom',
    # France
    'paris': 'France', 'lyon': 'France', 'marseille': 'France', 'toulouse': 'France',
    'bordeaux': 'France', 'lille': 'France', 'nantes': 'France', 'nice': 'France',
    'strasbourg': 'France', 'grenoble': 'France', 'montpellier': 'France',
    # Netherlands
    'amsterdam': 'Netherlands', 'rotterdam': 'Netherlands', 'utrecht': 'Netherlands',
    'eindhoven': 'Netherlands', 'groningen': 'Netherlands', 'delft': 'Netherlands',
    'arnhem': 'Netherlands', 'maastricht': 'Netherlands',
    # Spain
    'barcelona': 'Spain', 'madrid': 'Spain', 'valencia': 'Spain', 'sevilla': 'Spain',
    'seville': 'Spain', 'bilbao': 'Spain', 'málaga': 'Spain', 'zaragoza': 'Spain',
    # Switzerland
    'zürich': 'Switzerland', 'zurich': 'Switzerland', 'geneva': 'Switzerland', 'basel': 'Switzerland',
    'bern': 'Switzerland', 'lausanne': 'Switzerland', 'lucerne': 'Switzerland', 'zug': 'Switzerland',
    # Austria
    'vienna': 'Austria', 'wien': 'Austria', 'salzburg': 'Austria', 'graz': 'Austria', 'linz': 'Austria',
    # Italy
    'rome': 'Italy', 'milan': 'Italy', 'naples': 'Italy', 'turin': 'Italy', 'florence': 'Italy',
    # Poland
    'warsaw': 'Poland', 'kraków': 'Poland', 'krakow': 'Poland', 'gdańsk': 'Poland', 'wrocław': 'Poland',
    # India
    'bangalore': 'India', 'bengaluru': 'India', 'mumbai': 'India', 'delhi': 'India',
    'pune': 'India', 'hyderabad': 'India', 'chennai': 'India', 'kolkata': 'India',
    'noida': 'India', 'gurgaon': 'India', 'ahmedabad': 'India', 'jaipur': 'India',
    'kochi': 'India', 'trivandrum': 'India', 'thiruvananthapuram': 'India', 'madurai': 'India',
    'coimbatore': 'India', 'navi mumbai': 'India',
    # Asia-Pacific
    'singapore': 'Singapore', 'tokyo': 'Japan', 'seoul': 'South Korea', 'beijing': 'China',
    'shanghai': 'China', 'hong kong': 'Hong Kong', 'bangkok': 'Thailand', 'ho chi minh': 'Vietnam',
    'manila': 'Philippines', 'jakarta': 'Indonesia', 'kuala lumpur': 'Malaysia',
    # Australia
    'sydney': 'Australia', 'melbourne': 'Australia', 'brisbane': 'Australia',
    'perth': 'Australia', 'adelaide': 'Australia', 'canberra': 'Australia',
    'melbourne cbd': 'Australia', 'perth cbd': 'Australia', 'adelaide cbd': 'Australia',
    # New Zealand
    'auckland': 'New Zealand', 'wellington': 'New Zealand', 'christchurch': 'New Zealand',
    # Brazil
    'são paulo': 'Brazil', 'sao paulo': 'Brazil', 'rio de janeiro': 'Brazil',
    'brasilia': 'Brazil', 'brasília': 'Brazil', 'porto alegre': 'Brazil',
    'curitiba': 'Brazil', 'recife': 'Brazil', 'fortaleza': 'Brazil',
    'belo horizonte': 'Brazil', 'salvador': 'Brazil', 'manaus': 'Brazil',
    'campinas': 'Brazil', 'florianópolis': 'Brazil', 'goiânia': 'Brazil',
    # Latin America
    'buenos aires': 'Argentina', 'santiago': 'Chile', 'mexico city': 'Mexico',
    'bogotá': 'Colombia', 'lima': 'Peru', 'caracas': 'Venezuela', 'montevideo': 'Uruguay',
    # Canada
    'toronto': 'Canada', 'vancouver': 'Canada', 'montreal': 'Canada', 'montréal': 'Canada',
    'calgary': 'Canada', 'edmonton': 'Canada', 'ottawa': 'Canada', 'halifax': 'Canada',
    'winnipeg': 'Canada', 'québec city': 'Canada', 'quebec city': 'Canada',
    # United States
    'new york': 'United States', 'los angeles': 'United States', 'san francisco': 'United States',
    'chicago': 'United States', 'boston': 'United States', 'seattle': 'United States',
    'austin': 'United States', 'atlanta': 'United States', 'denver': 'United States',
    'miami': 'United States', 'philadelphia': 'United States', 'phoenix': 'United States',
    'dallas': 'United States', 'houston': 'United States', 'san diego': 'United States',
    'portland': 'United States', 'las vegas': 'United States', 'detroit': 'United States',
    'washington': 'United States', 'minneapolis': 'United States', 'pittsburgh': 'United States',
    # City abbreviations
    'nyc': 'United States', 'sf': 'United States', 'la': 'United States',
    'sea': 'United States', 'atl': 'United States', 'chi': 'United States',
    'phx': 'United States', 'pdx': 'United States',
    # South Africa
    'johannesburg': 'South Africa', 'cape town': 'South Africa', 'durban': 'South Africa', 'pretoria': 'South Africa',
}

STATE_TO_COUNTRY = {
    # United States
    'california': 'United States', 'texas': 'United States', 'florida': 'United States',
    'new york': 'United States', 'washington': 'United States', 'massachusetts': 'United States',
    'illinois': 'United States', 'pennsylvania': 'United States', 'ohio': 'United States',
    'georgia': 'United States', 'colorado': 'United States', 'oregon': 'United States',
    # Brazil
    'minas gerais': 'Brazil', 'rio grande do sul': 'Brazil', 'pernambuco': 'Brazil',
    'ceará': 'Brazil', 'ceara': 'Brazil', 'distrito federal': 'Brazil', 'amazonas': 'Brazil',
    'santa catarina': 'Brazil', 'paraná': 'Brazil', 'parana': 'Brazil', 'bahia': 'Brazil',
    'rio de janeiro': 'Brazil', 'são paulo': 'Brazil', 'sao paulo': 'Brazil', 'goiás': 'Brazil',
    # India
    'maharashtra': 'India', 'telangana': 'India', 'tamil nadu': 'India', 'karnataka': 'India',
    'kerala': 'India', 'gujarat': 'India', 'uttar pradesh': 'India', 'rajasthan': 'India',
    'west bengal': 'India', 'madhya pradesh': 'India', 'haryana': 'India', 'punjab': 'India',
    # Canada
    'british columbia': 'Canada', 'ontario': 'Canada', 'quebec': 'Canada', 'québec': 'Canada',
    'alberta': 'Canada', 'manitoba': 'Canada', 'saskatchewan': 'Canada', 'nova scotia': 'Canada',
    'new brunswick': 'Canada', 'newfoundland': 'Canada',
    # Australia
    'new south wales': 'Australia', 'victoria': 'Australia', 'queensland': 'Australia',
    'south australia': 'Australia', 'western australia': 'Australia',
    'australian capital territory': 'Australia', 'tasmania': 'Australia', 'northern territory': 'Australia',
    # Germany
    'baden-württemberg': 'Germany', 'baden-wurttemberg': 'Germany', 'bayern': 'Germany', 'bavaria': 'Germany',
    'berlin': 'Germany', 'brandenburg': 'Germany', 'bremen': 'Germany', 'hamburg': 'Germany',
    'hessen': 'Germany', 'hesse': 'Germany', 'niedersachsen': 'Germany', 'lower saxony': 'Germany',
    'nordrhein-westfalen': 'Germany', 'north rhine-westphalia': 'Germany', 'rheinland-pfalz': 'Germany',
    'saarland': 'Germany', 'sachsen': 'Germany', 'saxony': 'Germany', 'schleswig-holstein': 'Germany',
    'thüringen': 'Germany', 'thuringia': 'Germany',
    # France
    'île-de-france': 'France', 'ile-de-france': 'France', 'provence-alpes-côte d\'azur': 'France',
    'auvergne-rhône-alpes': 'France', 'nouvelle-aquitaine': 'France', 'occitanie': 'France',
    'hauts-de-france': 'France', 'bretagne': 'France', 'brittany': 'France', 'normandie': 'France',
    # Italy
    'lombardia': 'Italy', 'lombardy': 'Italy', 'lazio': 'Italy', 'latium': 'Italy',
    'toscana': 'Italy', 'tuscany': 'Italy', 'emilia-romagna': 'Italy', 'veneto': 'Italy',
    'piemonte': 'Italy', 'piedmont': 'Italy', 'campania': 'Italy', 'sicilia': 'Italy', 'sicily': 'Italy',
    # Netherlands
    'noord-holland': 'Netherlands', 'zuid-holland': 'Netherlands', 'noord-brabant': 'Netherlands',
    'gelderland': 'Netherlands', 'overijssel': 'Netherlands', 'friesland': 'Netherlands',
    'provincie utrecht': 'Netherlands',
    # Poland
    'mazowieckie': 'Poland', 'śląskie': 'Poland', 'dolnośląskie': 'Poland',
    'małopolskie': 'Poland', 'wielkopolskie': 'Poland', 'pomorskie': 'Poland',
    # Mexico
    'nuevo león': 'Mexico', 'nuevo leon': 'Mexico', 'jalisco': 'Mexico', 'estado de méxico': 'Mexico',
    'mexico city': 'Mexico', 'ciudad de méxico': 'Mexico',
}

COUNTRY_ALIASES = {
    # Language variations
    'brasil': 'Brazil', 'deutschland': 'Germany', 'nederland': 'Netherlands',
    'schweiz': 'Switzerland', 'suisse': 'Switzerland', 'svizzera': 'Switzerland',
    'österreich': 'Austria', 'oesterreich': 'Austria', 'españa': 'Spain', 'espana': 'Spain',
    'méxico': 'Mexico', 'mexico': 'Mexico', 'polska': 'Poland', 'france': 'France',
    'italia': 'Italy', 'italy': 'Italy',
    # Common abbreviations
    'usa': 'United States', 'us': 'United States', 'uk': 'United Kingdom',
    'uae': 'United Arab Emirates',
    # ISO codes that might be misused
    'il': 'Israel', 'nz': 'New Zealand', 'au': 'Australia', 'ca': 'Canada',
    'de': 'Germany', 'fr': 'France', 'nl': 'Netherlands', 'ch': 'Switzerland',
    'at': 'Austria', 'es': 'Spain', 'mx': 'Mexico', 'pl': 'Poland',
    'it': 'Italy', 'in': 'India', 'br': 'Brazil', 'ar': 'Argentina',
    'cl': 'Chile', 'co': 'Colombia', 'pe': 'Peru', 'za': 'South Africa',
}


def apply_intelligent_fallbacks(country_name: str) -> str:
    """Aplica fallbacks inteligentes para corrigir erros comuns"""
    normalized = country_name.lower().strip()

    # Ignore "Remote" and similar patterns
    if re.match(r'^(remote|anywhere|worldwide|global|flexible|hybrid)', normalized, re.IGNORECASE):
        return ''

    # Ignore remote work prefixes/suffixes
    if re.match(r'^(us|uk|ca|au|eu|apac|emea|latam|americas|europe|asia)[\s\-](remote|nationwide|national)', normalized, re.IGNORECASE):
        return ''
    if re.match(r'^remote[\s\-](us|uk|ca|au|in|de|fr|nl|it|es)', normalized, re.IGNORECASE):
        return ''

    # Ignore regional aggregations
    if re.match(r'^(emea|apac|latam|americas|europe|asia|oceania|north america|south america|central america)$', normalized, re.IGNORECASE):
        return ''

    # Ignore non-specific location markers
    if re.match(r'^(n/a|tbd|tba|various|multiple|na)$', normalized, re.IGNORECASE):
        return ''

    # Try alias first
    if normalized in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[normalized]

    # Try city to country
    if normalized in CITY_TO_COUNTRY:
        return CITY_TO_COUNTRY[normalized]

    # Try state to country
    if normalized in STATE_TO_COUNTRY:
        return STATE_TO_COUNTRY[normalized]

    # Return original if no fallback found
    return country_name


def get_or_create_country(conn, country_name: Optional[str]) -> Optional[int]:
    """
    Obtém um país normalizado da tabela sofia.countries
    Tenta múltiplas estratégias: ISO codes, nome comum, fallbacks inteligentes
    NÃO cria novos registros - apenas faz lookup
    """
    if not country_name or not country_name.strip():
        return None

    # Apply intelligent fallbacks first
    corrected_name = apply_intelligent_fallbacks(country_name.strip())
    if not corrected_name:
        return None  # "Remote" etc

    try:
        with conn.cursor() as cursor:
            return get_country_id(cursor, corrected_name)
    except Exception as e:
        print(f'Erro ao normalizar país "{country_name}": {e}')
        return None


def get_or_create_state(
    conn,
    state_name: Optional[str],
    country_id: Optional[int]
) -> Optional[int]:
    """
    Obtém um estado normalizado da tabela sofia.states
    Busca por código (2 letras) ou nome dentro do país especificado
    NÃO cria novos registros - apenas faz lookup
    """
    if not state_name or not state_name.strip() or not country_id:
        return None

    try:
        with conn.cursor() as cursor:
            return get_state_id(cursor, state_name.strip(), country_id)
    except Exception as e:
        print(f'Erro ao normalizar estado "{state_name}": {e}')
        return None


def get_or_create_city(
    conn,
    city_name: Optional[str],
    state_id: Optional[int],
    country_id: Optional[int]
) -> Optional[int]:
    """
    Obtém uma cidade normalizada da tabela sofia.cities
    Busca por nome dentro do estado/país especificado
    NÃO cria novos registros - apenas faz lookup
    """
    if not city_name or not city_name.strip() or not country_id:
        return None

    try:
        with conn.cursor() as cursor:
            return get_city_id(cursor, city_name.strip(), state_id, country_id)
    except Exception as e:
        print(f'Erro ao normalizar cidade "{city_name}": {e}')
        return None


def normalize_location(conn, location: dict) -> dict:
    """
    Normaliza uma localização completa (país, estado, cidade)
    Retorna os IDs normalizados

    Args:
        location: dict com keys 'country', 'state', 'city'

    Returns:
        dict com keys 'country_id', 'state_id', 'city_id'
    """
    country_id = get_or_create_country(conn, location.get('country'))
    state_id = get_or_create_state(conn, location.get('state'), country_id)
    city_id = get_or_create_city(conn, location.get('city'), state_id, country_id)

    return {
        'country_id': country_id,
        'state_id': state_id,
        'city_id': city_id
    }
