"""
Geographic ID Helpers (Python)

Helper functions for Python collectors to lookup normalized geographic IDs.

USAGE in Python collectors:
```python
from scripts.shared.geo_id_helpers import get_country_id, get_state_id, get_city_id

country_id = get_country_id(cursor, 'United States')  # or 'US' or 'USA'
state_id = get_state_id(cursor, 'California', country_id)
city_id = get_city_id(cursor, 'San Francisco', state_id, country_id)

# Then INSERT with IDs:
cursor.execute('''
    INSERT INTO sofia.jobs (title, company, country_id, state_id, city_id)
    VALUES (%s, %s, %s, %s, %s)
''', (title, company, country_id, state_id, city_id))
```
"""

from typing import Optional

# Eurostat-specific country code mappings
EUROSTAT_MAPPINGS = {
    "EL": "GR",  # Greece
    "UK": "GB",  # United Kingdom
}


def get_country_id(cursor, country_input: Optional[str]) -> Optional[int]:
    """
    Get country ID from normalized countries table.
    Tries multiple strategies: ISO alpha2, ISO alpha3, common name.

    Args:
        cursor: Database cursor
        country_input: Country code or name (e.g., 'US', 'USA', 'United States')

    Returns:
        Country ID or None if not found
    """
    if not country_input:
        return None

    country = country_input.strip()

    # Strategy 1: Try ISO alpha2 (US, BR, GB, etc.)
    if len(country) == 2:
        cursor.execute("SELECT id FROM sofia.countries WHERE iso_alpha2 = %s", (country.upper(),))
        result = cursor.fetchone()
        if result:
            return result[0]

    # Strategy 2: Try ISO alpha3 (USA, BRA, GBR, etc.)
    if len(country) == 3:
        cursor.execute("SELECT id FROM sofia.countries WHERE iso_alpha3 = %s", (country.upper(),))
        result = cursor.fetchone()
        if result:
            return result[0]

    # Strategy 3: Try common name (case-insensitive)
    cursor.execute("SELECT id FROM sofia.countries WHERE LOWER(common_name) = LOWER(%s)", (country,))
    result = cursor.fetchone()
    if result:
        return result[0]

    # Strategy 4: Try Eurostat-specific codes
    if country.upper() in EUROSTAT_MAPPINGS:
        mapped_code = EUROSTAT_MAPPINGS[country.upper()]
        cursor.execute("SELECT id FROM sofia.countries WHERE iso_alpha2 = %s", (mapped_code,))
        result = cursor.fetchone()
        if result:
            return result[0]

    print(f'⚠️  Country not found: "{country}"')
    return None


def get_state_id(cursor, state_name: Optional[str], country_id: Optional[int]) -> Optional[int]:
    """
    Get state ID from normalized states table.

    Args:
        cursor: Database cursor
        state_name: State name or code (e.g., 'California', 'CA')
        country_id: Country ID to narrow search

    Returns:
        State ID or None if not found
    """
    if not state_name or not country_id:
        return None

    state = state_name.strip()

    # Try by state code (e.g., "CA" for California)
    if len(state) == 2:
        cursor.execute("SELECT id FROM sofia.states WHERE code = %s AND country_id = %s", (state.upper(), country_id))
        result = cursor.fetchone()
        if result:
            return result[0]

    # Try by state name (case-insensitive)
    cursor.execute("SELECT id FROM sofia.states WHERE LOWER(name) = LOWER(%s) AND country_id = %s", (state, country_id))
    result = cursor.fetchone()
    if result:
        return result[0]

    print(f'⚠️  State not found: "{state}" in country {country_id}')
    return None


def get_city_id(cursor, city_name: Optional[str], state_id: Optional[int], country_id: Optional[int]) -> Optional[int]:
    """
    Get city ID from normalized cities table.

    Args:
        cursor: Database cursor
        city_name: City name
        state_id: State ID to narrow search (optional)
        country_id: Country ID to narrow search (optional)

    Returns:
        City ID or None if not found
    """
    if not city_name:
        return None

    city = city_name.strip()

    # Try with state_id if available
    if state_id:
        cursor.execute("SELECT id FROM sofia.cities WHERE LOWER(name) = LOWER(%s) AND state_id = %s", (city, state_id))
        result = cursor.fetchone()
        if result:
            return result[0]

    # Try with only country_id
    if country_id:
        cursor.execute(
            "SELECT id FROM sofia.cities WHERE LOWER(name) = LOWER(%s) AND country_id = %s", (city, country_id)
        )
        result = cursor.fetchone()
        if result:
            return result[0]

    # Try without any parent (last resort)
    cursor.execute("SELECT id FROM sofia.cities WHERE LOWER(name) = LOWER(%s) LIMIT 1", (city,))
    result = cursor.fetchone()
    if result:
        return result[0]

    print(f'⚠️  City not found: "{city}"')
    return None


def get_religion_id(cursor, religion_name: Optional[str]) -> Optional[int]:
    """
    Get religion ID from normalized religions table.

    Args:
        cursor: Database cursor
        religion_name: Religion name (e.g., 'Christian', 'Muslim')

    Returns:
        Religion ID or None if not found
    """
    if not religion_name:
        return None

    religion = religion_name.strip()

    cursor.execute("SELECT id FROM sofia.religions WHERE LOWER(name) = LOWER(%s)", (religion,))
    result = cursor.fetchone()
    if result:
        return result[0]

    print(f'⚠️  Religion not found: "{religion}"')
    return None


def get_country_ids_batch(cursor) -> dict:
    """
    Batch load all countries into a dictionary for fast lookups.
    More efficient than calling get_country_id repeatedly.

    Returns:
        Dictionary mapping country codes/names to IDs
    """
    country_map = {}

    cursor.execute(
        """
        SELECT iso_alpha2, iso_alpha3, LOWER(common_name) as name_lower, id
        FROM sofia.countries
    """
    )

    for row in cursor.fetchall():
        iso_alpha2, iso_alpha3, name_lower, country_id = row
        country_map[iso_alpha2] = country_id
        country_map[iso_alpha3] = country_id
        country_map[name_lower] = country_id

    return country_map
