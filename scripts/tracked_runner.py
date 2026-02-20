#!/usr/bin/env python3
import sys, os, json, subprocess, uuid, time, fcntl, socket
import psycopg2
from datetime import datetime

# OPTIONAL DOTENV
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    print("❌ ERROR: DATABASE_URL not set.")
    sys.exit(1)

REGISTRY = {
    # PILOT
    "ibge-api":   {"cmd": ["python3", "scripts/collect-ibge-api.py"], "timeout": 300, "v2": True},
    "hackernews": {"cmd": ["npx", "tsx", "scripts/collect-hackernews.ts"], "timeout": 300, "v2": True},
}
LOCK_DIR = "/tmp/sofia-locks"
LOG_DIR = os.path.join(os.getcwd(), "logs")


# ============================================================================
# PATCH 1 (Anti-OOM): Read tail from file in bytes — never load full output
# ============================================================================
def _tail_file(path: str, max_bytes: int = 1000) -> str:
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - max_bytes), os.SEEK_SET)
            data = f.read()
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def run_collector(collector_id):
    if collector_id not in REGISTRY:
        sys.exit(f"❌ Unknown collector: {collector_id}")

    cfg = REGISTRY[collector_id]

    # A. LOCKING
    os.makedirs(LOCK_DIR, exist_ok=True)
    lock_path = f"{LOCK_DIR}/{collector_id}.lock"
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        sys.exit(f"⚠️  Already running: {collector_id}")

    # B. DB INIT (Safety Flag)
    run_id = str(uuid.uuid4())
    db_started = False
    finalized = False  # PATCH 3: anti-zombie on kill/crash
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        _db_insert_start(conn, run_id, collector_id, " ".join(cfg["cmd"]), os.getpid())
        db_started = True
        print(f"🚀 Starting {collector_id} (RunID: {run_id})")
    except Exception as e:
        print(f"❌ DB Init Fail: {e}")
    finally:
        if conn:
            conn.close()

    # State vars — needed in finally
    status = "failed"
    exit_code = -1
    metrics = {}
    error_msg = None
    log_path = None
    stdout_tail = ""
    stderr_tail = ""
    start_ts = time.time()
    duration = None

    # PATCH 1: file paths for stdout/stderr (anti-OOM)
    out_path = os.path.join(LOG_DIR, collector_id, f"{run_id}.out")
    err_path = os.path.join(LOG_DIR, collector_id, f"{run_id}.err")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    try:
        # C. EXECUTE — write directly to files, never to RAM
        env = {**os.environ, "PYTHONUNBUFFERED": "1", "SOFIA_RUN_ID": run_id}

        # PATCH 3: BaseException to catch SIGTERM/KeyboardInterrupt
        try:
            with open(out_path, "wb") as stdout_f, open(err_path, "wb") as stderr_f:
                proc = subprocess.run(
                    cfg["cmd"],
                    stdout=stdout_f,
                    stderr=stderr_f,
                    text=False,
                    timeout=cfg["timeout"],
                    env=env,
                )
            exit_code = proc.returncode

        except subprocess.TimeoutExpired:
            status = "timeout"
            exit_code = -1
            error_msg = f"Timed out after {cfg['timeout']}s"
            with open(err_path, "ab") as f:
                f.write(f"\n[Runner] Timeout after {cfg['timeout']}s\n".encode())

        except BaseException as e:  # PATCH 3: catch kill/restart signals
            status = "failed"
            exit_code = -1
            error_msg = f"[Runner] Aborted: {type(e).__name__}: {e}"
            with open(err_path, "ab") as f:
                f.write(f"\n{error_msg}\n".encode())
            raise  # re-raise so cron/systemd sees non-zero exit

        duration = int((time.time() - start_ts) * 1000)

        # D. READ TAILS (anti-OOM: only last N bytes)
        stdout = _tail_file(out_path, 20_000)  # large enough for JSON parse
        stderr = _tail_file(err_path, 20_000)
        stdout_tail = _tail_file(out_path, 1_000)
        stderr_tail = _tail_file(err_path, 1_000)

        # E. PROCESS RESULT
        if status != "timeout":
            if exit_code == 0:
                if cfg.get("v2"):
                    metrics = _parse_json_last_lines(stdout)
                    if not metrics:
                        status = "invalid_output"
                        error_msg = "V2: No valid JSON in last 5 lines of stdout"
                    else:
                        metrics = _normalize_metrics(metrics)
                        valid, err = _validate_schema(metrics)
                        if not valid:
                            status = "invalid_output"
                            error_msg = f"V2 Schema Error: {err}"
                        elif metrics.get("status") == "fail":
                            status = "failed"
                            error_msg = f"Collector reported failure: {json.dumps(metrics.get('meta', {}))}"
                        else:
                            status = "success"
                else:
                    status = "success"
                    metrics = {"meta": {"legacy_mode": True}}
            else:
                status = "failed"
                error_msg = error_msg or stderr[-2000:]

        # F. PERSIST LOGS
        log_path = _save_logs(collector_id, run_id, out_path, err_path)

        # G. WRITE FINAL STATE FILE (Patch 2 — Opção B: anti-lying dashboard)
        _save_final_state(collector_id, run_id, status, exit_code, error_msg, metrics)

        # H. UPDATE DB
        if db_started:
            try:
                conn = psycopg2.connect(DB_URL)
                _db_update_finish(conn, run_id, status, duration, exit_code, error_msg, metrics, log_path, stdout_tail, stderr_tail)
                conn.close()
                finalized = True
            except Exception as e:
                fail_path = os.path.join(LOG_DIR, collector_id, f"{run_id}.dbfail")
                with open(fail_path, "w") as f:
                    f.write(f"DB Update Failed: {e}\n\nMetrics: {json.dumps(metrics)}\nStatus: {status}")
                print(f"⚠️ DB Update Failed. Saved to {fail_path}")
        else:
            print(f"⚠️ DB update skipped (init failed). Logs at {log_path}")

    finally:
        # PATCH 3: ensure DB record is closed on SIGTERM/uncaught exception
        if db_started and not finalized:
            duration_final = int((time.time() - start_ts) * 1000) if duration is None else duration
            try:
                conn = psycopg2.connect(DB_URL)
                _db_update_finish(
                    conn, run_id,
                    status if status != "running" else "failed",
                    duration_final,
                    exit_code,
                    error_msg or "[Runner] Aborted before finalize",
                    metrics or {},
                    log_path,
                    stdout_tail,
                    stderr_tail,
                )
                conn.close()
            except Exception:
                pass  # nothing else we can do

        try:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            lock_file.close()
        except Exception:
            pass

    print(f"✅ Finished: {status} ({duration}ms)")


