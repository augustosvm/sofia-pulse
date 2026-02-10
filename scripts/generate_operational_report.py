#!/usr/bin/env python3
"""
Sofia Pulse - Operational Report Generator
Gera relatório operacional baseado em DADOS REAIS do banco (não mensagens antigas).

Uso:
  python3 generate_operational_report.py [--since-hours 3] [--output-dir reports/]

Formatos gerados:
  - report_executive.txt (resumo 10-15 linhas)
  - report_technical.txt (completo)
  - report_whatsapp.txt (versão curta para WhatsApp)
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras
import argparse

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def connect_db():
    """Conecta ao banco PostgreSQL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL não configurado")
        sys.exit(1)

    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"❌ Falha ao conectar: {e}")
        sys.exit(1)


def get_expected_collectors(cur):
    """Retorna collectors esperados (enabled=true no inventory)."""
    cur.execute("""
        SELECT collector_id, expected_min_records, allow_empty
        FROM sofia.collector_inventory
        WHERE enabled = true
        ORDER BY collector_id
    """)

    expected = {}
    for row in cur.fetchall():
        expected[row['collector_id']] = {
            'expected_min': row['expected_min_records'] or 1,
            'allow_empty': row['allow_empty'] or False
        }

    return expected


def get_recent_runs(cur, since_hours):
    """Retorna runs das últimas N horas (timezone BRT)."""
    cur.execute("""
        SELECT
            collector_name,
            ok,
            fetched,
            saved,
            error_code,
            error_message,
            duration_ms,
            started_at,
            trace_id,
            (started_at AT TIME ZONE 'America/Sao_Paulo') AS started_brt
        FROM sofia.collector_runs
        WHERE started_at >= NOW() - INTERVAL '%s hours'
        ORDER BY started_at DESC
    """, (since_hours,))

    return cur.fetchall()


def detect_execution_window(runs):
    """Detecta janela de execução (início, fim, trace_id)."""
    if not runs:
        return None

    # Agrupar por trace_id (execução)
    trace_groups = {}
    for run in runs:
        trace = run['trace_id'] or 'unknown'
        if trace not in trace_groups:
            trace_groups[trace] = []
        trace_groups[trace].append(run)

    # Pegar a execução mais recente (maior número de runs)
    latest_trace = max(trace_groups.items(), key=lambda x: len(x[1]))
    trace_id = latest_trace[0]
    trace_runs = latest_trace[1]

    start_time = min(r['started_brt'] for r in trace_runs)
    end_time = max(r['started_brt'] for r in trace_runs)
    duration_seconds = (end_time - start_time).total_seconds() if start_time != end_time else 0

    return {
        'trace_id': trace_id,
        'start_brt': start_time,
        'end_brt': end_time,
        'duration_seconds': duration_seconds,
        'runs_count': len(trace_runs),
        'runs': trace_runs
    }


def classify_runs(runs, expected):
    """Classifica runs em: succeeded, empty, failed."""
    succeeded = []
    empty = []
    failed = []

    for run in runs:
        collector_id = run['collector_name']
        exp = expected.get(collector_id, {'expected_min': 1, 'allow_empty': False})

        if not run['ok']:
            # Falhou
            failed.append({
                'collector_id': collector_id,
                'error_code': run['error_code'] or 'UNKNOWN',
                'error_message': run['error_message'] or '',
                'started_brt': run['started_brt'],
                'duration_ms': run['duration_ms']
            })
        else:
            # OK=true
            saved = run['saved'] or 0
            fetched = run['fetched'] or 0

            if not exp['allow_empty'] and saved < exp['expected_min']:
                # Vazio
                empty.append({
                    'collector_id': collector_id,
                    'saved': saved,
                    'fetched': fetched,
                    'expected_min': exp['expected_min'],
                    'started_brt': run['started_brt'],
                    'duration_ms': run['duration_ms']
                })
            else:
                # Sucesso
                succeeded.append({
                    'collector_id': collector_id,
                    'saved': saved,
                    'fetched': fetched,
                    'started_brt': run['started_brt'],
                    'duration_ms': run['duration_ms']
                })

    return succeeded, empty, failed


def find_missing(expected, ran_collectors):
    """Encontra collectors esperados que não rodaram."""
    missing = []
    for collector_id, exp in expected.items():
        if collector_id not in ran_collectors:
            missing.append({
                'collector_id': collector_id,
                'expected_min': exp['expected_min']
            })

    return missing


