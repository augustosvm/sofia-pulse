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
}

STATE_TO_COUNTRY = {
    'california': 'United States', 'texas': 'United States',
    'florida': 'United States', 'new york': 'United States',
}

COUNTRY_ALIASES = {
    'brasil': 'Brazil', 'usa': 'United States', 'us': 'United States',
    'uk': 'United Kingdom', 'uae': 'United Arab Emirates',
}


def apply_intelligent_fallbacks(country_name: str) -> str:
    """Aplica fallbacks inteligentes para corrigir erros comuns"""
    normalized = country_name.lower().strip()

    # Ignore "Remote" and similar
    if re.match(r'^(remote|anywhere|worldwide|global)$', normalized, re.IGNORECASE):
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
