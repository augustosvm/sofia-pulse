"""Sofia Skill: collect.run — Executa collector, registra em collector_runs.

Nomenclatura canônica:
- collector_id: ID no inventory (ex: "acled") — OBRIGATÓRIO
- collector_path: path do script — OPCIONAL (resolvido do inventory se não passar)

O cron/n8n/pipeline só passa collector_id. Ponto.
"""

import os, re, subprocess, time, uuid, json, psycopg2
from lib.helpers import ok, fail, DB_URL
from lib.fs_bootstrap import ensure_directories


def execute(trace_id, actor, dry_run, params, context):
    start = time.time()
    run_id = str(uuid.uuid4())
    cid = params.get("collector_id", "")

    if not cid:
        return fail("INVALID_INPUT", "collector_id is required", start)

    # Bootstrap filesystem
    fs_setup = ensure_directories()
    warnings = []
    if fs_setup.get("warnings"):
        warnings = [{"code": "FS_WARNING", "message": w} for w in fs_setup["warnings"]]

    try:
        # --- Resolver path: explícito ou via inventory ---
        path = params.get("collector_path")
        if not path:
            path = _resolve_path(cid)
        if not path:
            return fail("INVENTORY_NOT_FOUND", f"No path for collector_id={cid}. Pass collector_path or register in inventory.", start)
        if not os.path.exists(path):
            return fail("INVENTORY_NOT_FOUND", f"File not found: {path}", start)

        # --- Executor ---
        if path.endswith(".py"): cmd = ["python3", path]
        elif path.endswith(".ts"): cmd = ["npx", "tsx", path]
        elif path.endswith(".js"): cmd = ["node", path]
        else: return fail("INVALID_INPUT", f"Unknown type: {path}", start)

        for k, v in params.get("args", {}).items():
            cmd.extend([f"--{k}", str(v)])
        if params.get("since"): cmd.extend(["--since", params["since"]])
        if params.get("until"): cmd.extend(["--until", params["until"]])
        if params.get("limit"): cmd.extend(["--limit", str(params["limit"])])
        if params.get("force"): cmd.append("--force")

        if dry_run:
            return ok({"run_id": run_id, "collector_id": cid, "collector_path": path, "dry_run": True}, start)

        _record_start(run_id, trace_id, cid, path, actor, params, context)
        env_vars = {**os.environ, "SOFIA_TRACE_ID": trace_id, "SOFIA_RUN_ID": run_id}
        timeout_s = params.get("timeout_ms", 300000) // 1000

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, env=env_vars)
        duration_ms = round((time.time() - start) * 1000)
        output = (result.stdout or "") + (result.stderr or "")

        fetched = _extract(output, r"(?:fetched|collected|found)[:\s]+(\d+)") or 0
        saved = _extract(output, r"(?:saved|inserted|upserted)[:\s]+(\d+)") or 0
        skipped = _extract(output, r"(?:skipped|duplicat|ignored)[:\s]+(\d+)") or 0

        # --- Classificar erro baseado em stderr ---
        error_code = None
        stderr_lower = (result.stderr or "").lower()
        if result.returncode != 0:
            # FS_ERROR: permission denied, no such file or directory (paths), errno 2/13
            if any(x in stderr_lower for x in ["no such file or directory", "permission denied", "errno 2", "errno 13", "filenotfounderror"]):
                # Distinguir: se é sobre módulo Python/Node → DEPENDENCY_MISSING
                # Se é sobre paths/diretórios → FS_ERROR
                if "module" in stderr_lower or "import" in stderr_lower:
                    error_code = "DEPENDENCY_MISSING"
                else:
                    error_code = "FS_ERROR"
            # DEPENDENCY_MISSING: módulos ausentes ou comandos não instalados
            elif any(x in stderr_lower for x in ["modulenotfounderror", "importerror", "cannot find module", "command not found", "tsx: not found", "npx: not found"]):
                error_code = "DEPENDENCY_MISSING"
            # COLLECT_SOURCE_DOWN: API down, timeouts, 5xx
            elif any(x in stderr_lower for x in ["connectionerror", "timeout", "timed out", "unreachable", "503", "502", "504"]):
                error_code = "COLLECT_SOURCE_DOWN"
            # SCRIPT_ERROR: fallback para outros erros (SQL, stacktrace, etc)
            else:
                error_code = "SCRIPT_ERROR"

        _record_finish(run_id, duration_ms, fetched, saved, skipped,
                       result.returncode, result.returncode == 0, error_code, result.stderr[:500] if error_code else None)

        if result.returncode != 0:
            return fail(error_code, f"Exit {result.returncode}: {(result.stderr or '')[:500]}", start, retryable=(error_code == "COLLECT_SOURCE_DOWN"))
        if fetched == 0 and saved == 0 and not params.get("force"):
            return fail("COLLECT_EMPTY", "Zero records fetched and saved", start)

        return ok({"run_id": run_id, "collector_id": cid, "collector_path": path,
                    "fetched": fetched, "saved": saved, "skipped": skipped,
                    "duration_ms": duration_ms, "exit_code": result.returncode}, start, warnings=warnings)

    except subprocess.TimeoutExpired:
        _record_finish(run_id, round((time.time()-start)*1000), 0,0,0,-1, False, "TIMEOUT", "Timed out")
        return fail("TIMEOUT", "Collector timed out", start, retryable=True)
    except Exception as e:
        return fail("UNKNOWN_ERROR", str(e), start)


def _resolve_path(collector_id):
    """Busca path no inventory. None se não encontrar."""
    try:
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()
        cur.execute("SELECT path FROM sofia.collector_inventory WHERE collector_id=%s AND enabled=TRUE", (collector_id,))
        row = cur.fetchone(); cur.close(); conn.close()
        return row[0] if row else None
    except: return None


def _extract(text, pattern):
    m = re.search(pattern, text, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _record_start(run_id, trace_id, cid, path, actor, params, ctx):
    try:
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()
        cur.execute("INSERT INTO sofia.collector_runs (run_id,trace_id,collector_name,collector_path,actor,params,env) VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s)",
                    (run_id, trace_id, cid, path, actor, json.dumps(params), ctx.get("env","prod")))
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        # Debug: não silenciar erros
        import sys
        print(f"[DEBUG] _record_start failed: {e}", file=sys.stderr)


def _record_finish(run_id, dur, fetched, saved, skipped, exit_code, is_ok, err_code, err_msg):
    try:
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()
        cur.execute("UPDATE sofia.collector_runs SET finished_at=NOW(),duration_ms=%s,fetched=%s,saved=%s,skipped=%s,exit_code=%s,ok=%s,error_code=%s,error_message=%s WHERE run_id=%s",
                    (dur, fetched, saved, skipped, exit_code, is_ok, err_code, err_msg, run_id))
        conn.commit(); cur.close(); conn.close()
    except: pass