def detect_anomalies(succeeded, empty, failed):
    """Detecta anomalias operacionais automaticamente."""
    observations = []

    # 1. Collectors com saved sempre igual (suspeito)
    saved_counts = {}
    for s in succeeded:
        saved = s['saved']
        if saved not in saved_counts:
            saved_counts[saved] = []
        saved_counts[saved].append(s['collector_id'])

    for saved, collectors in saved_counts.items():
        if len(collectors) >= 3 and saved > 0:
            observations.append(f"⚠️ {len(collectors)} collectors com saved={saved} (suspeito?): {', '.join(collectors[:3])}")

    # 2. Collectors sempre vazios
    if len(empty) >= 3:
        empty_names = [e['collector_id'] for e in empty[:5]]
        observations.append(f"⚠️ {len(empty)} collectors rodaram mas vieram vazios: {', '.join(empty_names)}")

    # 3. Collectors importantes falharam
    important = ['ga4-analytics', 'ga4-events', 'jobs-catho', 'jobs-linkedin', 'bacen-sgs', 'ibge-api']
    failed_important = [f['collector_id'] for f in failed if f['collector_id'] in important]
    if failed_important:
        observations.append(f"🚨 Collectors IMPORTANTES falharam: {', '.join(failed_important)}")

    # 4. Muitas falhas
    if len(failed) >= 5:
        observations.append(f"🚨 {len(failed)} falhas detectadas (acima do normal)")

    return observations


def check_gate_health(execution, expected):
    """Verifica health gate (required + GA4)."""
    if not execution:
        return {'healthy': False, 'reason': 'Nenhuma execução detectada'}

    # Collectors do gate
    gate_collectors = ['bacen-sgs', 'ibge-api', 'ipea-api', 'ga4-analytics', 'ga4-events']

    gate_failed = []
    gate_missing = []

    for run in execution['runs']:
        collector_id = run['collector_name']
        if collector_id in gate_collectors and not run['ok']:
            gate_failed.append(collector_id)

    ran_collectors = {r['collector_name'] for r in execution['runs']}
    for gc in gate_collectors:
        if gc in expected and gc not in ran_collectors:
            gate_missing.append(gc)

    healthy = len(gate_failed) == 0 and len(gate_missing) == 0

    return {
        'healthy': healthy,
        'failed': gate_failed,
        'missing': gate_missing,
        'reason': 'OK' if healthy else f"Failed: {gate_failed}, Missing: {gate_missing}"
    }


def format_report_executive(execution, summary, gate_status, observations):
    """Gera relatório executivo (10-15 linhas)."""
    if not execution:
        return """
═══════════════════════════════════════════════════════════
SOFIA PULSE - RELATÓRIO EXECUTIVO
═══════════════════════════════════════════════════════════

🚨 NENHUMA EXECUÇÃO DETECTADA

Não foram encontrados runs nas últimas 3 horas.

Ação recomendada: Verificar se o cron está rodando.
"""

    status_emoji = "✅" if gate_status['healthy'] else "🚨"

    report = f"""
═══════════════════════════════════════════════════════════
SOFIA PULSE - RELATÓRIO EXECUTIVO
═══════════════════════════════════════════════════════════

{status_emoji} STATUS GERAL: {"HEALTHY" if gate_status['healthy'] else "UNHEALTHY"}

Execução: {execution['trace_id'][:8]}
Janela: {execution['start_brt']:%Y-%m-%d %H:%M} → {execution['end_brt']:%H:%M} BRT
Duração: {int(execution['duration_seconds'])}s

NÚMEROS:
• Esperados: {summary['expected']}
• Rodaram: {summary['ran']} ({summary['ran']/summary['expected']*100:.0f}%)
• Sucessos: {summary['succeeded']}
• Vazios: {summary['empty']}
• Falhas: {summary['failed']}
• Não rodaram: {summary['missing']}

GATE (Required+GA4): {gate_status['reason']}
"""

    if observations:
        report += "\nOBSERVAÇÕES:\n"
        for obs in observations[:3]:
            report += f"• {obs}\n"

    return report


