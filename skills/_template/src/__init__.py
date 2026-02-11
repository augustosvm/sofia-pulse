"""Sofia Skill: _template"""
import time
from lib.helpers import ok, fail

def execute(trace_id, actor, dry_run, params, context):
    start = time.time()
    try:
        if dry_run: return ok({"dry_run": True}, start)
        # REPLACE: lógica aqui
        return ok({"result": "done"}, start)
    except Exception as e:
        return fail("UNKNOWN_ERROR", str(e), start)
