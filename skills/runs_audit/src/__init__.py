"""Sofia Skill: runs.audit — Auditoria diária. Sem LLM.

Critérios OBJETIVOS de healthy (não subjetivo):
  healthy = (missing == 0) AND (failed == 0) AND (empty == 0)
Cada critério é reportado individualmente.
"""

import time, psycopg2
from datetime import date
from lib.helpers import ok, fail, DB_URL

# Critérios explícitos — se quiser mudar, mude AQUI, não no código
HEALTHY_CRITERIA = {
    "missing_daily_collectors": 0,   # collectors daily que não rodaram
    "failed_runs": 0,                # runs com ok=false
    "empty_runs": 0,                 # runs com ok=true mas saved < expected_min_records e allow_empty=false
}


def execute(trace_id, actor, dry_run, params, context):
    start = time.time()
    try:
        audit_date = params.get("date", str(date.today()))
        include_details = params.get("include_details", False)
        include_succeeded = params.get("include_succeeded", True)  # Default true para relatórios completos
        since_hours = params.get("since_hours")  # Opcional: últimas N horas ao invés de dia inteiro
        expected_collectors = params.get("expected_collectors")  # Lista opcional de collector_ids
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()

        # 1. Collectors esperados
        if expected_collectors:
            # Modo explicit: usar lista fornecida
            if isinstance(expected_collectors, list) and len(expected_collectors) > 0:
                placeholders = ','.join(['%s'] * len(expected_collectors))
                cur.execute(f"SELECT collector_id, path, expected_min_records, allow_empty FROM sofia.collector_inventory WHERE collector_id IN ({placeholders}) AND enabled=TRUE", expected_collectors)
                expected = {r[0]: {"path": r[1], "min_records": r[2], "allow_empty": r[3]} for r in cur.fetchall()}
            else:
                expected = {}
        else:
            # Modo legacy: buscar todos daily
            cur.execute("SELECT collector_id, path, expected_min_records, allow_empty FROM sofia.collector_inventory WHERE schedule='daily' AND enabled=TRUE")
            expected = {r[0]: {"path": r[1], "min_records": r[2], "allow_empty": r[3]} for r in cur.fetchall()}

        # 2. Runs do dia (timezone Brasil: America/Sao_Paulo)
        # Se since_hours fornecido, usa janela de horas; caso contrário, usa dia inteiro
        if since_hours:
            # Modo: últimas N horas
            cur.execute("""
                SELECT collector_name, ok, fetched, saved, error_code, error_message, duration_ms
                FROM sofia.collector_runs
                WHERE started_at >= NOW() - interval '%s hours'
                ORDER BY started_at DESC
            """, (since_hours,))
        else:
            # Modo: dia inteiro (timezone Brasil)
            cur.execute("""
                WITH day_bounds AS (
                    SELECT
                        date_trunc('day', %s::timestamp at time zone 'America/Sao_Paulo') AS start_br,
                        date_trunc('day', %s::timestamp at time zone 'America/Sao_Paulo') + interval '1 day' AS end_br
                )
                SELECT collector_name, ok, fetched, saved, error_code, error_message, duration_ms
                FROM sofia.collector_runs, day_bounds
                WHERE (started_at at time zone 'America/Sao_Paulo') >= day_bounds.start_br
                  AND (started_at at time zone 'America/Sao_Paulo') < day_bounds.end_br
                ORDER BY started_at DESC
            """, (audit_date, audit_date))
        runs = cur.fetchall()
        cur.close(); conn.close()

        ran_names = set()
        succeeded, failed_list, empty_list = [], [], []

        for name, is_ok, fetched, saved, err_code, err_msg, dur in runs:
            ran_names.add(name)
            entry = {"collector_id": name, "ok": is_ok, "fetched": fetched, "saved": saved,
                     "error_code": err_code, "duration_ms": dur}

            if not is_ok:
                # Falhou
                if include_details: entry["error_message"] = err_msg
                failed_list.append(entry)
            else:
                # OK=true, mas checar se empty
                exp_info = expected.get(name, {})
                exp_min = exp_info.get("min_records", 1)
                allow_empty = exp_info.get("allow_empty", False)

                if not allow_empty and (saved or 0) < exp_min:
                    # Rodou mas veio vazio/insuficiente
                    entry["expected_min"] = exp_min
                    empty_list.append(entry)
                else:
                    succeeded.append(entry)

        missing = [{"collector_id": cid, "path": info["path"], "expected_min": info["min_records"]}
                   for cid, info in expected.items() if cid not in ran_names]

        # Healthy = critérios objetivos
        health_check = {
            "missing_daily_collectors": len(missing),
            "failed_runs": len(failed_list),
            "empty_runs": len(empty_list),
        }
        healthy = all(health_check[k] <= HEALTHY_CRITERIA[k] for k in HEALTHY_CRITERIA)

        summary = {
            "expected": len(expected), "ran": len(ran_names),
            "succeeded": len(succeeded), "failed": len(failed_list),
            "missing": len(missing), "empty": len(empty_list),
        }

        # Preparar listas conforme flags
        succeeded_output = []
        if include_succeeded:
            if include_details:
                succeeded_output = succeeded
            else:
                succeeded_output = [{"collector_id": s["collector_id"], "saved": s.get("saved", 0), "duration_ms": s.get("duration_ms", 0)} for s in succeeded]

        data = {
            "date": audit_date if not since_hours else "last_{}_hours".format(since_hours),
            "summary": summary,
            "health_check": health_check,
            "healthy": healthy,
            "missing": missing,
            "succeeded": succeeded_output,
            "failed": failed_list if include_details else [{"collector_id": f["collector_id"], "error_code": f.get("error_code")} for f in failed_list],
            "empty": empty_list if include_details else [{"collector_id": z["collector_id"], "saved": z.get("saved", 0), "expected_min": z.get("expected_min", 1)} for z in empty_list],
        }

        warnings = []
        if not healthy:
            parts = []
            if missing: parts.append(f"{len(missing)} missing")
            if failed_list: parts.append(f"{len(failed_list)} failed")
            if empty_list: parts.append(f"{len(empty_list)} empty")
            warnings.append({"code": "AUDIT_NO_RUNS_TODAY", "message": ", ".join(parts)})

        return ok(data, start, warnings=warnings)
    except Exception as e:
        return fail("UNKNOWN_ERROR", str(e), start)
