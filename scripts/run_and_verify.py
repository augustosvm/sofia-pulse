#!/usr/bin/env python3
"""
Sofia Skills Kit - Run and Verify (Execution + Immediate Audit + WhatsApp)
Executa collectors, verifica imediatamente e notifica via WhatsApp com prova objetiva.
"""

import sys
import os
import uuid
import json
import time
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.skill_runner import run


def execute_collector(cid, config, trace, max_retries=2):
    """Executa um collector com retry."""
    timeout_ms = config.get("timeout_s", 300) * 1000

    for attempt in range(1, max_retries + 1):
        result = run("collect.run", {
            "collector_id": cid,
            "timeout_ms": timeout_ms
        }, trace_id=trace)

        if result["ok"]:
            return {
                "collector_id": cid,
                "ok": True,
                "fetched": result["data"].get("fetched", 0),
                "saved": result["data"].get("saved", 0),
                "duration_ms": result["meta"].get("duration_ms", 0)
            }

        # Erro - verificar se retryable
        error_code = result["errors"][0].get("code", "UNKNOWN") if result["errors"] else "UNKNOWN"
        retryable = result["errors"][0].get("retryable", False) if result["errors"] else False

        if retryable and error_code == "COLLECT_SOURCE_DOWN" and attempt < max_retries:
            print(f"    ⚠️ {cid} failed (attempt {attempt}/{max_retries}), retrying...")
            time.sleep(5)
            continue

        # Falha final
        return {
            "collector_id": cid,
            "ok": False,
            "error_code": error_code,
            "attempt": attempt
        }

    # Max retries atingido
    return {
        "collector_id": cid,
        "ok": False,
        "error_code": error_code,
        "max_retries_exceeded": True
    }


def execute_batch(collectors_config, group_name, trace, max_parallel=3):
    """Executa um lote de collectors com concorrência limitada."""
    results = []

    if not collectors_config:
        return results

    print(f"\n[run_and_verify] === Group: {group_name} ({len(collectors_config)} collectors) ===")

    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        future_to_cid = {
            executor.submit(execute_collector, c["collector_id"], c, trace): c["collector_id"]
            for c in collectors_config
        }

        for future in as_completed(future_to_cid):
            cid = future_to_cid[future]
            try:
                result = future.result()
                results.append(result)

                if result["ok"]:
                    print(f"  ✅ {cid}: saved={result['saved']} ({result['duration_ms']}ms)")
                else:
                    print(f"  ❌ {cid}: {result.get('error_code', 'UNKNOWN')}")
            except Exception as e:
                print(f"  ❌ {cid}: Exception: {e}")
                results.append({
                    "collector_id": cid,
                    "ok": False,
                    "error_code": "UNKNOWN_ERROR",
                    "exception": str(e)
                })

    return results


def build_whatsapp_message(trace_id, audit_data, gate_status, max_offenders=12):
    """Compõe mensagem WhatsApp operacional."""
    summary = audit_data["summary"]
    failed = audit_data.get("failed", [])
    empty = audit_data.get("empty", [])
    succeeded = audit_data.get("succeeded", [])

    # Header
    status_emoji = "✅" if gate_status["healthy"] else "🚨"
    gate_emoji = "✅ HEALTHY" if gate_status["healthy"] else "🚨 UNHEALTHY"

    message = f"{status_emoji} *Sofia Pulse - Execução & Verificação*\n"
    message += f"Trace: `{trace_id[:8]}`\n"
    message += f"Janela: BRT {time.strftime('%Y-%m-%d %H:%M')}\n\n"

    message += f"*Gate (Required+GA4):* {gate_emoji}\n"
    message += f"*Resumo Execução (ALL):* Expected={summary['expected']} | Ran={summary['ran']} | OK={summary['succeeded']} | Failed={summary['failed']} | Empty={summary['empty']} | Missing={summary['missing']}\n\n"

    # Top Falhas
    if failed:
        message += f"*Top Falhas (máx {min(8, len(failed))})
