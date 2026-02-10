"""
Sofia Skill: inventory.collectors
Lista, valida, registra e audita collectors. Anti-entropia.
Actions: list, validate, register, deprecate, scan, update
"""

import os, time, glob, json, psycopg2
from lib.helpers import ok, fail, DB_URL


def execute(trace_id, actor, dry_run, params, context):
    start = time.time()
    action = params.get("action", "list")

    try:
        if action == "list":
            return _list(start, params)
        elif action == "validate":
            return _validate(start, params)
        elif action == "register":
            return _register(start, params, dry_run)
        elif action == "update":
            return _update(start, params, dry_run)
        elif action == "deprecate":
            return _deprecate(start, params, dry_run)
        elif action == "scan":
            return _scan(start, params, dry_run)
        else:
            return fail("INVALID_INPUT", f"Unknown action: {action}", start)
    except Exception as e:
        return fail("UNKNOWN_ERROR", str(e), start)


def _list(start, params):
    """Lista collectors do inventário com filtros opcionais."""
    conn = psycopg2.connect(DB_URL); cur = conn.cursor()
    status = params.get("status")
    if status:
        cur.execute("SELECT collector_id,path,schedule,enabled,status,expected_min_records,owner,tags,output_tables FROM sofia.collector_inventory WHERE status=%s ORDER BY collector_id", (status,))
    else:
        cur.execute("SELECT collector_id,path,schedule,enabled,status,expected_min_records,owner,tags,output_tables FROM sofia.collector_inventory ORDER BY collector_id")
    rows = cur.fetchall()
    cur.close(); conn.close()
    collectors = [{"collector_id": r[0], "path": r[1], "schedule": r[2], "enabled": r[3],
                    "status": r[4], "expected_min": r[5], "owner": r[6], "tags": r[7], "output_tables": r[8]} for r in rows]
    return ok({"collectors": collectors, "total": len(collectors)}, start)


def _validate(start, params):
    """Verifica se paths existem no filesystem."""
    conn = psycopg2.connect(DB_URL); cur = conn.cursor()
    cur.execute("SELECT collector_id,path FROM sofia.collector_inventory WHERE enabled=TRUE")
    rows = cur.fetchall()
    cur.close(); conn.close()

    valid, invalid = 0, []
    for cid, path in rows:
        if os.path.exists(path):
            valid += 1
        else:
            invalid.append({"collector_id": cid, "path": path, "reason": "File not found"})

    warnings = [{"code": "INVENTORY_NOT_FOUND", "message": f"{len(invalid)} collectors have missing files"}] if invalid else []
    return ok({"validated": valid, "invalid": len(invalid), "invalid_details": invalid}, start, warnings=warnings)


def _register(start, params, dry_run):
    """Registra novo collector no inventário."""
    cid = params.get("collector_id")
    path = params.get("path")
    if not cid or not path:
        return fail("INVALID_INPUT", "collector_id and path required", start)
    if not os.path.exists(path):
        return fail("INVENTORY_NOT_FOUND", f"Path not found: {path}", start)

    if dry_run:
        return ok({"registered": 0, "collector_id": cid, "dry_run": True}, start)

    conn = psycopg2.connect(DB_URL); cur = conn.cursor()
    lang = "python" if path.endswith(".py") else "typescript" if path.endswith(".ts") else "shell"
    cur.execute("""INSERT INTO sofia.collector_inventory (collector_id,path,language,schedule,status,description)
                VALUES (%s,%s,%s,%s,'experimental',%s)
                ON CONFLICT (collector_id) DO UPDATE SET path=%s, updated_at=NOW()""",
                (cid, path, lang, params.get("schedule", "manual"), params.get("description", ""),  path))
    conn.commit(); cur.close(); conn.close()
    return ok({"registered": 1, "collector_id": cid}, start)


