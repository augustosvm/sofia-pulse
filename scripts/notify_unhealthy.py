#!/usr/bin/env python3
"""
Sofia Skills Kit - Notify Unhealthy
Envia alerta WhatsApp se daily pipeline estiver unhealthy.
Usado após daily_pipeline para notificação sem spam.

MODOS:
  --gate (default): Apenas required+GA4 (sem spam)
  --all: Relatório completo de execução (todos collectors)

DEDUPE:
  - Usa sofia.notifications_sent com channel='whatsapp'
  - Dedupe por (date_brt + message_hash + purpose)
  - Purposes: daily_gate, daily_all, run_verify
"""

import sys
import os
import json
import uuid
import argparse
import hashlib
from pathlib import Path
from datetime import date

# Adicionar path do projeto (relativo ao arquivo)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.skill_runner import run


def check_dedupe(message_hash, purpose, trace_id):
    """Verifica se mensagem já foi enviada hoje (dedupe)."""
    import psycopg2

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("[notify_unhealthy] ⚠️ DATABASE_URL not set, skipping dedupe check")
        return True  # Permitir envio se não tem DB

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # Check if already sent today (BRT timezone)
        cur.execute("""
            SELECT 1 FROM sofia.notifications_sent
            WHERE date_brt = CURRENT_DATE
              AND channel = 'whatsapp'
              AND message_hash = %s
        """, (message_hash,))

        if cur.fetchone():
            cur.close()
            conn.close()
            return False  # Já enviado hoje

        # Record que estamos enviando
        cur.execute("""
            INSERT INTO sofia.notifications_sent (
                date_brt, channel, message_hash, recipient, severity,
                title, message_preview, trace_id
            )
            VALUES (
                CURRENT_DATE, 'whatsapp', %s, 'admin', 'critical',
                %s, %s, %s
            )
            ON CONFLICT (date_brt, channel, message_hash) DO NOTHING
        """, (message_hash, purpose, purpose[:200], trace_id))

        conn.commit()
        cur.close()
        conn.close()

        return True  # Pode enviar

    except Exception as e:
        print(f"[notify_unhealthy] ⚠️ Dedupe check failed: {e}")
        return True  # Em caso de erro, permitir envio


