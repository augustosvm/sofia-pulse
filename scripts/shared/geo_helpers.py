"""
Geographic Normalization Helpers for Python
Funções para obter/criar países, estados e cidades normalizados
"""

from typing import Optional
import psycopg2


def get_or_create_country(conn, country_name: Optional[str]) -> Optional[int]:
    """
    Obtém ou cria um país normalizado
    Usa a função SQL get_or_create_country()
    """
    if not country_name or not country_name.strip():
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT get_or_create_country(%s) as country_id",
                (country_name.strip(),)
            )
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f'Erro ao normalizar país "{country_name}": {e}')
        return None


def get_or_create_state(
    conn,
    state_name: Optional[str],
    country_id: Optional[int]
) -> Optional[int]:
    """
    Obtém ou cria um estado normalizado
    Usa a função SQL get_or_create_state()
    """
    if not state_name or not state_name.strip() or not country_id:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT get_or_create_state(%s, %s) as state_id",
                (state_name.strip(), country_id)
            )
            result = cur.fetchone()
            return result[0] if result else None
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
    Obtém ou cria uma cidade normalizada
    Usa a função SQL get_or_create_city()
    """
    if not city_name or not city_name.strip() or not country_id:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT get_or_create_city(%s, %s, %s) as city_id",
                (city_name.strip(), state_id, country_id)
            )
            result = cur.fetchone()
            return result[0] if result else None
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