def _update(start, params, dry_run):
    """Atualiza campos de um collector existente."""
    cid = params.get("collector_id")
    if not cid:
        return fail("INVALID_INPUT", "collector_id required", start)

    # Validar campos
    expected_min = params.get("expected_min_records")
    if expected_min is not None and (not isinstance(expected_min, int) or expected_min < 0):
        return fail("INVALID_INPUT", "expected_min_records must be >= 0", start)

    if dry_run:
        return ok({"updated": 0, "collector_id": cid, "dry_run": True}, start)

    # Verificar se collector existe
    conn = psycopg2.connect(DB_URL); cur = conn.cursor()
    cur.execute("SELECT collector_id FROM sofia.collector_inventory WHERE collector_id=%s", (cid,))
    if not cur.fetchone():
        cur.close(); conn.close()
        return fail("INVENTORY_NOT_FOUND", f"Collector not found: {cid}", start)

    # Montar UPDATE dinamicamente baseado nos params fornecidos
    updates = []
    values = []

    if expected_min is not None:
        updates.append("expected_min_records = %s")
        values.append(expected_min)

    if "allow_empty" in params:
        updates.append("allow_empty = %s")
        values.append(params["allow_empty"])

    if "schedule" in params:
        updates.append("schedule = %s")
        values.append(params["schedule"])

    if "status" in params:
        updates.append("status = %s")
        values.append(params["status"])

    if "path" in params:
        updates.append("path = %s")
        values.append(params["path"])

    if not updates:
        cur.close(); conn.close()
        return fail("INVALID_INPUT", "No fields to update", start)

    # Executar UPDATE
    updates.append("updated_at = NOW()")
    values.append(cid)

    sql = f"UPDATE sofia.collector_inventory SET {', '.join(updates)} WHERE collector_id = %s"
    cur.execute(sql, values)
    affected = cur.rowcount
    conn.commit(); cur.close(); conn.close()

    return ok({"updated": affected, "collector_id": cid}, start)


def _deprecate(start, params, dry_run):
    """Marca collector como deprecated."""
    cid = params.get("collector_id")
    if not cid: return fail("INVALID_INPUT", "collector_id required", start)

    if dry_run:
        return ok({"collector_id": cid, "status": "deprecated", "dry_run": True}, start)

    conn = psycopg2.connect(DB_URL); cur = conn.cursor()
    cur.execute("UPDATE sofia.collector_inventory SET status='deprecated', updated_at=NOW() WHERE collector_id=%s", (cid,))
    affected = cur.rowcount
    conn.commit(); cur.close(); conn.close()
    if affected == 0:
        return fail("INVENTORY_NOT_FOUND", f"Collector not found: {cid}", start)
    return ok({"collector_id": cid, "status": "deprecated"}, start)


def _scan(start, params, dry_run):
    """Auto-scan de diretório para encontrar scripts não registrados (órfãos)."""
    scan_dir = params.get("scan_dir", "scripts/")
    if not os.path.isdir(scan_dir):
        return fail("INVALID_INPUT", f"Directory not found: {scan_dir}", start)

    # Buscar scripts existentes no filesystem
    found = set()
    for ext in ("*.py", "*.ts", "*.js"):
        for f in glob.glob(os.path.join(scan_dir, "**", ext), recursive=True):
            if "node_modules" not in f and "__pycache__" not in f:
                found.add(f)

    # Buscar paths registrados
    conn = psycopg2.connect(DB_URL); cur = conn.cursor()
    cur.execute("SELECT path FROM sofia.collector_inventory")
    registered = {r[0] for r in cur.fetchall()}
    cur.close(); conn.close()

    orphaned = sorted(found - registered)
    registered_missing = sorted(registered - found)

    warnings = []
    if orphaned:
        warnings.append({"code": "INVENTORY_NOT_FOUND", "message": f"{len(orphaned)} scripts not in inventory"})

    return ok({
        "scanned_dir": scan_dir,
        "found_scripts": len(found),
        "registered": len(registered),
        "orphaned": orphaned[:50],  # Cap output
        "registered_but_missing": registered_missing[:50],
    }, start, warnings=warnings)
