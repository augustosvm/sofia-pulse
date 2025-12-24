"""
Geographic Normalization Helpers for Python
Funções para obter países, estados e cidades normalizados

UPDATED 2025-12-23: Now uses normalized lookup functions instead of get_or_create
This prevents duplicates and ensures referential integrity with normalized tables.
"""

from typing import Optional
import psycopg2

# Support both relative and absolute imports
try:
    from .geo_id_helpers import get_country_id, get_state_id, get_city_id
except ImportError:
    from geo_id_helpers import get_country_id, get_state_id, get_city_id


def get_or_create_country(conn, country_name: Optional[str]) -> Optional[int]:
    """
    Obtém um país normalizado da tabela sofia.countries
    Tenta múltiplas estratégias: ISO codes, nome comum, etc.
    NÃO cria novos registros - apenas faz lookup
    """
    if not country_name or not country_name.strip():
        return None

    try:
        with conn.cursor() as cursor:
            return get_country_id(cursor, country_name.strip())
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
