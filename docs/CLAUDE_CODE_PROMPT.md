# Sofia Skills — Prompt de Implementação v1.1

## Regra #1: Leia `docs/skills/00_standard_pack.md` ANTES de tudo.

## Contexto
- **Projeto:** Sofia Pulse — inteligência estratégica
- **Stack:** Python 3.11+, FastAPI, PostgreSQL 15+ pgvector, psycopg2 (raw SQL), cron
- **Estrutura:** 590+ scripts em `scripts/`, API em `api/`, frontend Next.js em `src/`
- **Problema atual:** entropia operacional — collectors que ninguém sabe se rodam, docs geradas sem necessidade, insights diários que não estão sendo gerados

## Convenções CRÍTICAS (v1.2 — bugs corrigidos)

- Pastas usam **underscore**: `skills/logger_event/`, `skills/collect_run/`
- skill.yaml usa **ponto**: `name: logger.event`
- Runner resolve: `skill_name.replace('.', '_')`
- Import: `from skills.logger_event.src import execute`
- Schemas: `schemas/input.json`, `schemas/output.json` (sem `.schema.` no nome)
- DDL vive APENAS em `sql/migrations/` — Python referencia, nunca duplica
- `__init__.py` em TODA pasta (lib/, skills/, skills/*/,  skills/*/src/)
- Logs: SOFIA_LOG_DIR com fallback automático (/var/log/sofia → /tmp/sofia)
- Docs geradas APENAS sob demanda. `SOFIA_AUTODOC=false` sempre.
- Error codes: use APENAS os de `02_error_codes.md`. Se não existir, use `UNKNOWN_ERROR`.

### Runner — Assinatura canônica (não mude)
```python
run(skill_name, params, *, trace_id=None, actor="system", dry_run=False, env="prod")
```
- `*` torna kwargs keyword-only. `trace_id` NUNCA vai dentro de `params`.
- Toda skill expõe `execute()`. Aliases como `log()` são atalhos internos, nunca chamados pelo runner.

### Nomenclatura de collectors (padronizada)
- `collector_id`: ID canônico no inventory (ex: "acled") — o que o pipeline usa
- `collector_path`: path do script — opcional, resolvido do inventory
- `collect.run` aceita só `collector_id` (obrigatório). Path vem do inventory.

## O que NÃO TOCAR
- Collectors em `scripts/` — funcionam, têm ON CONFLICT
- API FastAPI em `api/`
- Materialized views em `sql/`
- Frontend em `src/`

## Ordem de implementação

### Fase 0 — Setup (PRIMEIRO)

1. **Rodar migrations** em ordem:
```bash
psql $DATABASE_URL < sql/migrations/20250209_001_create_collector_runs.sql
psql $DATABASE_URL < sql/migrations/20250209_002_create_budget_tables.sql
psql $DATABASE_URL < sql/migrations/20250209_003_create_embeddings.sql
psql $DATABASE_URL < sql/migrations/20250209_004_create_collector_inventory.sql
```

2. **Verificar `lib/skill_runner.py`** funciona:
```python
from lib.skill_runner import run
r = run("logger.event", {"level":"info","event":"test.ping","skill":"test"})
assert r["ok"] == True
```

### Fase 0.5 — Anti-entropia (ANTES de expandir features)

3. **inventory.collectors** — Popular inventário:
```python
# Scan automático de scripts/
r = run("inventory.collectors", {"action":"scan","scan_dir":"scripts/"})
# Vai listar scripts órfãos (não registrados)

# Registrar os importantes:
run("inventory.collectors", {"action":"register","collector_id":"acled","path":"scripts/collect-brazil-security.py","schedule":"daily"})
```

4. **runs.audit** — Verificar saúde:
```python
r = run("runs.audit", {})
# r["data"]["healthy"] == True/False
# r["data"]["missing"] == collectors que deveriam ter rodado e não rodaram
```

### Fase 1 — Fundação (Sprint 0)

5. **logger.event** — Teste e comece a migrar prints:
```python
from skills.logger_event.src import log
log(trace_id, "collect.run", "collector.started", message="ACLED")
```

6. **collect.run** — Wrapper para cron:
```bash
# ANTES: python3 scripts/collect-brazil-security.py >> log 2>&1
# DEPOIS (collector_id resolve path do inventory):
python3 -c "from lib.skill_runner import run; run('collect.run',{'collector_id':'acled'})"
# OU com path explícito (se não estiver no inventory ainda):
python3 -c "from lib.skill_runner import run; run('collect.run',{'collector_id':'acled','collector_path':'scripts/collect-brazil-security.py'})"
```

7. **budget.guard** — Ativar limite:
```sql
INSERT INTO sofia.budget_limits VALUES ('day','global',5.00,'USD',true,NOW()) ON CONFLICT DO NOTHING;
```

### Fase 2 — Pipeline (Sprint 1)

8. **http.fetch** — Migrar collectors para usar rate-limit
9. **data.normalize** — Unificar normalização

### Fase 3 — Valor (Sprint 2)

10. **insights.rank** → 11. **brief.generate** → 12. **search.semantic**

### Pipeline Diário (o objetivo final)

```python
# daily_pipeline.py — roda via cron 1x/dia
import uuid
from lib.skill_runner import run

trace = str(uuid.uuid4())

# 1. Budget check
b = run("budget.guard", {"scope":"day","scope_id":"global","estimated_cost":0.5}, trace_id=trace)
if not b["ok"]: exit(1)

# 2. Rodar collectors diários (collector_id resolve path do inventory)
inv = run("inventory.collectors", {"action":"list","status":"active"}, trace_id=trace)
for c in inv["data"]["collectors"]:
    if c["schedule"] == "daily":
        run("collect.run", {"collector_id": c["collector_id"]}, trace_id=trace)

# 3. Ranking + Brief
# (buscar insights do banco, rankear, gerar brief)

# 4. Audit
audit = run("runs.audit", {}, trace_id=trace)
if not audit["data"]["healthy"]:
    from skills.logger_event.src import log
    log(trace, "daily_pipeline", "pipeline.unhealthy",
        level="error", missing=audit["data"]["summary"]["missing"],
        failed=audit["data"]["summary"]["failed"])
```

## Regras para implementação

1. Leia README.md + skill.yaml da skill antes de mexer
2. Erros usam códigos de `02_error_codes.md` — não invente
3. trace_id propaga em chamadas internas
4. budget.guard antes de LLM — SEMPRE
5. Migrations versionadas em `sql/migrations/` — única fonte de DDL
6. NÃO gere documentação automática — só quando explicitamente pedido
7. NÃO reescreva collectors existentes — apenas envolva com runner

## Checklist

- [ ] Migrations rodadas
- [ ] `__init__.py` em toda pasta
- [ ] skill_runner funcional
- [ ] inventory populado (scan + register)
- [ ] runs.audit retorna resultado
- [ ] Pelo menos 1 collector rodando via collect.run
- [ ] budget.guard com limite configurado
- [ ] Pipeline diário stubado e testado
