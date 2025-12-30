#!/usr/bin/env python3
"""
Sofia Pulse - Collector Template with Full Reliability
This is a reference implementation showing how to use all reliability features
"""

import os
import sys
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database imports
import psycopg2
import psycopg2.extras

from scripts.utils.alerts import alert_collector_failed, alert_data_anomaly

# Import reliability utilities
from scripts.utils.logger import (
    log_collector_error,
    log_collector_finish,
    log_collector_start,
    setup_logger,
)
from scripts.utils.retry import retry_with_backoff, safe_request

# Collector configuration
COLLECTOR_NAME = "example-collector"
MIN_EXPECTED_ROWS = 10  # Alert if less than this


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "sofia"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "sofia"),
    )


@retry_with_backoff(max_retries=5)
def fetch_data_from_api():
    """
    Fetch data from external API with automatic retry

    This decorator will automatically retry up to 5 times with exponential backoff
    """
    url = "https://api.example.com/data"

    # Use safe_request for automatic retry and rate limit handling
    response = safe_request(url, max_retries=5, timeout=15)

    if response is None:
        raise Exception("Failed to fetch data after all retries")

    if response.status_code != 200:
        raise Exception(f"API returned {response.status_code}")

    return response.json()


def insert_data_safely(data, logger):
    """
    Insert data with transaction safety (guaranteed delivery)

    Uses temporary table to ensure atomicity:
    - If insert fails, no partial data is committed
    - If insert succeeds, old data is replaced atomically
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Step 1: Create temporary table
        cursor.execute(
            """
            CREATE TEMP TABLE temp_example_data (
                id SERIAL PRIMARY KEY,
                name TEXT,
                value FLOAT,
                collected_at TIMESTAMP DEFAULT NOW()
            )
        """
        )

        # Step 2: Insert all data into temp table
        logger.info(f"Inserting {len(data)} rows into temp table...")

        for item in data:
            cursor.execute(
                """
                INSERT INTO temp_example_data (name, value)
                VALUES (%s, %s)
            """,
                (item["name"], item["value"]),
            )

        # Step 3: Verify data in temp table
        cursor.execute("SELECT COUNT(*) FROM temp_example_data")
        temp_count = cursor.fetchone()[0]

        logger.info(f"Inserted {temp_count} rows into temp table")

        if temp_count == 0:
            logger.warning("Zero rows inserted - skipping commit")
            alert_data_anomaly("example_data", "ZERO_ROWS", f"Expected {MIN_EXPECTED_ROWS}+, got 0")
            conn.rollback()
            return 0

        # Step 4: Begin transaction - delete old data and insert new
        cursor.execute("BEGIN")
        cursor.execute("DELETE FROM example_data WHERE DATE(collected_at) = CURRENT_DATE")

        deleted_count = cursor.rowcount
        logger.info(f"Deleted {deleted_count} old rows")

        cursor.execute("INSERT INTO example_data SELECT * FROM temp_example_data")
        cursor.execute("COMMIT")

        logger.info(f"Successfully committed {temp_count} rows")

        # Step 5: Sanity check
        if temp_count < MIN_EXPECTED_ROWS:
            alert_data_anomaly("example_data", "LOW_VOLUME", f"Expected {MIN_EXPECTED_ROWS}+ rows, got {temp_count}")

        return temp_count

    except Exception as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    """Main collector function with full error handling"""

    # Setup logger
    logger = setup_logger(COLLECTOR_NAME)

    # Track execution time
    start_time = time.time()

    try:
        # Log start
        log_collector_start(logger, COLLECTOR_NAME)

        # Step 1: Fetch data from API
        logger.info("Fetching data from API...")
        data = fetch_data_from_api()
        logger.info(f"FETCHED: {len(data)} records from API")

        # Step 2: Insert data safely
        logger.info("Inserting data into database...")
        rows_inserted = insert_data_safely(data, logger)

        # Step 3: Log success
        duration = time.time() - start_time
        log_collector_finish(logger, COLLECTOR_NAME, rows_inserted, duration)

        return 0  # Success

    except Exception as e:
        # Log error
        duration = time.time() - start_time
        log_collector_error(logger, COLLECTOR_NAME, str(e), duration)

        # Send alert
        alert_collector_failed(COLLECTOR_NAME, str(e))

        return 1  # Failure


if __name__ == "__main__":
    sys.exit(main())
