#!/usr/bin/env python3
"""
ACLED Normalizer V3 - Security Layer
Normalizes acled_aggregated.regional data into sofia.security_events table
Works with ACLED V3 collector (multi-region support)
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('acled_normalizer_v3')

# Database config
DB_CONFIG = {
    'host': os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', '91.98.158.19')),
    'port': os.getenv('DB_PORT', os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'dbs_sofia')),
    'password': os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', '')),
    'database': os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'sofia'))
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def normalize_acled_regional_to_security(batch_size: int = 5000) -> int:
    """
    Normalize acled_aggregated.regional into sofia.security_events
    Regional table has geo coordinates (centroid) - perfect for map visualization
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Count total records in regional table
    cursor.execute("SELECT COUNT(*) FROM acled_aggregated.regional")
    total = cursor.fetchone()[0]
    logger.info(f"Total ACLED regional records: {total}")

    if total == 0:
        logger.warning("No data in acled_aggregated.regional table!")
        logger.info("Run: python3 scripts/collect-acled-aggregated-postgres-v3.py first")
        cursor.close()
        conn.close()
        return 0

    # Clear existing ACLED data in security_events (fresh start)
    logger.info("Clearing existing ACLED data from sofia.security_events...")
    cursor.execute("DELETE FROM sofia.security_events WHERE source = 'ACLED'")
    deleted = cursor.rowcount
    logger.info(f"Deleted {deleted} existing ACLED records")
    conn.commit()

    # Process in batches
    offset = 0
    inserted = 0
    skipped = 0

    while offset < total:
        cursor.execute("""
            SELECT
                dataset_slug,
                country,
                admin1,
                admin2,
                year,
                month,
                week,
                centroid_latitude,
                centroid_longitude,
                event_type,
                events,
                fatalities,
                disorder_type,
                metadata,
                collected_at
            FROM acled_aggregated.regional
            ORDER BY collected_at DESC, year DESC, month DESC
            LIMIT %s OFFSET %s
        """, (batch_size, offset))

        rows = cursor.fetchall()
        if not rows:
            break

        batch_data = []

        for row in rows:
            try:
                (dataset_slug, country, admin1, admin2, year, month, week,
                 lat, lon, event_type, events, fatalities,
                 disorder_type, metadata, collected_at) = row

                # Skip if no geo
                if not lat or not lon:
                    skipped += 1
                    continue

                # Generate deterministic source_id
                key = f"acled_v3_{dataset_slug}_{country}_{admin1 or ''}_{admin2 or ''}_{year}_{month}_{week}_{lat}_{lon}_{event_type}"
                source_id = hashlib.md5(key.encode()).hexdigest()

                # Calculate event_date from year/month/week
                if week and year:
                    # week is INTEGER (1-53), convert to date
                    try:
                        event_date = datetime.strptime(f'{year}-W{week:02d}-1', '%Y-W%W-%w').date()
                    except:
                        # Fallback: use year-month-01
                        event_date = datetime(year, month or 1, 1).date()
                else:
                    event_date = datetime(year or 2024, month or 1, 1).date()

                # Normalize country name and get country code (simple heuristic)
                country_name = country or 'Unknown'
                # TODO: Map to ISO2/ISO3 codes from dim_country table

                # Calculate severity
                fatalities_val = int(fatalities) if fatalities else 0
                events_val = int(events) if events else 1
                severity = fatalities_val if fatalities_val > 0 else events_val

                # Prepare metadata
                raw_payload = {
                    'dataset_slug': dataset_slug,
                    'admin1': admin1,
                    'admin2': admin2,
                    'disorder_type': disorder_type,
                    'source_metadata': metadata,
                    'collected_at': collected_at.isoformat() if collected_at else None
                }

                batch_data.append((
                    'ACLED',
                    source_id,
                    event_date,
                    country_name,
                    None,  # country_code (TODO: map from dim_country)
                    lat,
                    lon,
                    event_type or 'Unknown',
                    fatalities_val,
                    json.dumps(raw_payload)
                ))

            except Exception as e:
                logger.warning(f"Error processing record: {e}")
                skipped += 1
                continue

        # Bulk insert
        if batch_data:
            execute_values(cursor, """
                INSERT INTO sofia.security_events
                (source, source_id, event_date, country_name, country_code,
                 latitude, longitude, event_type, fatalities, raw_payload)
                VALUES %s
                ON CONFLICT (source, source_id) DO NOTHING
            """, batch_data)

            inserted += len(batch_data)
            conn.commit()

        offset += batch_size
        logger.info(f"Processed {min(offset, total)}/{total} records... (inserted: {inserted}, skipped: {skipped})")

    cursor.close()
    conn.close()

    return inserted


def refresh_views():
    """Refresh materialized views"""
    conn = get_db_connection()
    cursor = conn.cursor()

    logger.info("Refreshing materialized views...")

    try:
        # Use new hybrid refresh function if available, otherwise fallback to old views
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc WHERE proname = 'refresh_security_hybrid_views'
            )
        """)
        has_hybrid = cursor.fetchone()[0]

        if has_hybrid:
            logger.info("Using sofia.refresh_security_hybrid_views()")
            cursor.execute("SELECT sofia.refresh_security_hybrid_views()")
        else:
            logger.info("Using legacy refresh (individual views)")
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_security_country_summary")
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_security_geo_points")
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY sofia.mv_security_momentum")

        conn.commit()
        logger.info("Views refreshed successfully")
    except Exception as e:
        logger.error(f"Error refreshing views: {e}")
        conn.rollback()
        raise

    cursor.close()
    conn.close()


def main():
    logger.info("=" * 60)
    logger.info("ACLED Normalizer V3 - Security Layer")
    logger.info("Reads from: acled_aggregated.regional (V3 schema)")
    logger.info("Writes to: sofia.security_events")
    logger.info("=" * 60)

    # Normalize data
    inserted = normalize_acled_regional_to_security()

    logger.info(f"\nResults:")
    logger.info(f"  Inserted into security_events: {inserted}")

    if inserted == 0:
        logger.warning("\n⚠️  No data was inserted!")
        logger.info("Make sure you ran: python3 scripts/collect-acled-aggregated-postgres-v3.py")
        sys.exit(1)

    # Refresh views
    refresh_views()

    # Summary stats
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(latitude) as with_geo,
            COUNT(DISTINCT country_name) as countries,
            MIN(event_date) as earliest,
            MAX(event_date) as latest
        FROM sofia.security_events
        WHERE source = 'ACLED'
    """)

    row = cursor.fetchone()
    logger.info("\n✅ Security Events Summary (ACLED):")
    logger.info(f"  Total records: {row[0]}")
    logger.info(f"  With geo: {row[1]}")
    logger.info(f"  Countries: {row[2]}")
    logger.info(f"  Date range: {row[3]} to {row[4]}")

    # Sample countries
    cursor.execute("""
        SELECT country_name, COUNT(*) as events
        FROM sofia.security_events
        WHERE source = 'ACLED' AND latitude IS NOT NULL
        GROUP BY country_name
        ORDER BY COUNT(*) DESC
        LIMIT 20
    """)

    logger.info("\n📊 Top 20 countries by events:")
    for row in cursor.fetchall():
        logger.info(f"  {row[0]}: {row[1]} events")

    cursor.close()
    conn.close()

    logger.info("\n=" * 60)
    logger.info("✅ Normalization complete!")
    logger.info("Next: Reload your map at http://172.27.140.239:3001/map")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
