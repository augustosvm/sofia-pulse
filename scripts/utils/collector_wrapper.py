#!/usr/bin/env python3
"""
Sofia Pulse - Collector Wrapper Utility

Provides timeout protection and collector_runs tracking for all collectors.

Usage:
    from utils.collector_wrapper import with_timeout, with_tracking

    @with_timeout(timeout_seconds=600)
    @with_tracking(collector_name='my-collector')
    def main():
        # Your collector logic here
        results = collect_data()
        return results  # Will be counted as records_inserted

    if __name__ == '__main__':
        main()
"""

import os
import sys
import signal
import socket
import psycopg2
from functools import wraps
from typing import Callable, Optional
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIG
# ============================================================================

DB_CONFIG = {
    'host': os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', 'localhost')),
    'port': int(os.getenv('DB_PORT', os.getenv('POSTGRES_PORT', '5432'))),
    'user': os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'sofia')),
    'password': os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', '')),
    'database': os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'sofia_db')),
}

HOSTNAME = socket.gethostname()

# ============================================================================
# TIMEOUT HANDLER
# ============================================================================

class TimeoutError(Exception):
    """Raised when collector execution exceeds timeout."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Collector execution exceeded timeout limit")


def with_timeout(timeout_seconds: int = 600):
    """
    Decorator that adds timeout protection to a collector.

    Args:
        timeout_seconds: Maximum execution time (default 10 minutes)

    Raises:
        TimeoutError: If execution exceeds timeout

    Example:
        @with_timeout(timeout_seconds=300)  # 5 minutes
        def collect_data():
            # Your logic here
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set up signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel alarm
                return result
            except TimeoutError:
                print(f"\n🔴 [FATAL] Collector exceeded {timeout_seconds}s timeout")
                raise
            finally:
                signal.signal(signal.SIGALRM, old_handler)

        return wrapper
    return decorator


# ============================================================================
# COLLECTOR_RUNS TRACKING
# ============================================================================

def start_collector_run(collector_name: str, conn) -> int:
    """
    Start tracking a collector run.

    Returns:
        run_id (int): Primary key of collector_runs record
    """
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sofia.collector_runs (collector_name, started_at, status)
        VALUES (%s, NOW(), 'running')
        RETURNING id
        """,
        (collector_name,),
    )
    conn.commit()
    run_id = cur.fetchone()[0]
    cur.close()
    print(f"✅ Started collector run: {collector_name} (run_id={run_id})")
    return run_id


def finish_collector_run(
    run_id: int,
    conn,
    status: str,
    records_inserted: int = 0,
    records_updated: int = 0,
    error_message: Optional[str] = None
):
    """
    Finish tracking a collector run.

    Args:
        run_id: Primary key from start_collector_run()
        conn: Database connection
        status: 'success' or 'failed'
        records_inserted: Number of new records inserted
        records_updated: Number of existing records updated
        error_message: Error details if failed
    """
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE sofia.collector_runs
        SET status = %s,
            completed_at = NOW(),
            records_inserted = %s,
            records_updated = %s,
            error_message = %s
        WHERE id = %s
        """,
        (status, records_inserted, records_updated, error_message, run_id),
    )
    conn.commit()
    cur.close()

    duration_query = """
        SELECT EXTRACT(EPOCH FROM (completed_at - started_at))::int as duration_sec
        FROM sofia.collector_runs
        WHERE id = %s
    """
    cur = conn.cursor()
    cur.execute(duration_query, (run_id,))
    duration = cur.fetchone()[0]
    cur.close()

    print(f"✅ Finished collector run: status={status}, inserted={records_inserted}, updated={records_updated}, duration={duration}s")


def with_tracking(collector_name: str):
    """
    Decorator that adds collector_runs tracking.

    The decorated function should return an integer (number of records inserted)
    or a dict with 'inserted' and 'updated' keys.

    Args:
        collector_name: Name to register in collector_runs table

    Example:
        @with_tracking(collector_name='github')
        def main():
            # Your collector logic
            return 100  # records inserted

        @with_tracking(collector_name='hackernews')
        def main():
            # Or return detailed stats
            return {'inserted': 50, 'updated': 10}
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            conn = None
            run_id = None

            try:
                # Connect to database
                conn = psycopg2.connect(**DB_CONFIG)
                print(f"📊 [TRACKING] Collector: {collector_name}")

                # Start tracking
                run_id = start_collector_run(collector_name, conn)

                # Execute collector
                result = func(*args, **kwargs)

                # Parse result
                if isinstance(result, dict):
                    inserted = result.get('inserted', 0)
                    updated = result.get('updated', 0)
                elif isinstance(result, int):
                    inserted = result
                    updated = 0
                else:
                    inserted = 0
                    updated = 0

                # Finish tracking
                finish_collector_run(run_id, conn, 'success', inserted, updated)

                return result

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                print(f"\n🔴 [ERROR] {error_msg}")

                # Mark as failed
                if conn and run_id:
                    finish_collector_run(run_id, conn, 'failed', 0, 0, error_msg)

                raise

            finally:
                if conn:
                    conn.close()

        return wrapper
    return decorator


# ============================================================================
# COMBINED WRAPPER (Timeout + Tracking)
# ============================================================================

def wrapped_collector(collector_name: str, timeout_seconds: int = 600):
    """
    Combined decorator: timeout + tracking.

    Args:
        collector_name: Name for collector_runs tracking
        timeout_seconds: Max execution time (default 10 min)

    Example:
        @wrapped_collector('github', timeout_seconds=300)
        def main():
            # Collector logic with timeout AND tracking
            return 100
    """
    def decorator(func: Callable):
        # Apply both decorators
        return with_timeout(timeout_seconds)(with_tracking(collector_name)(func))
    return decorator