def format_report_technical(execution, expected, succeeded, empty, failed, missing, gate_status, observations):
    """Gera relatório técnico completo."""
    if not execution:
        return format_report_executive(None, {}, {}, [])

    report = f"""
═══════════════════════════════════════════════════════════
SOFIA PULSE - RELATÓRIO TÉCNICO COMPLETO
═══════════════════════════════════════════════════════════

1️⃣ EXECUÇÃO DETECTADA

Trace ID: {execution['trace_id']}
Início (BRT): {execution['start_brt']:%Y-%m-%d %H:%M:%S}
Fim (BRT): {execution['end_brt']:%Y-%m-%d %H:%M:%S}
Duração total: {int(execution['duration_seconds'])}s ({execution['runs_count']} collectors)
Gate Status: {"✅ HEALTHY" if gate_status['healthy'] else "🚨 UNHEALTHY"}
  Motivo: {gate_status['reason']}

───────────────────────────────────────────────────────────

2️⃣ RESUMO NUMÉRICO

Collectors esperados: {len(expected)}
Collectors que rodaram: {len(set(r['collector_name'] for r in execution['runs']))}
Sucessos (saved > 0): {len(succeeded)}
Vazios (saved = 0 ou < min): {len(empty)}
Falhas (ok = false): {len(failed)}
Não rodaram: {len(missing)}

───────────────────────────────────────────────────────────

3️⃣ SUCESSOS (saved > 0): {len(succeeded)}
"""

    if succeeded:
        for s in succeeded:
            saved = s['saved'] if s['saved'] is not None else 'UNKNOWN'
            fetched = s['fetched'] if s['fetched'] is not None else 'UNKNOWN'
            report += f"\n• {s['collector_id']}\n"
            report += f"  saved={saved} | fetched={fetched} | {s['duration_ms']}ms\n"
            report += f"  horário: {s['started_brt']:%H:%M:%S} BRT\n"
    else:
        report += "\nNenhum sucesso registrado.\n"

    report += f"\n───────────────────────────────────────────────────────────\n"
    report += f"\n4️⃣ VAZIOS (rodou mas não gerou dados): {len(empty)}\n"

    if empty:
        for e in empty:
            saved = e['saved'] if e['saved'] is not None else 'UNKNOWN'
            report += f"\n• {e['collector_id']}\n"
            report += f"  saved={saved} (esperado mín: {e['expected_min']})\n"
            report += f"  horário: {e['started_brt']:%H:%M:%S} BRT\n"
            report += f"  ⚠️ Rodou mas não gerou dados suficientes\n"
    else:
        report += "\nNenhum vazio.\n"

    report += f"\n───────────────────────────────────────────────────────────\n"
    report += f"\n5️⃣ FALHAS (ok = false): {len(failed)}\n"

    if failed:
        for f in failed:
            report += f"\n• {f['collector_id']}\n"
            report += f"  error_code: {f['error_code']}\n"
            if f['error_message']:
                msg = f['error_message'][:100]
                report += f"  mensagem: {msg}{'...' if len(f['error_message']) > 100 else ''}\n"
            report += f"  horário: {f['started_brt']:%H:%M:%S} BRT\n"
    else:
        report += "\nNenhuma falha.\n"

    report += f"\n───────────────────────────────────────────────────────────\n"
    report += f"\n6️⃣ NÃO RODARAM (esperados mas ausentes): {len(missing)}\n"

    if missing:
        for m in missing:
            report += f"• {m['collector_id']} (esperado mín: {m['expected_min']})\n"
    else:
        report += "Todos os collectors esperados rodaram.\n"

    report += f"\n───────────────────────────────────────────────────────────\n"
    report += f"\n7️⃣ OBSERVAÇÕES OPERACIONAIS (AUTOMÁTICAS)\n\n"

    if observations:
        for obs in observations:
            report += f"{obs}\n"
    else:
        report += "Nenhuma anomalia detectada.\n"

    report += "\n═══════════════════════════════════════════════════════════\n"

    return report


def format_report_whatsapp(execution, summary, gate_status, observations):
    """Gera versão WhatsApp-friendly (curta)."""
    if not execution:
        return """🚨 *Sofia Pulse - Relatório*

Nenhuma execução detectada nas últimas 3h.

Verificar cron."""

    status = "✅ HEALTHY" if gate_status['healthy'] else "🚨 UNHEALTHY"

    report = f"""*Sofia Pulse - Relatório Operacional*

Trace: `{execution['trace_id'][:8]}`
Janela: {execution['start_brt']:%H:%M}→{execution['end_brt']:%H:%M} BRT

*Gate:* {status}
*Esperado/Rodou:* {summary['expected']}/{summary['ran']}
*OK/Vazios/Falhas/Missing:* {summary['succeeded']}/{summary['empty']}/{summary['failed']}/{summary['missing']}
"""

    if observations:
        report += "\n*Observações:*\n"
        for obs in observations[:2]:
            # Remove emojis para WhatsApp
            clean_obs = obs.replace("⚠️", "!").replace("🚨", "!")
            report += f"• {clean_obs}\n"

    return report


