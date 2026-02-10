"""Sofia Skill: budget.guard — Block por padrão quando custo excede limite."""

import os, time, psycopg2
from lib.helpers import ok, fail, DB_URL


def execute(trace_id, actor, dry_run, params, context):
    start = time.time()
    try:
        scope, scope_id = params["scope"], params["scope_id"]
        estimated = params.get("estimated_cost", 0)
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()

        cur.execute("SELECT limit_cost FROM sofia.budget_limits WHERE scope=%s AND scope_id=%s AND active=TRUE", (scope, scope_id))
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT limit_cost FROM sofia.budget_limits WHERE scope='day' AND scope_id='global' AND active=TRUE")
            row = cur.fetchone()
        limit_cost = float(row[0]) if row else 10.0

        if scope == "day":
            cur.execute("SELECT COALESCE(SUM(cost),0) FROM sofia.budget_usage WHERE scope=%s AND scope_id=%s AND created_at>=CURRENT_DATE", (scope, scope_id))
        else:
            cur.execute("SELECT COALESCE(SUM(cost),0) FROM sofia.budget_usage WHERE scope=%s AND scope_id=%s", (scope, scope_id))
        current = float(cur.fetchone()[0])
        cur.close(); conn.close()

        remaining = limit_cost - current
        allowed = (current + estimated) <= limit_cost
        data = {"allowed": allowed, "current_cost": current, "limit_cost": limit_cost,
                "remaining": max(0, remaining), "scope": scope, "scope_id": scope_id,
                "reason": "OK" if allowed else f"Exceeded: {current:.4f}+{estimated:.4f}>{limit_cost:.4f}"}

        if not allowed:
            return {"ok": False, "data": data, "warnings": [],
                    "errors": [{"code": "BUDGET_EXCEEDED", "message": data["reason"], "retryable": False}],
                    "meta": {"duration_ms": round((time.time()-start)*1000), "version": "1.0.0"}}

        warnings = []
        if remaining < limit_cost * 0.2:
            warnings.append({"code": "BUDGET_WARNING", "message": f"Only {remaining:.4f} remaining"})
        return ok(data, start, warnings=warnings)
    except Exception as e:
        return fail("UNKNOWN_ERROR", str(e), start)


def record_usage(trace_id, scope, scope_id, skill, provider, cost, tokens_in=0, tokens_out=0, requests=1):
    """Registra gasto após execução."""
    try:
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()
        cur.execute("INSERT INTO sofia.budget_usage (scope,scope_id,trace_id,skill,provider,cost,tokens_in,tokens_out,requests) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (scope, scope_id, trace_id, skill, provider, cost, tokens_in, tokens_out, requests))
        conn.commit(); cur.close(); conn.close()
    except Exception: pass
