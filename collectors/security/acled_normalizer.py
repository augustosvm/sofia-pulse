#!/usr/bin/env python3
"""
ACLED Normalizer - Security Layer
Normalizes acled_aggregated data into security_events table
Maps country names to country_id and ensures proper geo data
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import psycopg2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('acled_normalizer')

# Database config
DB_CONFIG = {
    'host': os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', '91.98.158.19')),
    'port': os.getenv('DB_PORT', os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'sofia')),
    'password': os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', 'SofiaPulse2025Secure@DB')),
    'database': os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'sofia_db'))
}

# Country name variations mapping to ISO2
COUNTRY_NAME_TO_ISO2 = {
    'United States': 'US',
    'United States of America': 'US',
    'USA': 'US',
    'United Kingdom': 'GB',
    'UK': 'GB',
    'Russia': 'RU',
    'Russian Federation': 'RU',
    'South Korea': 'KR',
    'Republic of Korea': 'KR',
    'North Korea': 'KP',
    'Democratic Republic of Congo': 'CD',
    'DRC': 'CD',
    'DR Congo': 'CD',
    'Republic of the Congo': 'CG',
    'Congo': 'CG',
    'Ivory Coast': 'CI',
    "Cote d'Ivoire": 'CI',
    'Czech Republic': 'CZ',
    'Czechia': 'CZ',
    'Syria': 'SY',
    'Syrian Arab Republic': 'SY',
    'Iran': 'IR',
    'Venezuela': 'VE',
    'Bolivia': 'BO',
    'Tanzania': 'TZ',
    'Vietnam': 'VN',
    'Laos': 'LA',
    'Myanmar': 'MM',
    'Burma': 'MM',
    'Palestine': 'PS',
    'Taiwan': 'TW',
    'Macau': 'MO',
    'Hong Kong': 'HK',
    'British Indian Ocean Territory': 'IO',
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def build_country_mapping(conn) -> Tuple[Dict[str, int], Dict[str, str]]:
    """Build country name -> id and country name -> iso2 mappings"""
    cursor = conn.cursor()

    # Get all countries with their names and codes
    cursor.execute("""
        SELECT id, common_name, iso_alpha2
        FROM sofia.countries
        WHERE common_name IS NOT NULL
    """)

    name_to_id = {}
    name_to_iso2 = {}

    for row in cursor.fetchall():
        country_id, name, iso2 = row
        if name:
            name_lower = name.lower().strip()
            name_to_id[name_lower] = country_id
            name_to_iso2[name_lower] = iso2

    cursor.close()

    # Add manual overrides
    for name_var, iso2 in COUNTRY_NAME_TO_ISO2.items():
        name_lower = name_var.lower().strip()
        # Find id for this iso2
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM sofia.countries WHERE iso_alpha2 = %s", (iso2,))
        result = cursor.fetchone()
        if result:
            name_to_id[name_lower] = result[0]
            name_to_iso2[name_lower] = iso2
        cursor.close()

    return name_to_id, name_to_iso2


def generate_source_id(row: Dict) -> str:
    """Generate deterministic source_id for ACLED aggregated record"""
    key = f"{row['week']}_{row['country']}_{row['latitude']}_{row['longitude']}_{row['event_type']}"
    return hashlib.md5(key.encode()).hexdigest()[:16]


def normalize_acled_to_security(batch_size: int = 5000) -> int:
    """Normalize acled_aggregated into security_events"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build country mappings
    logger.info("Building country mappings...")
    name_to_id, name_to_iso2 = build_country_mapping(conn)
    logger.info(f"Loaded {len(name_to_id)} country name mappings")

    # Count total records
    cursor.execute("SELECT COUNT(*) FROM sofia.acled_aggregated")
    total = cursor.fetchone()[0]
    logger.info(f"Total ACLED aggregated records: {total}")

    # Process in batches
    offset = 0
    inserted = 0
    updated_country_ids = 0

    while offset < total:
        cursor.execute("""
            SELECT id, week, region, country, admin1, event_type, sub_event_type,
                   events, fatalities, population_exposure, disorder_type,
                   centroid_latitude, centroid_longitude, source_file, country_id
            FROM sofia.acled_aggregated
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (batch_size, offset))

        rows = cursor.fetchall()
        if not rows:
            break

        for row in rows:
            try:
                record = {
                    'id': row[0],
                    'week': row[1],
                    'region': row[2],
                    'country': row[3],
                    'admin1': row[4],
                    'event_type': row[5],
                    'sub_event_type': row[6],
                    'events': row[7] or 1,
                    'fatalities': row[8] or 0,
                    'population_exposure': row[9],
                    'disorder_type': row[10],
                    'latitude': float(row[11]) if row[11] else None,
                    'longitude': float(row[12]) if row[12] else None,
                    'source_file': row[13],
                    'existing_country_id': row[14]
                }

                # Skip if no geo
                if not record['latitude'] or not record['longitude']:
                    continue

                # Generate source_id
                source_id = generate_source_id(record)

                # Map country
                country_lower = (record['country'] or '').lower().strip()
                country_id = name_to_id.get(country_lower)
                country_code = name_to_iso2.get(country_lower)

                # Calculate severity
                fatalities = record['fatalities'] or 0
                event_count = record['events'] or 1
                severity = fatalities if fatalities > 0 else event_count

                # Insert into security_events
                cursor.execute("""
                    INSERT INTO sofia.security_events
                    (source, source_id, event_date, week_start, country_name, country_code,
                     country_id, admin1, latitude, longitude, event_type, sub_event_type,
                     severity_score, fatalities, event_count, raw_payload)
                    VALUES ('ACLED', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source, source_id) DO UPDATE SET
                        severity_score = EXCLUDED.severity_score,
                        fatalities = EXCLUDED.fatalities,
                        event_count = EXCLUDED.event_count,
                        country_id = EXCLUDED.country_id,
                        ingested_at = now()
                """, (
                    source_id,
                    record['week'],  # event_date = week start
                    record['week'],  # week_start
                    record['country'],
                    country_code,
                    country_id,
                    record['admin1'],
                    record['latitude'],
                    record['longitude'],
                    record['event_type'],
                    record['sub_event_type'],
                    severity,
                    record['fatalities'],
                    record['events'],
                    json.dumps({
                        'region': record['region'],
                        'disorder_type': record['disorder_type'],
                        'population_exposure': record['population_exposure'],
                        'source_file': record['source_file']
                    })
                ))
                inserted += 1

                # Also update country_id in acled_aggregated if missing
                if country_id and not record['existing_country_id']:
                    cursor.execute("""
                        UPDATE sofia.acled_aggregated
                        SET country_id = %s
                        WHERE id = %s AND country_id IS NULL
                    """, (country_id, record['id']))
                    updated_country_ids += 1

            except Exception as e:
                logger.warning(f"Error processing record {row[0]}: {e}")
                continue

        conn.commit()
        offset += batch_size
        logger.info(f"Processed {min(offset, total)}/{total} records...")

    cursor.close()
    conn.close()

    return inserted, updated_country_ids


def refresh_views():
    """Refresh materialized views"""
    conn = get_db_connection()
    cursor = conn.cursor()

    logger.info("Refreshing materialized views...")

    try:
        cursor.execute("REFRESH MATERIALIZED VIEW sofia.mv_security_country_summary")
        cursor.execute("REFRESH MATERIALIZED VIEW sofia.mv_security_geo_points_30d")
        cursor.execute("REFRESH MATERIALIZED VIEW sofia.mv_security_momentum")
        conn.commit()
        logger.info("Views refreshed successfully")
    except Exception as e:
        logger.error(f"Error refreshing views: {e}")
        conn.rollback()

    cursor.close()
    conn.close()


def main():
    logger.info("=" * 60)
    logger.info("ACLED Normalizer - Security Layer")
    logger.info("=" * 60)

    # Normalize data
    inserted, updated_ids = normalize_acled_to_security()

    logger.info(f"\nResults:")
    logger.info(f"  Inserted/updated in security_events: {inserted}")
    logger.info(f"  Updated country_id in acled_aggregated: {updated_ids}")

    # Refresh views
    refresh_views()

    # Summary stats
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT source, COUNT(*), COUNT(latitude), COUNT(country_id)
        FROM sofia.security_events
        GROUP BY source
    """)

    logger.info("\nSecurity Events Summary:")
    for row in cursor.fetchall():
        logger.info(f"  {row[0]}: {row[1]} total, {row[2]} with geo, {row[3]} with country_id")

    cursor.close()
    conn.close()

    logger.info("=" * 60)
    logger.info("Normalization complete")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
