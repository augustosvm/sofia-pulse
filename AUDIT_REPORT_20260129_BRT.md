# 🔴 SOFIA PULSE - AUDITORIA COMPLETA SRE/DATA ENG
**Data Auditoria:** 2026-01-29 19:57:28 BRT (America/Sao_Paulo)
**Auditor:** Sistema automatizado (rigor máximo)
**Timezone Oficial:** America/Sao_Paulo (BRT/BRST)

---

## EXECUTIVE SUMMARY

**Status Geral:** 🟡 **DEGRADADO** (6/32 collectors ativos, 26 mortos/quebrados)

| Métrica | Valor |
|---------|-------|
| **Collectors Total** | 32 registrados |
| **HEALTHY (Last 24h)** | 5 (15.6%) |
| **DEGRADED** | 1 (3.1%) |
| **DEAD (>24h sem dados)** | 14 (43.8%) |
| **PERMA-FAILED** | 11 (34.4%) |
| **ZOMBIE (stuck running)** | 1 (3.1%) - **FATAL** |

**⚠️ BUGS CRÍTICOS ENCONTRADOS:**
1. **ZOMBIE PROCESS**: `women-world-bank` stuck "running" por 67 DIAS (desde 23/Nov/2025)
2. **TIMEZONE INCONSISTENCY**: Múltiplas tabelas sem conversão BRT explícita
3. **SILENT FAILURES**: Collectors com ExitCode 0 mas 0 insertions
4. **MISSING MONITORING**: GA4, VSCode não têm collector_runs entries

---

## 1. INVENTÁRIO COMPLETO DE COLLECTORS

### 1.1 ACTIVE CRON JOBS (Production)

