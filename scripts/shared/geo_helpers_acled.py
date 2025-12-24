"""
Geographic Normalization Helpers for Python - ACLED Version
Funções para obter/criar países, estados e cidades normalizados
"""

from typing import Optional
import psycopg2


def normalize_location_acled(conn, country: Optional[str], location: Optional[str]) -> dict:
    """
    Normaliza localização do ACLED (país e cidade)
    
    Args:
        conn: Conexão psycopg2
        country: Nome do país
        location: Nome da localização/cidade
    
    Returns:
        dict com keys 'country_id', 'city_id'
    """
    country_id = None
    city_id = None
    
    # Normalizar país
    if country and country.strip():
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT get_or_create_country(%s) as country_id",
                    (country.strip(),)
                )
                result = cur.fetchone()
                country_id = result[0] if result else None
        except Exception as e:
            print(f'Erro ao normalizar país "{country}": {e}')
    
    # Normalizar cidade (se temos país)
    if location and location.strip() and country_id:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT get_or_create_city(%s, NULL, %s) as city_id",
                    (location.strip(), country_id)
                )
                result = cur.fetchone()
                city_id = result[0] if result else None
        except Exception as e:
            print(f'Erro ao normalizar cidade "{location}": {e}')
    
    return {
        'country_id': country_id,
        'city_id': city_id
    }
