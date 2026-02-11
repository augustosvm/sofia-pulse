"""Sofia Skill: logger.event — Logging JSON estruturado com trace_id.

Interface padrão: execute() — chamado pelo runner.
Convenience alias: log() — atalho para migração gradual de prints.
O runner SEMPRE chama execute(). Nunca log().
"""

import json, time, os, logging
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from lib.helpers import ok, fail, SOFIA_LOG_DIR

_loggers = {}


def _get_logger(skill: str) -> logging.Logger:
    if skill in _loggers:
        return _loggers[skill]
    lg = logging.getLogger(f"sofia.{skill}")
    lg.setLevel(logging.DEBUG)
    if not lg.handlers:
        fh = TimedRotatingFileHandler(
            os.path.join(SOFIA_LOG_DIR, f"{skill}.log"),
            when="midnight", backupCount=30, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(message)s"))
        lg.addHandler(fh)
        lg.addHandler(logging.StreamHandler())
    _loggers[skill] = lg
    return lg


def execute(trace_id, actor, dry_run, params, context):
    """Interface padrão. Chamado pelo runner."""
    start = time.time()
    try:
        level = params.get("level", "info")
        event = params.get("event", "unknown")
        skill = params.get("skill", "unknown")
        entry = json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(), "level": level,
            "event": event, "skill": skill, "trace_id": trace_id,
            "actor": actor, "env": context.get("env"),
            "message": params.get("message", ""), **params.get("fields", {})
        }, ensure_ascii=False, default=str)
        if not dry_run:
            getattr(_get_logger(skill), level if level != "critical" else "critical", _get_logger(skill).info)(entry)
        return ok({"logged": not dry_run, "log_path": os.path.join(SOFIA_LOG_DIR, f"{skill}.log")}, start)
    except Exception as e:
        return fail("UNKNOWN_ERROR", str(e), start)


# --- Convenience alias (NÃO é a interface padrão, é atalho para migração) ---

def log(trace_id, skill, event, level="info", message="", actor="system", env="prod", **fields):
    """
    Atalho para migração gradual de print() nos collectors existentes.
    NÃO é chamado pelo runner. Uso direto:
        from skills.logger_event.src import log
        log(trace_id, "collect.run", "collector.started", fetched=150)
    """
    return execute(trace_id, actor, False,
                   {"level": level, "event": event, "skill": skill, "message": message, "fields": fields},
                   {"env": env})