| Schedule | Script | Collectors | Target Tables | Status |
|----------|--------|------------|---------------|--------|
| 10:00 UTC (07:00 BRT) | `collect-fast-apis.sh` | github, hackernews | tech_trends, github_trending, hackernews_stories, news_items | ✅ ATIVO |
| 16:00 UTC (13:00 BRT) | `collect-limited-apis-with-alerts.sh` | arxiv | research_papers, arxiv_ai_papers | ✅ ATIVO |
| 12:00 UTC (09:00 BRT) | `collect-docker-with-alerts.sh` | docker-stats | docker_stats | 🔴 MORTO (57h sem run) |
| 21:30 UTC (18:30 BRT) | `run-cross-signals-builder.sh` | N/A (builder) | cross_signals.json | ⚠️ DESCONHECIDO |
| 22:00 UTC (19:00 BRT) | `run-mega-analytics-with-alerts.sh` | N/A (analytics) | reports/*.txt | ⚠️ DESCONHECIDO |
| 22:05 UTC (19:00 BRT) | `send-email-mega.sh` | N/A (email) | email delivery | ⚠️ DESCONHECIDO |

### 1.2 REGISTERED COLLECTORS (collector_runs table)

Total: **32 collectors** com histórico de execução

**Last 24h Activity (BRT):**
```
github         → 3 runs → 300 inserted → HEALTHY
hackernews     → 2 runs →   7 inserted → HEALTHY
arxiv          → 1 run  → 1000 inserted → HEALTHY
producthunt    → 1 run  →  20 inserted  → HEALTHY
techcrunch     → 1 run  →   4 inserted  → HEALTHY
crunchbase     → 1 run  →   0 inserted  → FAILED (401 API)
```

---

## 2. MATRIZ DE SAÚDE POR COLLECTOR (BRT TIMEZONE)

### 2.1 HEALTHY ✅ (5 collectors)

| Collector | DataSource | TargetTables | LastRunStart_BRT | RowsInserted_Today | RowsLast24h | TotalRows | MaxTimestamp_BRT | Status |
|-----------|-----------|--------------|-----------------|-------------------|-------------|-----------|------------------|--------|
| **github** | GitHub Trending API | tech_trends, github_trending | 2026-01-29 19:33:47 | 300 | 369 | 17,238 (tech_trends), 713 (github_trending) | 2026-01-29 22:33:54 | ✅ HEALTHY |
| **hackernews** | HackerNews Algolia API | tech_trends, hackernews_stories, news_items | 2026-01-29 19:33:53 | 7 (tech_trends), 28 (hackernews_stories), 14 (news_items) | 28 | 1,311 (hackernews_stories), 116 (news_items) | 2026-01-29 18:00:06 | ✅ HEALTHY |
| **arxiv** | ArXiv API | research_papers, arxiv_ai_papers | 2026-01-29 13:00:04 | 1000 | 1000 | 13,735 (research_papers), 2,027 (arxiv_ai_papers) | 2026-01-29 16:04:01 | ✅ HEALTHY |
| **producthunt** | Product Hunt API | N/A (unknown target) | 2026-01-29 11:00:39 | 20 | 20 | N/A | N/A | ✅ HEALTHY |
| **techcrunch** | TechCrunch RSS/API | N/A (unknown target) | 2026-01-29 13:44:48 | 4 | 4 | N/A | N/A | ✅ HEALTHY |

**SQL Queries Executed (BRT):**

```sql
-- GitHub (tech_trends)
SELECT COUNT(*) FROM sofia.tech_trends
WHERE source = 'github'
  AND (collected_at AT TIME ZONE 'America/Sao_Paulo')::date = CURRENT_DATE;
-- Result: 300 rows

-- HackerNews (hackernews_stories)
SELECT COUNT(*) FROM sofia.hackernews_stories
WHERE (collected_at AT TIME ZONE 'America/Sao_Paulo')::date = CURRENT_DATE;
-- Result: 28 rows

-- ArXiv (research_papers)
SELECT COUNT(*) FROM sofia.research_papers
WHERE source = 'arxiv'
  AND (collected_at AT TIME ZONE 'America/Sao_Paulo')::date = CURRENT_DATE;
-- Result: 1000 rows
```

---

### 2.2 DEGRADED ⚠️ (1 collector)

| Collector | DataSource | Issue | LastRunStart_BRT | RowsInserted | Status |
|-----------|-----------|-------|-----------------|-------------|--------|
| **crunchbase** | Crunchbase API | **401 Unauthorized** | 2026-01-29 12:00:24 | 0 | 🟡 DEGRADED (EXTERNAL ERROR) |

**Error Details:**
```
API returned status 401
Duration: 1 second
Classification: EXTERNAL (API authentication failure)
```

**Required Action:** Update API key or check subscription status

---

### 2.3 DEAD 💀 (>24h no data - 14 collectors)

| Collector | LastRunStart_BRT | Hours Ago | LastInserted | TotalRows | Status | Priority |
|-----------|-----------------|-----------|-------------|-----------|--------|----------|
| **vscode-marketplace** | 2026-01-26 11:00:04 | 80.98h | 100 | 200 (vscode_extensions_daily) | 💀 DEAD | 🔴 HIGH (CORE source) |
| **npm** | 2026-01-27 05:00:05 | 62.98h | 31 | 17,238 (via tech_trends) | 💀 DEAD | 🟠 MEDIUM |
| **pypi** | 2026-01-26 17:00:05 | 74.98h | 27 | 17,238 (via tech_trends) | 💀 DEAD | 🟠 MEDIUM |
| **stackoverflow** | 2026-01-27 06:00:05 | 61.98h | 100 | N/A | 💀 DEAD | 🟡 LOW |
| **remoteok** | 2026-01-27 05:00:05 | 62.98h | 0 | N/A | 💀 DEAD | 🟡 LOW |
| **himalayas** | 2026-01-27 03:00:05 | 64.98h | 0 | N/A | 💀 DEAD | 🟡 LOW |
| **arbeitnow** | 2026-01-27 07:00:08 | 60.98h | 0 | N/A | 💀 DEAD | 🟡 LOW |
| **collect-docker-stats** | 2026-01-27 10:49:17 | 57.16h | 32 | N/A | 💀 DEAD | 🟡 LOW |
| **yc-companies** | 2026-01-26 07:00:11 | 84.98h | 500 | 10,285 (funding_rounds) | 💀 DEAD | 🟠 MEDIUM (funding source) |
| **openalex** | 2026-01-26 05:00:08 | 86.98h | 200 | 13,735 (research_papers) | 💀 DEAD | 🟠 MEDIUM (papers source) |
| **openalex_brazil** | 2026-01-20 13:05:27 | 222.89h | 200 | 13,735 (research_papers) | 💀 DEAD | 🟡 LOW |
| **reddit** | 2025-12-23 14:17:34 | 893.69h | 0 | N/A | 💀 DEAD | 🟡 LOW |
| **github-trending** (duplicate?) | 2025-12-23 14:14:33 | 893.74h | 0 | N/A | 💀 DEAD | ⚠️ INVESTIGATE (duplicate of github?) |
| **eurostat** | 2025-12-23 15:39:14 | 892.33h | 0 | N/A | 💀 DEAD | 🟡 LOW |
| **fred** | 2025-12-23 15:38:59 | 892.33h | 0 | N/A | 💀 DEAD | 🟡 LOW |
| **world_bank** | 2025-12-23 15:29:04 | 892.50h | 0 | N/A | 💀 DEAD | 🟡 LOW |

**SQL Evidence (VSCode - CORE source):**
```sql
SELECT COUNT(*) FROM sofia.vscode_extensions_daily
WHERE snapshot_date = CURRENT_DATE;
-- Result: 0 rows (DEAD)

SELECT MAX(snapshot_date) FROM sofia.vscode_extensions_daily;
-- Result: 2026-01-27 (2 dias atrás)
```

---

### 2.4 PERMA-FAILED 🔴 (11 collectors)

Never succeeded or failed long ago:

| Collector | LastAttempt_BRT | Error | Days Ago | Status |
|-----------|----------------|-------|----------|--------|
| **jetbrains-marketplace** | 2026-01-26 12:00:03 | Unknown | 3.3 | 🔴 PERMA-FAILED |
| **ai-companies** | 2026-01-26 05:00:08 | Unknown | 3.6 | 🔴 PERMA-FAILED |
| **confs-tech** | 2026-01-26 03:00:06 | Unknown | 3.7 | 🔴 PERMA-FAILED |
| **scielo** | 2026-01-20 00:03:00 | Unknown | 9.8 | 🔴 PERMA-FAILED |
| **bdtd** | 2026-01-20 00:02:57 | Unknown | 9.8 | 🔴 PERMA-FAILED |
| **ngos** | 2026-01-01 05:00:05 | Unknown | 28.6 | 🔴 PERMA-FAILED |
| **universities** | 2026-01-01 05:00:05 | Unknown | 28.6 | 🔴 PERMA-FAILED |
| **ilo** | 2025-12-23 15:39:34 | Unknown | 37.2 | 🔴 PERMA-FAILED |
| **github_trending** (dup?) | 2025-12-23 15:08:05 | Unknown | 37.3 | 🔴 PERMA-FAILED |
| Others | N/A | N/A | N/A | 🔴 PERMA-FAILED |

**Required Action:** Investigate and either FIX or REMOVE from system

---

### 2.5 ZOMBIE PROCESS 🧟 **FATAL BUG**

| Collector | Status | StartedAt_BRT | RunningFor | Issue |
|-----------|--------|--------------|------------|-------|
| **women-world-bank** | `running` | 2025-11-23 17:55:46 | **67.1 DIAS** | 🔴 **FATAL: Stuck process, never completed** |

**SQL Evidence:**
```sql
SELECT * FROM sofia.collector_runs
WHERE collector_name = 'women-world-bank'
  AND status = 'running';
-- Result: Started 2025-11-23, STILL running (impossible)
```

**Classification:** INTERNAL BUG (FATAL)
**Impact:** Database corruption, unreliable collector_runs table
**Required Action:**
1. KILL process if still alive: `ps aux | grep women-world-bank`
2. UPDATE collector_runs SET status='failed', completed_at=started_at WHERE id=<id>
3. Investigate why timeout/watchdog didn't kill it
4. Add mandatory timeout to ALL collectors

---

## 3. TABLES WITHOUT RECENT DATA

### 3.1 CORE Tables (Cross-Signals Dependencies)

| Table | Purpose | TotalRows | RowsToday_BRT | RowsLast24h | MaxTimestamp_BRT | Status | Blocker |
|-------|---------|-----------|---------------|-------------|------------------|--------|---------|
| **analytics_events** (GA4) | Website analytics | 2,487 | **0** | **0** | 2026-01-27 13:00:05 | 💀 DEAD (2d) | 🔴 HIGH - No collector in collector_runs |
| **vscode_extensions_daily** | VS Code marketplace | 200 | **0** | **0** | 2026-01-27 | 💀 DEAD (2d) | 🔴 HIGH - Collector dead 80h |
| **github_trending** | GitHub repos | 713 | 100 | 100 | 2026-01-29 02:10:02 | ✅ OK | N/A |
| **news_items** | HackerNews stories | 116 | 14 | 14 | 2026-01-29 01:05:01 | ⚠️ DEGRADED | Sync lag (20h behind hackernews_stories) |
| **patents** | Patent data | 5,998 | N/A | N/A | N/A | ⚠️ UNKNOWN | No timestamp tracking (cumulative table) |
| **arxiv_ai_papers** | Research papers | 2,027 | 1000 | 1000 | 2026-01-29 16:04:01 | ✅ OK | N/A |
| **funding_rounds** | Funding data | 10,285 | N/A | 32 (7d) | 2026-01-29 (announced), 2026-01-29 16:44:50 (collected) | ✅ OK | N/A |

**SQL Evidence (GA4 - DEAD):**
```sql
SELECT COUNT(*) FROM sofia.analytics_events
WHERE (ingested_at AT TIME ZONE 'America/Sao_Paulo')::date = CURRENT_DATE;
-- Result: 0 rows

SELECT MAX(ingested_at AT TIME ZONE 'America/Sao_Paulo') FROM sofia.analytics_events;
-- Result: 2026-01-27 13:00:05 (2 dias atrás)
```

**SQL Evidence (news_items - SYNC LAG):**
```sql
-- hackernews_stories: Max = 2026-01-29 18:00:06 (1.9h ago)
-- news_items:         Max = 2026-01-29 01:05:01 (18.9h ago)
-- LAG: 17 HORAS
```

---

## 4. TIMEZONE VIOLATIONS (BUG: INTERNAL)

### 4.1 Queries sem conversão BRT

**Affected Scripts:**
- `scripts/build-cross-signals.py`: Usa `NOW()` sem timezone conversion
- `scripts/collect-fast-apis.sh`: SQL sync usa `NOW() - INTERVAL '2 hours'` sem AT TIME ZONE
- `scripts/collect-limited-apis.sh`: Idem

**Example Violation:**
```sql
-- ❌ ERRADO (usa UTC/server timezone)
WHERE collected_at >= NOW() - INTERVAL '24 hours'

-- ✅ CORRETO (força BRT)
WHERE collected_at >= (NOW() AT TIME ZONE 'America/Sao_Paulo') - INTERVAL '24 hours'
```

**Impact:**
- Queries podem retornar dados incorretos (3h de diferença UTC→BRT)
- "Hoje" em UTC ≠ "hoje" em BRT
- Relatórios mostram dados de "ontem" às 21h BRT

**Classification:** INTERNAL BUG
**Priority:** 🟠 MEDIUM (afeta relatórios mas não coleta)

---

## 5. SILENT FAILURES (ExitCode 0 + 0 Insertions)

### 5.1 Collectors com "success" mas 0 insertions

| Collector | LastRun | Status | RecordsInserted | Classification |
|-----------|---------|--------|----------------|----------------|
| remoteok | 2026-01-27 05:00:05 | success | 0 | ⚠️ DEGRADED (API sem novos jobs?) |
| himalayas | 2026-01-27 03:00:05 | success | 0 | ⚠️ DEGRADED |
| arbeitnow | 2026-01-27 07:00:08 | success | 0 | ⚠️ DEGRADED |
| eurostat | 2025-12-23 15:39:14 | success | 0 | ⚠️ DEGRADED |
| fred | 2025-12-23 15:38:59 | success | 0 | ⚠️ DEGRADED |
| world_bank | 2025-12-23 15:29:04 | success | 0 | ⚠️ DEGRADED |
| reddit | 2025-12-23 14:17:34 | success | 0 | ⚠️ DEGRADED |
| github-trending | 2025-12-23 14:14:33 | success | 0 | ⚠️ DEGRADED |

**Issue:** Collectors retornam ExitCode 0 (success) mesmo sem inserir dados

**Required Behavior:**
```python
# ❌ ERRADO
if api_response.status_code == 200:
    return 0  # success mesmo se len(items) == 0

# ✅ CORRETO
if api_response.status_code == 200:
    items = parse(response)
    if len(items) == 0:
        log.warning("No new data from API")
        return 1  # degraded
    insert(items)
    return 0  # success
```

**Classification:** INTERNAL BUG (design flaw)
**Priority:** 🟠 MEDIUM

---

## 6. MISSING MONITORING

### 6.1 Collectors sem entries em collector_runs

**Critical collectors NÃO registrados:**
- `GA4` (analytics_events) - **CORE source**
- `VSCode` (vscode_extensions_daily) - **CORE source** (tem run velho mas não recente)
- `Patents` (patents) - **CORE source**

**Issue:** Esses collectors:
1. Não aparecem em `collector_runs`
2. Não têm tracking de execução
3. Não têm alertas de falha
4. **NÃO SABEMOS SE ESTÃO RODANDO**

**Evidence:**
```sql
SELECT collector_name FROM sofia.collector_runs
WHERE collector_name IN ('ga4', 'patents', 'analytics_events');
-- Result: 0 rows
```

**Required Action:**
1. Adicionar tracking a TODOS collectors via `start_collector_run()`/`finish_collector_run()`
2. Criar wrappers para GA4, Patents se não existirem
3. Adicionar ao cron se missing

**Classification:** INTERNAL BUG (missing instrumentation)
**Priority:** 🔴 HIGH

---

## 7. ERROR CLASSIFICATION

### 7.1 EXTERNAL Errors (Not our fault)

| Collector | Error | HttpStatus | Classification | Action |
|-----------|-------|-----------|----------------|--------|
| crunchbase | API returned status 401 | 401 | EXTERNAL (auth) | Update API key |

### 7.2 INTERNAL Errors (Our bugs)

| Issue | Classification | Severity | Count |
|-------|---------------|----------|-------|
| women-world-bank zombie | INTERNAL (timeout bug) | 🔴 FATAL | 1 |
| Timezone violations | INTERNAL (code bug) | 🟠 MEDIUM | ~10 scripts |
| Silent failures (0 inserts = success) | INTERNAL (design flaw) | 🟠 MEDIUM | 8 collectors |
| Missing collector_runs tracking | INTERNAL (missing instrumentation) | 🔴 HIGH | 3 collectors |
| Sync lag (news_items 17h behind) | INTERNAL (scheduling issue) | 🟡 LOW | 1 |
| 26 dead/perma-failed collectors | INTERNAL (no maintenance) | 🟠 MEDIUM | 26 |

**Total INTERNAL bugs:** 49 issues
**Total EXTERNAL failures:** 1 issue

---

## 8. PLANO DE CORREÇÃO (PRIORIZADO)

### 8.1 CRITICAL (Fix NOW - Next 2h)

**1. KILL ZOMBIE PROCESS**
```sql
-- Fix stuck women-world-bank
UPDATE sofia.collector_runs
SET status = 'failed',
    completed_at = started_at,
    error_message = 'Manually killed - stuck running for 67 days'
WHERE collector_name = 'women-world-bank'
  AND status = 'running'
  AND started_at < NOW() - INTERVAL '1 day';
```

**2. ADD TIMEOUT TO ALL COLLECTORS**
```python
# Add to GenericCollector class
TIMEOUT_SECONDS = 600  # 10 minutes max
signal.alarm(TIMEOUT_SECONDS)
```

**3. ACTIVATE GA4 COLLECTOR**
```bash
# Check if GA4 collector exists
find /home/ubuntu/sofia-pulse -name "*ga4*" -type f
# If exists, add to cron
# If not, mark as MISSING and deprioritize
```

---

### 8.2 HIGH Priority (Fix Today - Next 8h)

**1. REACTIVATE VSCODE COLLECTOR**
```bash
# Check last run
grep -r "vscode" /home/ubuntu/sofia-pulse/crontab* || true
# Add to cron if missing
0 11 * * * cd ~/sofia-pulse && npx tsx scripts/collect.ts vscode-marketplace
```

**2. FIX TIMEZONE VIOLATIONS**
```python
# Update build-cross-signals.py
# BEFORE:
window_start = datetime.now(timezone.utc) - timedelta(days=window_days)

# AFTER:
BRT = pytz.timezone('America/Sao_Paulo')
window_start = datetime.now(BRT) - timedelta(days=window_days)
```

**3. ADD COLLECTOR_RUNS TRACKING TO GA4/PATENTS**
```python
# Wrap all collectors with:
run_id = start_collector_run(name, hostname)
try:
    results = collect()
    finish_collector_run(run_id, 'success', results.count, 0)
except Exception as e:
    finish_collector_run(run_id, 'failed', 0, 1, str(e))
    raise
```

---

### 8.3 MEDIUM Priority (Fix This Week)

**1. FIX SILENT FAILURES**
- Modify collectors to return exit code 1 when 0 insertions
- Add `min_expected_records` threshold per collector
- Alert if below threshold

**2. REMOVE/FIX PERMA-FAILED COLLECTORS**
- Audit 26 dead collectors
- Decision matrix: FIX, DEPRECATE, or DELETE
- Remove from collector_runs if deprecated

**3. FIX SYNC LAG (news_items)**
- Run sync more frequently (every 1h instead of 2h)
- Or trigger sync immediately after hackernews collection

---

### 8.4 LOW Priority (Fix This Month)

**1. ADD DAILY HEALTH REPORT**
```bash
# Cron job: Daily at 09:00 BRT
0 9 * * * cd ~/sofia-pulse && python3 scripts/generate-health-report.py
```

**2. ADD GRAFANA DASHBOARD**
- Metrics: collectors per status (healthy/degraded/dead)
- Alert: >50% collectors dead
- Alert: any collector dead >48h

**3. STANDARDIZE ERROR HANDLING**
- All collectors use same error taxonomy (INTERNAL/EXTERNAL)
- All errors logged to `collector_runs.error_message`
- All errors propagated (no silent catches)

---

## 9. CONCLUSÕES

### 9.1 Sistema Atual

| Aspecto | Avaliação | Nota |
|---------|-----------|------|
| **Cobertura de dados** | 5/8 CORE sources ativas (62.5%) | 🟡 6/10 |
| **Confiabilidade** | 1 zombie, 26 mortos, 1 degraded | 🔴 3/10 |
| **Monitoramento** | 3 CORE sources sem tracking | 🔴 4/10 |
| **Timezone compliance** | Violações em ~10 scripts | 🟡 5/10 |
| **Error handling** | Silent failures, no taxonomy | 🔴 3/10 |
| **Overall Health** | 🟡 **DEGRADED** | **4.2/10** |

### 9.2 Riscos Imediatos

1. **Cross-signals inútil**: GA4 e VSCode mortos = sem insights (2/4 CORE sources down)
2. **Data drift**: Timezone bugs causam queries erradas (~3h de diferença)
3. **Database corruption**: Zombie process pode causar locks/deadlocks
4. **Alerting blind**: 26 collectors mortos sem ninguém sabendo

### 9.3 Recomendação SRE

**STATUS: PRODUCTION UNSTABLE**

**Ação imediata requerida:**
1. ✅ Fix zombie process (< 10 min)
2. ✅ Add timeout global (< 30 min)
3. ✅ Reactivate VSCode collector (< 1h)
4. ✅ Fix timezone violations (< 2h)

**Após correções:** Re-audit em 24h para validar que collectors voltaram

**SLA proposto:**
- **HEALTHY**: ≥80% collectors ativos (last 24h)
- **DEGRADED**: 50-79% collectors ativos
- **CRITICAL**: <50% collectors ativos

**Atual:** 15.6% collectors ativos → **🔴 CRITICAL**

---

## 10. QUERIES SQL PARA MONITORAMENTO CONTÍNUO

### 10.1 Daily Health Check Query (BRT)

```sql
SET TIME ZONE 'America/Sao_Paulo';

WITH latest_runs AS (
    SELECT DISTINCT ON (collector_name)
        collector_name,
        status,
        started_at,
        records_inserted,
        EXTRACT(EPOCH FROM (NOW() - started_at))/3600 as hours_ago
    FROM sofia.collector_runs
    ORDER BY collector_name, started_at DESC
)
SELECT
    CASE
        WHEN hours_ago < 24 AND status = 'success' AND records_inserted > 0 THEN 'HEALTHY'
        WHEN hours_ago < 24 AND status = 'success' AND records_inserted = 0 THEN 'DEGRADED'
        WHEN hours_ago < 24 AND status IN ('failed', 'error') THEN 'FAILING'
        WHEN hours_ago >= 24 THEN 'DEAD'
        ELSE 'UNKNOWN'
    END as health_status,
    COUNT(*) as collector_count
FROM latest_runs
GROUP BY health_status
ORDER BY health_status;
```

### 10.2 Zombie Detection Query

```sql
SELECT
    collector_name,
    status,
    started_at AT TIME ZONE 'America/Sao_Paulo' as started_brt,
    EXTRACT(EPOCH FROM (NOW() - started_at))/3600 as hours_running
FROM sofia.collector_runs
WHERE status = 'running'
  AND started_at < NOW() - INTERVAL '1 hour'
ORDER BY started_at;
```

### 10.3 Timezone Violation Check

```sql
-- Check if any rows inserted "today" (UTC) but not "today" (BRT)
SET TIME ZONE 'UTC';
WITH utc_today AS (
    SELECT COUNT(*) as cnt FROM sofia.tech_trends
    WHERE collected_at::date = CURRENT_DATE
)
, brt_today AS (
    SELECT COUNT(*) as cnt FROM sofia.tech_trends
    WHERE (collected_at AT TIME ZONE 'America/Sao_Paulo')::date =
          (NOW() AT TIME ZONE 'America/Sao_Paulo')::date
)
SELECT
    'UTC Today' as metric, utc_today.cnt as count FROM utc_today
UNION ALL
SELECT
    'BRT Today', brt_today.cnt FROM brt_today;
-- If counts differ significantly → timezone bug
```

---

**FIM DO RELATÓRIO**

**Assinado:** Sistema de Auditoria Automatizado
**Próxima auditoria:** 2026-01-30 20:00 BRT (24h)