def main():
    parser = argparse.ArgumentParser(description="Gera relatório operacional do Sofia Pulse")
    parser.add_argument("--since-hours", type=int, default=3, help="Janela de horas (default: 3)")
    parser.add_argument("--output-dir", type=str, default="reports", help="Diretório de saída")
    args = parser.parse_args()

    print(f"[generate_operational_report] Gerando relatório...")
    print(f"  Janela: últimas {args.since_hours} horas")
    print(f"  Output: {args.output_dir}/")

    # Conectar ao banco
    conn = connect_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # 1. Buscar dados reais
    print("\n[1/7] Buscando collectors esperados...")
    expected = get_expected_collectors(cur)
    print(f"  ✅ {len(expected)} collectors esperados")

    print("\n[2/7] Buscando runs recentes...")
    runs = get_recent_runs(cur, args.since_hours)
    print(f"  ✅ {len(runs)} runs encontrados")

    if not runs:
        print("\n🚨 ATENÇÃO: Nenhuma execução encontrada nas últimas {args.since_hours} horas")
        print("  Gerando relatório de ausência...\n")

        # Gerar relatórios de ausência
        exec_report = format_report_executive(None, {}, {}, [])
        tech_report = format_report_technical(None, {}, [], [], [], [], {}, [])
        wpp_report = format_report_whatsapp(None, {}, {}, [])

    else:
        print("\n[3/7] Detectando janela de execução...")
        execution = detect_execution_window(runs)
        print(f"  ✅ Trace: {execution['trace_id'][:8]}")
        print(f"  ✅ Janela: {execution['start_brt']:%H:%M} → {execution['end_brt']:%H:%M} BRT")

        print("\n[4/7] Classificando runs...")
        succeeded, empty, failed = classify_runs(execution['runs'], expected)
        print(f"  ✅ Sucessos: {len(succeeded)}")
        print(f"  ✅ Vazios: {len(empty)}")
        print(f"  ✅ Falhas: {len(failed)}")

        print("\n[5/7] Identificando missing...")
        ran_collectors = {r['collector_name'] for r in execution['runs']}
        missing = find_missing(expected, ran_collectors)
        print(f"  ✅ Não rodaram: {len(missing)}")

        print("\n[6/7] Verificando gate health...")
        gate_status = check_gate_health(execution, expected)
        print(f"  ✅ Gate: {gate_status['reason']}")

        print("\n[7/7] Detectando anomalias...")
        observations = detect_anomalies(succeeded, empty, failed)
        print(f"  ✅ Observações: {len(observations)}")

        # Gerar relatórios
        summary = {
            'expected': len(expected),
            'ran': len(ran_collectors),
            'succeeded': len(succeeded),
            'empty': len(empty),
            'failed': len(failed),
            'missing': len(missing)
        }

        exec_report = format_report_executive(execution, summary, gate_status, observations)
        tech_report = format_report_technical(execution, expected, succeeded, empty, failed, missing, gate_status, observations)
        wpp_report = format_report_whatsapp(execution, summary, gate_status, observations)

    # Criar diretório de output
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Salvar arquivos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    exec_file = output_dir / f"report_executive_{timestamp}.txt"
    tech_file = output_dir / f"report_technical_{timestamp}.txt"
    wpp_file = output_dir / f"report_whatsapp_{timestamp}.txt"

    with open(exec_file, 'w') as f:
        f.write(exec_report)

    with open(tech_file, 'w') as f:
        f.write(tech_report)

    with open(wpp_file, 'w') as f:
        f.write(wpp_report)

    print(f"\n✅ Relatórios gerados:")
    print(f"  📄 Executivo: {exec_file}")
    print(f"  📄 Técnico: {tech_file}")
    print(f"  📄 WhatsApp: {wpp_file}")

    # Mostrar executivo no stdout
    print("\n" + "="*60)
    print(exec_report)

    cur.close()
    conn.close()

    sys.exit(0)


if __name__ == "__main__":
    main()