def reap_zombies():
    """Marks runs as zombie if running > 1h, but skips if .dbfail or .final.json exist on disk."""
    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT run_id, collector_id
                FROM sofia.collector_runs_v2
                WHERE status='running'
                  AND NOW() - started_at > INTERVAL '1 hour'
                LIMIT 500
            """)
            candidates = cur.fetchall()

        reaped = 0
        reconciled = 0
        for run_id, collector_id in candidates:
            # PATCH 2 (Opção A+B): Don't zombify if we have local proof of completion
            final_path  = os.path.join(LOG_DIR, collector_id, f"{run_id}.final.json")
            dbfail_path = os.path.join(LOG_DIR, collector_id, f"{run_id}.dbfail")

            if os.path.exists(final_path):
                # Reconcile: apply the real status from disk to DB
                try:
                    with open(final_path) as f:
                        final = json.load(f)
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE sofia.collector_runs_v2
                            SET status=%s, finished_at=NOW(),
                                error_message=COALESCE(error_message,'') || ' [Reconciled from .final.json]'
                            WHERE run_id=%s
                        """, (final.get("status", "failed"), run_id))
                    conn.commit()
                    reconciled += 1
                except Exception:
                    pass
                continue

            if os.path.exists(dbfail_path):
                # We know it ran but DB failed — leave it for manual review, don't zombie
                continue

            # No evidence on disk = true zombie
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE sofia.collector_runs_v2
                    SET status='zombie', finished_at=NOW(),
                        error_message=COALESCE(error_message,'') || ' [Runner] Reaped'
                    WHERE run_id=%s
                """, (run_id,))
            conn.commit()
            reaped += 1

        print(f"🧟 Zombies: {reaped} reaped, {reconciled} reconciled from disk.")
    finally:
        conn.close()


def print_status():
    """Operational dashboard: Long running (>10m) and Invalid Outputs (24h)"""
    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            print("\n=== 🏃 LONG RUNNING (> 10m) ===")
            cur.execute("""
                SELECT collector_id, started_at, now() - started_at as duration
                FROM sofia.collector_runs_v2
                WHERE status='running' AND now() - started_at > INTERVAL '10 minutes'
                ORDER BY started_at
            """)
            long_runs = cur.fetchall()
            if not long_runs: print("None.")
            else:
                for row in long_runs: print(f"{row[0]} ({row[2]})")

            print("\n=== ⚠️  INVALID OUTPUT (Last 24h) ===")
            cur.execute("""
                SELECT collector_id, started_at, error_message
                FROM sofia.collector_runs_v2
                WHERE status='invalid_output' AND started_at > now() - INTERVAL '24 hours'
                ORDER BY started_at DESC
            """)
            invalid = cur.fetchall()
            if not invalid: print("None.")
            else:
                for row in invalid: print(f"{row[0]} at {row[1]}: {row[2]}")
            
            print("\n=== 📊 RECENT HEALTH (Non-Healthy) ===")
            cur.execute("""
                SELECT collector_id, health_state, last_error 
                FROM sofia.v_collector_health 
                WHERE health_state != 'healthy'
            """)
            unhealthy = cur.fetchall()
            if not unhealthy: print("All collectors healthy.")
            else:
                for row in unhealthy: print(f"{row[0]}: {row[1]} ({row[2]})")

    finally:
        conn.close()


# ============================================================================
# Helpers
# ============================================================================

def _save_final_state(cid, rid, status, exit_code, error_msg, metrics):
    """Write .final.json before DB update. Used for anti-zombie reconciliation."""
    path = os.path.join(LOG_DIR, cid, f"{rid}.final.json")
    try:
        with open(path, "w") as f:
            json.dump({
                "run_id": rid,
                "collector_id": cid,
                "status": status,
                "exit_code": exit_code,
                "error_message": error_msg,
                "metrics": metrics,
            }, f)
    except Exception:
        pass  # Non-fatal


def _parse_json_last_lines(stdout):
    if not stdout:
        return None
    lines = [l.strip() for l in stdout.strip().splitlines() if l.strip()]
    if not lines:
        return None
    for line in reversed(lines[-5:]):
        try:
            return json.loads(line)
        except Exception:
            continue
    return None


def _normalize_metrics(d):
    """Cast metric fields to int. Returns a copy — never mutates original."""
    if not isinstance(d, dict):
        return d
    d = dict(d)
    for k in ["items_inserted", "items_updated", "items_read", "items_candidate", "items_ignored_conflict"]:
        if k in d:
            try:
                d[k] = int(d[k])
            except Exception:
                pass
    return d


def _validate_schema(d):
    """Pure validation (no mutations). Returns (bool, error_message)."""
    if not isinstance(d, dict):
        return False, "Root must be a dict"
    required = ["status", "source", "items_inserted", "items_updated", "tables_affected"]
    missing = [k for k in required if k not in d]
    if missing:
        return False, f"Missing keys: {missing}"
    if d["status"] not in ("ok", "fail"):
        return False, f"Invalid status: {d['status']}"
    src = d.get("source")
    if not src or src == "unknown":
        return False, "source cannot be unknown/empty"
    if not isinstance(d["tables_affected"], list):
        return False, "tables_affected must be a list"
    for k in ["items_inserted", "items_updated", "items_read", "items_candidate", "items_ignored_conflict"]:
        if k in d and not isinstance(d[k], int):
            return False, f"{k} must be int (got {type(d[k]).__name__})"
    return True, None


def _save_logs(cid, rid, out_path, err_path):
    """Merge .out + .err into a single .log file for easy human inspection."""
    log_path = os.path.join(LOG_DIR, cid, f"{rid}.log")
    with open(log_path, "w", encoding="utf-8") as log_f:
        log_f.write(f"RunID: {rid}\nDate: {datetime.now().isoformat()}\n\n=== STDOUT ===\n")
        log_f.write(_tail_file(out_path, 100_000))
        log_f.write("\n\n=== STDERR ===\n")
        log_f.write(_tail_file(err_path, 100_000))
    return log_path


def _db_insert_start(conn, run_id, cid, cmd, pid):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO sofia.collector_runs_v2 (run_id, collector_id, command, hostname, pid)
            VALUES (%s, %s, %s, %s, %s)
        """, (run_id, cid, cmd, socket.gethostname(), pid))
    conn.commit()


