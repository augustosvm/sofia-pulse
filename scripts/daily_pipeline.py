#!/usr/bin/env python3
"""
Sofia Skills Kit - Daily Pipeline (v2 - Batch Execution)
Executa collectors em lotes com prioridades + budget control.
"""

import sys
import uuid
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Adicionar path do projeto (relativo ao arquivo)
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
            time.sleep(5)  # Wait before retry
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

    print(f"\n[daily_pipeline] === Group: {group_name} ({len(collectors_config)} collectors) ===")

    # Executar com ThreadPoolExecutor
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
                    print(f"  ✅ {cid}: saved={result['saved']}, fetched={result['fetched']} ({result['duration_ms']}ms)")
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


def main():
    trace = str(uuid.uuid4())
    print(f"[daily_pipeline] Starting pipeline v2 (trace={trace})")

    # 1. Ler config com grupos
    config_path = Path(__file__).resolve().parents[1] / "config" / "daily_expected_collectors.json"

    if not config_path.exists():
        print(f"[daily_pipeline] ❌ Config not found: {config_path}")
        sys.exit(1)

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"[daily_pipeline] ❌ Failed to read config: {e}")
        sys.exit(1)

    # Verificar se é formato novo (com groups) ou legacy
    if "groups" in config:
        groups = config["groups"]
        stats = config.get("_stats", {})
        print(f"[daily_pipeline] Loaded config (grouped format)")
        print(f"  Total allowed: {stats.get('total_allowed', 'N/A')}")
        print(f"  Total blocked: {stats.get('total_blocked', 'N/A')}")
        print(f"  Required count: {stats.get('required_count', 'N/A')}")
    else:
        # Fallback para formato legacy
        print(f"[daily_pipeline] ⚠️ Using legacy config format (no groups)")
        collectors_list = config.get("collectors", [])
        groups = {
            "required": [{"collector_id": c, "required": True, "timeout_s": 300} for c in collectors_list]
        }

    # 2. Executar grupo REQUIRED primeiro (sequencial, com retry)
    print(f"\n[daily_pipeline] ========================================")
    print(f"[daily_pipeline] PHASE 1: Required collectors")
    print(f"[daily_pipeline] ========================================")

    required_results = []
    if "required" in groups:
        required_results = execute_batch(groups["required"], "required", trace, max_parallel=1)

    # 3. Executar grupo GA4 (com budget.guard)
    print(f"\n[daily_pipeline] ========================================")
    print(f"[daily_pipeline] PHASE 2: GA4 collectors (with budget control)")
    print(f"[daily_pipeline] ========================================")

    ga4_results = []
    if "ga4" in groups and groups["ga4"]:
        # Budget guard antes de GA4
        print(f"[daily_pipeline] Running budget.guard...")
        budget_result = run("budget.guard", {
            "action": "check",
            "skill": "ga4-collectors",
            "estimated_cost": 0.50  # Estimativa conservadora
        }, trace_id=trace)

        if budget_result["ok"] and budget_result["data"].get("allowed", False):
            print(f"  ✅ Budget OK, proceeding with GA4")
            ga4_results = execute_batch(groups["ga4"], "ga4", trace, max_parallel=2)
        else:
            print(f"  ❌ Budget exceeded, skipping GA4")
            for ga4_collector in groups["ga4"]:
                ga4_results.append({
                    "collector_id": ga4_collector["collector_id"],
                    "ok": False,
                    "error_code": "BUDGET_EXCEEDED",
                    "skipped": True
                })

    # 4. Executar demais grupos (paralelo, best-effort)
    print(f"\n[daily_pipeline] ========================================")
    print(f"[daily_pipeline] PHASE 3: Other collectors (best-effort)")
    print(f"[daily_pipeline] ========================================")

    other_results = []
    for group_name in ["tech", "research", "jobs", "patents", "other"]:
        if group_name in groups and groups[group_name]:
            batch_results = execute_batch(groups[group_name], group_name, trace, max_parallel=3)
            other_results.extend(batch_results)

    # 5. Consolidar resultados
    all_results = required_results + ga4_results + other_results
    succeeded = [r for r in all_results if r["ok"]]
    failed = [r for r in all_results if not r["ok"]]

    print(f"\n[daily_pipeline] ========================================")
    print(f"[daily_pipeline] EXECUTION SUMMARY")
    print(f"[daily_pipeline] ========================================")
    print(f"  Total: {len(all_results)}")
    print(f"  Succeeded: {len(succeeded)}")
    print(f"  Failed: {len(failed)}")

    # 6. Normalize & Aggregate (PHASE 4)
    print(f"\n[daily_pipeline] ========================================")
    print(f"[daily_pipeline] PHASE 4: Normalize & Aggregate")
    print(f"[daily_pipeline] ========================================")

    # 6.1 Normalize research domain (incremental)
    print(f"[daily_pipeline] Running data.normalize (research, incremental)...")
    normalize_result = run("data.normalize", {
        "domain": "research",
        "mode": "incremental"
    }, trace_id=trace)

    if normalize_result["ok"]:
        norm_data = normalize_result["data"]
        print(f"  ✅ Normalized research: inserted={norm_data['inserted']}, updated={norm_data['updated']} ({norm_data['duration_ms']}ms)")
    else:
        print(f"  ⚠️ Normalization failed: {normalize_result.get('errors', [])}")

    # 6.2 Aggregate research monthly (incremental)
    print(f"[daily_pipeline] Running facts.aggregate (research_monthly_summary, incremental)...")
    aggregate_result = run("facts.aggregate", {
        "aggregation": "research_monthly_summary",
        "mode": "incremental"
    }, trace_id=trace)

    if aggregate_result["ok"]:
        agg_data = aggregate_result["data"]
        print(f"  ✅ Aggregated research: records={agg_data['total_records']}, grain={agg_data['grain_count']} ({agg_data['duration_ms']}ms)")
    else:
        print(f"  ⚠️ Aggregation failed: {aggregate_result.get('errors', [])}")

    # 7. Generate Insights (PHASE 5)
    print(f"\n[daily_pipeline] ========================================")
    print(f"[daily_pipeline] PHASE 5: Generate Insights")
    print(f"[daily_pipeline] ========================================")

    # Load domains from config
    insights_config_path = Path(__file__).resolve().parents[1] / "config" / "insights_domains.json"
    if insights_config_path.exists():
        with open(insights_config_path, "r") as f:
            insights_config = json.load(f)
            enabled_domains = insights_config.get("enabled_domains", ["research"])
    else:
        enabled_domains = ["research"]

    print(f"[daily_pipeline] Running insights.generate (domains={enabled_domains})...")
    insights_result = run("insights.generate", {
        "domains": enabled_domains
    }, trace_id=trace)

    if insights_result["ok"]:
        ins_data = insights_result["data"]
        print(f"  ✅ Insights generated: {ins_data['insights_generated']}")
        print(f"     By severity: info={ins_data['by_severity']['info']}, warning={ins_data['by_severity']['warning']}, critical={ins_data['by_severity']['critical']}")

        # Send WhatsApp alert if critical insights or high volume
        critical_count = ins_data['by_severity'].get('critical', 0)
        total_insights = ins_data['insights_generated']

        if critical_count > 0 or total_insights >= 5:
            print(f"  📱 Sending WhatsApp alert (critical={critical_count}, total={total_insights})...")

            # Build alert message
            alert_title = "🔔 Sofia Pulse - Insights Críticos" if critical_count > 0 else "📊 Sofia Pulse - Novos Insights"
            alert_message = f"*Resumo Diário de Insights*\n\n"
            alert_message += f"Total: {total_insights} insights gerados\n"
            alert_message += f"• Info: {ins_data['by_severity']['info']}\n"
            alert_message += f"• Warning: {ins_data['by_severity']['warning']}\n"
            alert_message += f"• Critical: {ins_data['by_severity']['critical']}\n\n"
            alert_message += f"Por domínio:\n"
            for domain, count in ins_data['by_domain'].items():
                alert_message += f"• {domain}: {count}\n"

            # Dedupe check: has this alert been sent today?
            import hashlib
            import os
            import psycopg2
            from datetime import datetime

            message_hash = hashlib.sha256(alert_message.encode()).hexdigest()
            db_url = os.environ.get("DATABASE_URL")

            should_send = True
            if db_url:
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
                        print(f"  ⏭️  WhatsApp alert skipped (already sent today)")
                        should_send = False
                    else:
                        # Record that we're sending
                        cur.execute("""
                            INSERT INTO sofia.notifications_sent (
                                date_brt, channel, message_hash, recipient, severity,
                                title, message_preview, trace_id
                            )
                            VALUES (
                                CURRENT_DATE, 'whatsapp', %s, 'admin', %s,
                                %s, %s, %s
                            )
                            ON CONFLICT (date_brt, channel, message_hash) DO NOTHING
                        """, (
                            message_hash,
                            "critical" if critical_count > 0 else "warning",
                            alert_title,
                            alert_message[:200],
                            trace
                        ))
                        conn.commit()

                    cur.close()
                    conn.close()
                except Exception as e:
                    print(f"  ⚠️  Dedupe check failed: {e}")

            if should_send:
                whatsapp_result = run("notify.whatsapp", {
                    "to": "admin",
                    "severity": "critical" if critical_count > 0 else "warning",
                    "title": alert_title,
                    "message": alert_message,
                    "summary": {
                        "total_insights": total_insights,
                        "critical": critical_count
                    }
                }, trace_id=trace)

                if whatsapp_result["ok"]:
                    print(f"  ✅ WhatsApp alert sent")
                else:
                    print(f"  ⚠️ WhatsApp alert failed: {whatsapp_result.get('errors', [])}")
    else:
        print(f"  ⚠️ Insights generation failed: {insights_result.get('errors', [])}")
        # Don't fail pipeline if insights fail (best-effort)

    # 8. Audit final (baseado apenas em required + ga4)
    required_collector_ids = []
    if "required" in groups:
        required_collector_ids.extend([c["collector_id"] for c in groups["required"]])
    if "ga4" in groups:
        required_collector_ids.extend([c["collector_id"] for c in groups["ga4"]])

    print(f"\n[daily_pipeline] Running audit (required set: {len(required_collector_ids)} collectors)...")

    audit = run("runs.audit", {
        "include_details": True,
        "expected_collectors": required_collector_ids
    }, trace_id=trace)

    if not audit["ok"]:
        print(f"[daily_pipeline] ❌ Audit failed: {audit['errors']}")
        sys.exit(1)

    data = audit["data"]
    summary = data["summary"]
    healthy = data["healthy"]

    print(f"[daily_pipeline] Audit summary: {json.dumps(summary)}")
    print(f"[daily_pipeline] Healthy (required only): {healthy}")

    # 9. Log resultado
    if not healthy:
        print(f"\n[daily_pipeline] ❌ UNHEALTHY (required collectors)")
        print(f"  Missing: {len(data['missing'])}")
        print(f"  Failed: {len(data['failed'])}")
        print(f"  Empty: {len(data['empty'])}")

        if data['missing']:
            print(f"\n  Missing collectors:")
            for m in data['missing']:
                print(f"    - {m['collector_id']}")

        if data['failed']:
            print(f"\n  Failed collectors:")
            for f in data['failed']:
                print(f"    - {f['collector_id']}: {f.get('error_code', 'UNKNOWN')}")

        if data['empty']:
            print(f"\n  Empty collectors:")
            for e in data['empty']:
                print(f"    - {e['collector_id']}: saved={e.get('saved', 0)}, expected>={e.get('expected_min', 1)}")

        run("logger.event", {
            "level": "error",
            "event": "daily_pipeline.unhealthy",
            "skill": "daily_pipeline",
            "missing": len(data['missing']),
            "failed": len(data['failed']),
            "empty": len(data['empty'])
        }, trace_id=trace)

        sys.exit(1)

    else:
        print(f"\n[daily_pipeline] ✅ HEALTHY (required collectors)")
        run("logger.event", {
            "level": "info",
            "event": "daily_pipeline.ok",
            "skill": "daily_pipeline",
            "expected": summary['expected'],
            "ran": summary['ran'],
            "succeeded": summary['succeeded']
        }, trace_id=trace)

        sys.exit(0)


if __name__ == "__main__":
    main()
