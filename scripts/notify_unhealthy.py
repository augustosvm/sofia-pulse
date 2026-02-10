#!/usr/bin/env python3
"""
Sofia Skills Kit - Notify Unhealthy
Envia alerta WhatsApp se daily pipeline estiver unhealthy.
Usado após daily_pipeline para notificação sem spam.
"""

import sys
import json
import uuid
from pathlib import Path

# Adicionar path do projeto (relativo ao arquivo)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.skill_runner import run


def main():
    trace = str(uuid.uuid4())
    print(f"[notify_unhealthy] Starting (trace={trace})")

    # 1. Ler expected set
    config_path = Path(__file__).resolve().parents[1] / "config" / "daily_expected_collectors.json"

    if not config_path.exists():
        print(f"[notify_unhealthy] ⚠️ Config not found: {config_path}")
        sys.exit(0)  # Não falhar, apenas não notificar

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            expected_collectors = config.get("collectors", [])
    except Exception as e:
        print(f"[notify_unhealthy] ⚠️ Failed to read config: {e}")
        sys.exit(0)

    # 2. Rodar audit com expected set
    audit = run("runs.audit", {
        "include_details": True,
        "expected_collectors": expected_collectors
    }, trace_id=trace)

    if not audit["ok"]:
        print(f"[notify_unhealthy] ❌ Audit failed: {audit['errors']}")
        sys.exit(0)  # Não falhar, audit já logou erro

    data = audit["data"]
    summary = data["summary"]
    healthy = data["healthy"]

    print(f"[notify_unhealthy] Audit summary: {json.dumps(summary)}")
    print(f"[notify_unhealthy] Healthy: {healthy}")

    # 3. Se healthy, não notifica
    if healthy:
        print("[notify_unhealthy] ✅ System healthy, no alert needed")
        sys.exit(0)

    # 4. Construir mensagem de alerta
    missing = data.get("missing", [])
    failed = data.get("failed", [])
    empty = data.get("empty", [])

    # Construir corpo da mensagem
    alert_parts = []
    alert_parts.append(f"*Expected:* {summary['expected']} | *Ran:* {summary['ran']} | *Succeeded:* {summary['succeeded']}")
    alert_parts.append("")  # Linha em branco

    if missing:
        alert_parts.append(f"*Missing ({len(missing)}):*")
        for m in missing[:3]:  # Top 3
            alert_parts.append(f"• {m['collector_id']}")
        if len(missing) > 3:
            alert_parts.append(f"...and {len(missing) - 3} more")
        alert_parts.append("")

    if failed:
        alert_parts.append(f"*Failed ({len(failed)}):*")
        for f in failed[:3]:
            error_code = f.get("error_code", "UNKNOWN")
            alert_parts.append(f"• {f['collector_id']}: {error_code}")
        if len(failed) > 3:
            alert_parts.append(f"...and {len(failed) - 3} more")
        alert_parts.append("")

    if empty:
        alert_parts.append(f"*Empty ({len(empty)}):*")
        for e in empty[:3]:
            saved = e.get("saved", 0)
            expected = e.get("expected_min", 1)
            alert_parts.append(f"• {e['collector_id']}: saved={saved}, expected>={expected}")
        if len(empty) > 3:
            alert_parts.append(f"...and {len(empty) - 3} more")
        alert_parts.append("")

    alert_parts.append("_Check logs for details_")

    message_body = "\n".join(alert_parts)

    # 5. Enviar via notify.whatsapp skill
    print("[notify_unhealthy] Sending WhatsApp alert...")

    result = run("notify.whatsapp", {
        "to": "admin",
        "severity": "critical",
        "title": "Sofia Pulse - Daily Pipeline UNHEALTHY",
        "message": message_body,
        "summary": {
            "Expected": summary['expected'],
            "Ran": summary['ran'],
            "Succeeded": summary['succeeded'],
            "Missing": len(missing),
            "Failed": len(failed),
            "Empty": len(empty)
        }
    }, trace_id=trace)

    if result["ok"]:
        print(f"[notify_unhealthy] ✅ WhatsApp alert sent to {result['data']['to']}")
        success = True
    else:
        error_msg = result["errors"][0]["message"] if result["errors"] else "Unknown error"
        print(f"[notify_unhealthy] ❌ WhatsApp alert failed: {error_msg}")
        success = False

    # Log evento
    run("logger.event", {
        "level": "error",
        "event": "notify_unhealthy.alert_sent" if success else "notify_unhealthy.alert_failed",
        "skill": "notify_unhealthy",
        "missing": len(missing),
        "failed": len(failed),
        "empty": len(empty),
        "whatsapp_success": success
    }, trace_id=trace)

    sys.exit(0)  # Sempre exit 0 (notificação é best-effort)


if __name__ == "__main__":
    main()