def _db_update_finish(conn, run_id, status, duration, exit_code, error, m, log_path, out_tail, err_tail):
    m = m or {}
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE sofia.collector_runs_v2
            SET status=%s, finished_at=NOW(), duration_ms=%s, exit_code=%s, error_message=%s,
                source=%s, items_read=%s, items_candidate=%s,
                items_inserted=%s, items_updated=%s, items_ignored_conflict=%s,
                tables_affected=%s, meta=%s,
                full_log_path=%s, stdout_tail=%s, stderr_tail=%s
            WHERE run_id=%s
        """, (
            status, duration, exit_code, error,
            m.get("source"),
            m.get("items_read", 0), m.get("items_candidate", 0),
            m.get("items_inserted", 0), m.get("items_updated", 0), m.get("items_ignored_conflict", 0),
            m.get("tables_affected", []), json.dumps(m.get("meta", {})),
            log_path, out_tail, err_tail,
            run_id,
        ))
    conn.commit()


def print_health():
    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT collector_id, health_state, last_run_at, last_error
                FROM sofia.v_collector_health
                WHERE health_state IS DISTINCT FROM 'healthy'
            """)
            issues = cur.fetchall()
            if not issues:
                print("✅ All collectors healthy.")
            else:
                for i in issues:
                    print(f"⚠️ {i[0]}: {i[1]} (Last: {i[2]}) — {i[3]}")
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: tracked_runner.py <collector_id> | --health | --status | --reap-zombies")
    arg = sys.argv[1]
    if arg == "--health":
        print_health()
    elif arg == "--status":
        print_status()
    elif arg == "--reap-zombies":
        reap_zombies()
    else:
        run_collector(arg)
