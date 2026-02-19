#!/usr/bin/env python3
"""
Tracked Runner - Executa comando/collector com tracking em collector_runs

Uso:
  python3 tracked_runner.py <collector_name> [<command>]

Exemplos:
  python3 tracked_runner.py adzuna
  python3 tracked_runner.py adzuna "/home/ubuntu/sofia-pulse/scripts/collect-with-notification.sh adzuna"
  python3 tracked_runner.py test "echo 'hello'"
"""

import os
import sys
import time
import subprocess
from urllib.parse import urlparse

try:
    import psycopg2
except Exception as e:
    raise SystemExit(f"[tracked_runner] psycopg2 not available: {e}")

DEFAULT_SCHEMA = os.environ.get("SOFIA_DB_SCHEMA", "sofia")

def ts():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def get_db_conn():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not set")

    parsed = urlparse(db_url)
    if not parsed.hostname or not parsed.path:
        raise ValueError("DATABASE_URL invalid format")

    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
        connect_timeout=10,
    )

def qname(table: str) -> str:
    return f"{DEFAULT_SCHEMA}.{table}"

def record_start(conn, collector_name: str):
    with conn.cursor() as cur:
        cur.execute(f"""
            INSERT INTO {qname('collector_runs')}
              (collector_name, status, started_at)
            VALUES (%s, 'running', NOW())
            RETURNING id, started_at
        """, (collector_name,))
        run_id, started_at = cur.fetchone()
    conn.commit()
    return run_id, started_at

def _count_saved(conn, collector_name: str, started_at):
    # Try multiple patterns to find saved records
    # Some collectors use source, others use platform (greenhouse, etc)
    # Also try without 'jobs-' prefix for jobs collectors
    
    collector_simple = collector_name.replace('jobs-', '')  # 'jobs-greenhouse' -> 'greenhouse'
    
    attempts = [
        # Try with original collector_name
        (f"SELECT COUNT(*) FROM {qname('jobs')} WHERE created_at >= %s AND source = %s", (started_at, collector_name)),
        (f"SELECT COUNT(*) FROM {qname('jobs')} WHERE collected_at >= %s AND source = %s", (started_at, collector_name)),
        (f"SELECT COUNT(*) FROM {qname('jobs')} WHERE created_at >= %s AND platform = %s", (started_at, collector_name)),
        (f"SELECT COUNT(*) FROM {qname('jobs')} WHERE collected_at >= %s AND platform = %s", (started_at, collector_name)),
        
        # Try with simplified name (without 'jobs-' prefix)
        (f"SELECT COUNT(*) FROM {qname('jobs')} WHERE created_at >= %s AND source = %s", (started_at, collector_simple)),
        (f"SELECT COUNT(*) FROM {qname('jobs')} WHERE collected_at >= %s AND source = %s", (started_at, collector_simple)),
        (f"SELECT COUNT(*) FROM {qname('jobs')} WHERE created_at >= %s AND platform = %s", (started_at, collector_simple)),
        (f"SELECT COUNT(*) FROM {qname('jobs')} WHERE collected_at >= %s AND platform = %s", (started_at, collector_simple)),
        
        # Fallback: without schema qualifier
        (f"SELECT COUNT(*) FROM jobs WHERE created_at >= %s AND source = %s", (started_at, collector_name)),
        (f"SELECT COUNT(*) FROM jobs WHERE collected_at >= %s AND source = %s", (started_at, collector_name)),
        (f"SELECT COUNT(*) FROM jobs WHERE created_at >= %s AND platform = %s", (started_at, collector_simple)),
    ]

    last_err = None
    for sql, params in attempts:
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return int(cur.fetchone()[0] or 0)
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"Could not count saved rows (schema/columns mismatch). Last error: {last_err}")

def record_finish(conn, run_id: int, collector_name: str, started_at, exit_code: int, duration_ms: int, stderr_hint: str):
    ok = (exit_code == 0)
    error_code = None if ok else (stderr_hint or f"EXIT_{exit_code}")

    saved = 0
    try:
        saved = _count_saved(conn, collector_name, started_at)
    except Exception as e:
        error_code = (error_code or "FAILED") + f"|SAVED_COUNT_ERR"
        print(f"[{ts()}] [tracked_runner] WARN saved count failed: {e}", file=sys.stderr)

    with conn.cursor() as cur:
        cur.execute(f"""
            UPDATE {qname('collector_runs')}
            SET
              completed_at = NOW(),
              status = %s,
              ok = %s,
              saved = %s,
              error_code = %s,
              duration_ms = %s
            WHERE id = %s
        """, (
            "completed" if ok else "failed",
            ok,
            saved,
            error_code,
            duration_ms,
            run_id
        ))
    conn.commit()
    return saved

def run_tracked(collector_name: str, command: str):
    if not command:
        command = f"/home/ubuntu/sofia-pulse/scripts/collect-with-notification.sh {collector_name}"

    conn = get_db_conn()
    try:
        run_id, started_at = record_start(conn, collector_name)
        print(f"[{ts()}] [{collector_name}] run_id={run_id} started_at={started_at} cmd={command}")

        t0 = time.time()
        stderr_hint = None
        exit_code = 1

        try:
            r = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True,
                timeout=600
            )
            exit_code = r.returncode
            if r.stderr:
                stderr_hint = (r.stderr.strip().splitlines()[-1])[:120]
            if r.stdout:
                print(r.stdout, end="")
            if r.stderr:
                print(r.stderr, end="", file=sys.stderr)

        except subprocess.TimeoutExpired:
            exit_code = 124
            stderr_hint = "TIMEOUT_600S"
            print(f"[{ts()}] [{collector_name}] TIMEOUT after 600s", file=sys.stderr)

        except Exception as e:
            exit_code = 1
            stderr_hint = f"EXC_{type(e).__name__}"
            print(f"[{ts()}] [{collector_name}] ERROR {e}", file=sys.stderr)

        duration_ms = int((time.time() - t0) * 1000)
        saved = record_finish(conn, run_id, collector_name, started_at, exit_code, duration_ms, stderr_hint)

        print(f"[{ts()}] [{collector_name}] finished exit={exit_code} saved={saved} duration_ms={duration_ms}")
        return exit_code

    finally:
        conn.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: tracked_runner.py <collector_name> [<command>]", file=sys.stderr)
        sys.exit(1)

    collector_name = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(run_tracked(collector_name, command))

if __name__ == "__main__":
    main()
