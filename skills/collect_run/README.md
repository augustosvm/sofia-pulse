# collect.run
Wrapper que executa collectors e registra em `sofia.collector_runs`.
NÃO reescreve collectors.

**collector_id** é obrigatório. Path resolvido do inventory (ou passado explícito).
Pipeline/cron: `run("collect.run", {"collector_id": "acled"})`

DDL: `sql/migrations/20250209_001_create_collector_runs.sql`