def main():
    # Parse args
    parser = argparse.ArgumentParser(description="Notificar unhealthy via WhatsApp")
    parser.add_argument("--gate", action="store_true", help="Modo gate (required+GA4 apenas)")
    parser.add_argument("--all", action="store_true", help="Modo all (relatório completo)")
    args = parser.parse_args()

    # Default: gate mode
    if not args.gate and not args.all:
        args.gate = True

    mode = "gate" if args.gate else "all"
    purpose = f"daily_{mode}"

    trace = str(uuid.uuid4())
    print(f"[notify_unhealthy] Starting (mode={mode}, trace={trace})")

    # 1. Ler expected set
    config_path = Path(__file__).resolve().parents[1] / "config" / "daily_expected_collectors.json"

    if not config_path.exists():
        print(f"[notify_unhealthy] ⚠️ Config not found: {config_path}")
        sys.exit(0)

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"[notify_unhealthy] ⚠️ Failed to read config: {e}")
        sys.exit(0)

    # Determinar expected collectors baseado no modo
    if mode == "gate":
        # Apenas required + GA4
        expected_collectors = []
        groups = config.get("groups", {})

        if "required" in groups:
            expected_collectors.extend([c["collector_id"] for c in groups["required"]])
        if "ga4" in groups:
            expected_collectors.extend([c["collector_id"] for c in groups["ga4"]])

        print(f"[notify_unhealthy] Mode: gate (required+GA4), {len(expected_collectors)} collectors")
    else:
        # Todos os collectors do execution set
        groups = config.get("groups", {})
        expected_collectors = []

        for group_collectors in groups.values():
            expected_collectors.extend([c["collector_id"] for c in group_collectors])

        print(f"[notify_unhealthy] Mode: all, {len(expected_collectors)} collectors")

    if not expected_collectors:
        print("[notify_unhealthy] ⚠️ No expected collectors found")
        sys.exit(0)

    # 2. Rodar audit
    audit = run("runs.audit", {
        "include_details": False,
        "include_succeeded": (mode == "all"),
        "expected_collectors": expected_collectors
    }, trace_id=trace)

    if not audit["ok"]:
        print(f"[notify_unhealthy] ❌ Audit failed: {audit['errors']}")
        sys.exit(0)

    data = audit["data"]
    summary = data["summary"]
    healthy = data["healthy"]

    print(f"[notify_unhealthy] Audit summary: {json.dumps(summary)}")
    print(f"[notify_unhealthy] Healthy: {healthy}")

    # 3. Se gate mode + healthy, não notifica
    if mode == "gate" and healthy:
        print("[notify_unhealthy] ✅ Gate healthy, no alert needed")
        sys.exit(0)

    # 4. Construir mensagem
    missing = data.get("missing", [])
    failed = data.get("failed", [])
    empty = data.get("empty", [])
    succeeded = data.get("succeeded", [])

    if mode == "gate":
        # Mensagem de alerta crítico
        alert_parts = []
        alert_parts.append(f"*Expected:* {summary['expected']} | *Ran:* {summary['ran']} | *Succeeded:* {summary['succeeded']}")
        alert_parts.append("")

        if missing:
            alert_parts.append(f"*Missing ({len(missing)}):*")
            for m in missing[:5]:
                alert_parts.append(f"• {m['collector_id']}")
            if len(missing) > 5:
                alert_parts.append(f"...and {len(missing) - 5} more")
            alert_parts.append("")

        if failed:
            alert_parts.append(f"*Failed ({len(failed)}):*")
            for f in failed[:5]:
                error_code = f.get("error_code", "UNKNOWN")
                alert_parts.append(f"• {f['collector_id']}: {error_code}")
            if len(failed) > 5:
                alert_parts.append(f"...and {len(failed) - 5} more")
            alert_parts.append("")

        if empty:
            alert_parts.append(f"*Empty ({len(empty)}):*")
            for e in empty[:5]:
                saved = e.get("saved", 0)
                expected = e.get("expected_min", 1)
                alert_parts.append(f"• {e['collector_id']}: saved={saved}, expected>={expected}")
            if len(empty) > 5:
                alert_parts.append(f"...and {len(empty) - 5} more")
            alert_parts.append("")

        alert_parts.append("_Check logs for details_")

        message_body = "\n".join(alert_parts)
        title = "Sofia Pulse - Daily Pipeline UNHEALTHY"
        severity = "critical"

    else:
        # Mensagem de relatório completo
        alert_parts = []
        alert_parts.append(f"*Resumo Execução (ALL):*")
        alert_parts.append(f"Expected={summary['expected']} | Ran={summary['ran']} | OK={summary['succeeded']} | Failed={summary['failed']} | Empty={summary['empty']} | Missing={summary['missing']}")
        alert_parts.append("")

        if failed:
            alert_parts.append(f"*Top Falhas ({len(failed)}):*")
            for f in failed[:8]:
                error_code = f.get("error_code", "UNKNOWN")
                alert_parts.append(f"• {f['collector_id']} — `{error_code}`")
            if len(failed) > 8:
                alert_parts.append(f"...and {len(failed) - 8} more")
            alert_parts.append("")

        if empty:
            alert_parts.append(f"*Top Vazios ({len(empty)}):*")
            for e in empty[:5]:
                saved = e.get("saved", 0)
                expected = e.get("expected_min", 1)
                alert_parts.append(f"• {e['collector_id']} — saved={saved} (min={expected})")
            if len(empty) > 5:
                alert_parts.append(f"...and {len(empty) - 5} more")
            alert_parts.append("")

        if succeeded and len(succeeded) > 0:
            alert_parts.append(f"*Top Sucessos ({min(5, len(succeeded))}):*")
            for s in succeeded[:5]:
                saved = s.get("saved", 0)
                alert_parts.append(f"• {s['collector_id']} — saved={saved}")
            if len(succeeded) > 5:
                alert_parts.append(f"...and {len(succeeded) - 5} more")

        message_body = "\n".join(alert_parts)
        title = "Sofia Pulse - Daily Execution Report"
        severity = "warning" if healthy else "critical"

    # 5. Dedupe check
    message_hash = hashlib.sha256(message_body.encode()).hexdigest()

    if not check_dedupe(message_hash, purpose, trace):
        print(f"[notify_unhealthy] ⏭️ Skipped (already sent today, purpose={purpose})")
        sys.exit(0)

    # 6. Enviar via notify.whatsapp skill
    print(f"[notify_unhealthy] Sending WhatsApp alert (purpose={purpose})...")

    result = run("notify.whatsapp", {
        "to": "admin",
        "severity": severity,
        "title": title,
        "message": message_body,
        "summary": {
            "Expected": summary['expected'],
            "Ran": summary['ran'],
            "Succeeded": summary['succeeded'],
            "Missing": len(missing),
            "Failed": len(failed),
            "Empty": len(empty),
            "Mode": mode
        }
    }, trace_id=trace)

    if result["ok"]:
        print(f"[notify_unhealthy] ✅ WhatsApp alert sent")
        success = True
    else:
        error_msg = result["errors"][0]["message"] if result["errors"] else "Unknown error"
        print(f"[notify_unhealthy] ❌ WhatsApp alert failed: {error_msg}")
        success = False

    # Log evento
    run("logger.event", {
        "level": "error" if not healthy else "info",
        "event": "notify_unhealthy.alert_sent" if success else "notify_unhealthy.alert_failed",
        "skill": "notify_unhealthy",
        "mode": mode,
        "purpose": purpose,
        "missing": len(missing),
        "failed": len(failed),
        "empty": len(empty),
        "whatsapp_success": success
    }, trace_id=trace)

    sys.exit(0)  # Sempre exit 0 (notificação é best-effort)


if __name__ == "__main__":
    main()
