"""
Sofia Skills — Shared Helpers
Importado por todas as skills para evitar duplicação de envelope/meta.
"""

import time
import os

VERSION = "1.2.0"

# Log dir com fallback
SOFIA_LOG_DIR = os.getenv("SOFIA_LOG_DIR", "/var/log/sofia")
if not os.access(SOFIA_LOG_DIR, os.W_OK):
    SOFIA_LOG_DIR = os.getenv("SOFIA_LOG_FALLBACK", "/tmp/sofia")
os.makedirs(SOFIA_LOG_DIR, exist_ok=True)

DB_URL = os.getenv("DATABASE_URL")

# Autodoc disabled by default — docs only on demand
SOFIA_AUTODOC = os.getenv("SOFIA_AUTODOC", "false").lower() == "true"


def ok(data: dict, start: float, version: str = VERSION, warnings: list = None, cost_estimate: float = 0) -> dict:
    return {
        "ok": True, "data": data, "warnings": warnings or [], "errors": [],
        "meta": {"duration_ms": round((time.time() - start) * 1000), "version": version,
                 "cost_estimate": cost_estimate, "cost_confidence": "high" if cost_estimate == 0 else "medium"},
    }


def fail(code: str, message: str, start: float, version: str = VERSION, retryable: bool = False) -> dict:
    return {
        "ok": False, "data": None, "warnings": [],
        "errors": [{"code": code, "message": message, "retryable": retryable}],
        "meta": {"duration_ms": round((time.time() - start) * 1000), "version": version},
    }