:*\n"
        for f in failed[:8]:
            error_code = f.get("error_code", "UNKNOWN")
            message += f"• {f['collector_id']} — `{error_code}`\n"
        if len(failed) > 8:
            message += f"... e {len(failed) - 8} mais\n"
        message += "\n"

    # Top Vazios
    if empty:
        message += f"*Top Vazios (máx {min(5, len(empty))}):*\n"
        for e in empty[:5]:
            saved = e.get("saved", 0)
            expected_min = e.get("expected_min", 1)
            message += f"• {e['collector_id']} — saved={saved} (min={expected_min})\n"
        if len(empty) > 5:
            message += f"... e {len(empty) - 5} mais\n"
        message += "\n"

    # Top Sucessos
    if succeeded:
        message += f"*Top Sucessos (máx {min(5, len(succeeded))}):*\n"
        for s in succeeded[:5]:
            saved = s.get("saved", 0)
            message += f"• {s['collector_id']} — saved={saved}\n"
        if len(succeeded) > 5:
            message += f"... e {len(succeeded) - 5} mais\n"

    return message


def main():
    start_time = time.time()
    trace = str(uuid.uuid4())

    print(f"[run_and_verify] ========================================")
    print(f"[run_and_verify] Starting Run & Verify Pipeline")
    print(f"[run_and_verify] Trace: {trace}")
    print(f"[run_and_verify] ========================================\n")

    # Env vars
    sync_expected = os.environ.get("SOFIA_PIPELINE_SYNC_EXPECTED", "false").lower() == "true"
    verify_all = os.environ.get("SOFIA_PIPELINE_VERIFY_ALL", "true").lower() == "true"
    always_notify = os.environ.get("SOFIA_WPP_ALWAYS_NOTIFY", "true").lower() == "true"
    wpp_to = os.environ.get("SOFIA_WPP_TO", "admin")
    max_offenders = int(os.environ.get("SOFIA_MAX_OFFENDERS", "12"))
    execution_set_mode = os.environ.get("SOFIA_EXECUTION_SET_MODE", "all")

    # 1. Sync expected set (opcional)
    if sync_expected:
        print("[run_and_verify] Running sync_expected_set.py...")
        sync_script = Path(__file__).resolve().parent / "sync_expected_set.py"
        try:
            subprocess.run([sys.executable, str(sync_script)], check=True)
            print("[run_and_verify] ✅ Sync completed\n")
        except subprocess.CalledProcessError as e:
            print(f"[run_and_verify] ⚠️ Sync failed: {e}\n")

    # 2. Ler config de execution set
    project_root = Path(__file__).resolve().parents[1]
    config_path = project_root / "config" / "daily_expected_collectors.json"

    if not config_path.exists():
        print(f"[run_and_verify] ❌ Config not found: {config_path}")
        sys.exit(1)

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"[run_and_verify] ❌ Failed to read config: {e}")
        sys.exit(1)

    groups = config.get("groups", {})
    print(f"[run_and_verify] Loaded config with {len(groups)} groups\n")

    # 3. Executar collectors por grupo
    all_results = []
    all_collector_ids = []

    # Group 1: Required (sequencial)
    if "required" in groups and groups["required"]:
        required_results = execute_batch(groups["required"], "required", trace, max_parallel=1)
        all_results.extend(required_results)
        all_collector_ids.extend([c["collector_id"] for c in groups["required"]])

    # Group 2: GA4 (com budget control)
    if "ga4" in groups and groups["ga4"]:
        # Budget guard
        print(f"\n[run_and_verify] Running budget.guard for GA4...")
        budget_result = run("budget.guard", {
            "action": "check",
            "skill": "ga4-collectors",
            "estimated_cost": 0.50
        }, trace_id=trace)

        if budget_result["ok"] and budget_result["data"].get("allowed", False):
            print(f"  ✅ Budget OK, proceeding with GA4")
            ga4_results = execute_batch(groups["ga4"], "ga4", trace, max_parallel=2)
            all_results.extend(ga4_results)
            all_collector_ids.extend([c["collector_id"] for c in groups["ga4"]])
        else:
            print(f"  ❌ Budget exceeded, skipping GA4")
            for ga4_collector in groups["ga4"]:
                all_results.append({
                    "collector_id": ga4_collector["collector_id"],
                    "ok": False,
                    "error_code": "BUDGET_EXCEEDED",
                    "skipped": True
                })
                all_collector_ids.append(ga4_collector["collector_id"])

    # Group 3+: Best-effort (paralelo)
    for group_name in ["tech", "research", "jobs", "patents", "other"]:
        if group_name in groups and groups[group_name]:
            batch_results = execute_batch(groups[group_name], group_name, trace, max_parallel=3)
            all_results.extend(batch_results)
            all_collector_ids.extend([c["collector_id"] for c in groups[group_name]])

    # 4. IMEDIATO: Auditoria
    print(f"\n[run_and_verify] ========================================")
    print(f"[run_and_verify] IMMEDIATE AUDIT")
    print(f"[run_and_verify] ========================================")

    expected_collectors = all_collector_ids if verify_all else None
    audit_result = run("runs.audit", {
        "expected_collectors": expected_collectors,
        "since_hours": 2,  # Últimas 2 horas (acabou de rodar)
        "include_succeeded": True,
        "include_details": False
    }, trace_id=trace)

    if not audit_result["ok"]:
        print(f"[run_and_verify] ❌ Audit failed: {audit_result['errors']}")
        sys.exit(1)

    audit_data = audit_result["data"]
    summary = audit_data["summary"]

    print(f"\n[run_and_verify] Audit Summary:")
    print(f"  Expected: {summary['expected']}")
    print(f"  Ran: {summary['ran']}")
    print(f"  Succeeded: {summary['succeeded']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Empty: {summary['empty']}")
    print(f"  Missing: {summary['missing']}")

    # 5. Determinar gate status (required + GA4 apenas)
    required_ids = []
    if "required" in groups:
        required_ids.extend([c["collector_id"] for c in groups["required"]])
    if "ga4" in groups:
        required_ids.extend([c["collector_id"] for c in groups["ga4"]])

    # Verificar se required+GA4 estão healthy
    gate_failed = [f for f in audit_data.get("failed", []) if f["collector_id"] in required_ids]
    gate_empty = [e for e in audit_data.get("empty", []) if e["collector_id"] in required_ids]
    gate_missing = [m for m in audit_data.get("missing", []) if m["collector_id"] in required_ids]

    gate_healthy = len(gate_failed) == 0 and len(gate_empty) == 0 and len(gate_missing) == 0

    gate_status = {
        "healthy": gate_healthy,
        "required_failed": len(gate_failed),
        "required_empty": len(gate_empty),
        "required_missing": len(gate_missing)
    }

    print(f"\n[run_and_verify] Gate Status (Required+GA4): {'✅ HEALTHY' if gate_healthy else '🚨 UNHEALTHY'}")
    if not gate_healthy:
        print(f"  Failed: {len(gate_failed)}")
        print(f"  Empty: {len(gate_empty)}")
        print(f"  Missing: {len(gate_missing)}")

    # 6. Compor e enviar WhatsApp
    if always_notify:
        print(f"\n[run_and_verify] ========================================")
        print(f"[run_and_verify] WHATSAPP NOTIFICATION")
        print(f"[run_and_verify] ========================================")

        message = build_whatsapp_message(trace, audit_data, gate_status, max_offenders)

        severity = "critical" if not gate_healthy else "warning"
        title = "🚨 Sofia Pulse - UNHEALTHY" if not gate_healthy else "✅ Sofia Pulse - Execução OK"

        # Enviar
        wpp_result = run("notify.whatsapp", {
            "to": wpp_to,
            "severity": severity,
            "title": title,
            "message": message,
            "summary": {
                "trace_id": trace,
                "execution_set_count": len(all_collector_ids),
                "ran": summary["ran"],
                "succeeded": summary["succeeded"],
                "failed": summary["failed"],
                "gate_healthy": gate_healthy
            }
        }, trace_id=trace)

        if wpp_result["ok"]:
            print(f"[run_and_verify] ✅ WhatsApp notification sent to {wpp_to}")
        else:
            print(f"[run_and_verify] ⚠️ WhatsApp notification failed: {wpp_result.get('errors', [])}")

    # 7. Output final JSON
    duration_ms = int((time.time() - start_time) * 1000)

    output = {
        "trace_id": trace,
        "execution_set_count": len(all_collector_ids),
        "audit_summary": summary,
        "health_gate_ok": gate_healthy,
        "whatsapp_sent": always_notify,
        "duration_ms": duration_ms
    }

    print(f"\n[run_and_verify] ========================================")
    print(f"[run_and_verify] FINAL OUTPUT")
    print(f"[run_and_verify] ========================================")
    print(json.dumps(output, indent=2))

    # 8. Exit code
    exit_code = 0 if gate_healthy else 1
    print(f"\n[run_and_verify] Exiting with code {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
