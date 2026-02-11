# Sofia Skills Standard Pack v1.1

Regras obrigatórias. Leia ANTES de implementar qualquer skill.

## Envelope I/O (TODA skill usa isso)

```python
# INPUT
class SkillInput:
    trace_id: str          # UUID, propagado end-to-end
    actor: str             # "system"|"user"|"n8n"|"cron"|"api"
    dry_run: bool          # True = simula sem efeitos
    params: dict           # payload específico da skill
    context: dict          # {"env":"prod|dev","timezone":"America/Sao_Paulo","locale":"pt-BR"}

# OUTPUT
class SkillOutput:
    ok: bool               # False => errors não-vazio
    data: dict | None
    warnings: list         # [{"code":"...","message":"..."}]
    errors: list           # [{"code":"...","message":"...","retryable":bool}]
    meta: dict             # {"duration_ms":0,"version":"1.0.0","cost_estimate":0}
```

## 13 Regras (não-negociáveis)

1. ok=false → errors NÃO-VAZIO. ok=true → errors VAZIO.
2. Sem fallback silencioso. Sem dados inventados. Sem fontes fake.
3. Acessa APENAS o declarado em skill.yaml (deps/permissions).
4. Nunca loga secrets.
5. DB writes DEVEM ser idempotentes (hash/uuid/ON CONFLICT).
6. Apenas SQL parametrizado. Zero string-built SQL.
7. Timeouts e retries seguem skill.yaml.
8. Se llm=true ou API paga → meta.cost_estimate obrigatório.
9. trace_id propagado em TODA chamada interna.
10. Erro explícito > fallback inventado.
11. Exceções SEMPRE capturadas e traduzidas pro envelope.
12. Geração de texto usa style_profile fechado, nunca tom livre.
13. Rodar 2x NÃO duplica efeitos (idempotência).

## Convenções

- skill.yaml → `name: logger.event` (ponto)
- Pasta → `skills/logger_event/` (underscore)
- Import → `from skills.logger_event.src import execute`
- Runner → `skill_name.replace('.', '_')`
- Schemas → `schemas/input.json`, `schemas/output.json`
- DDL → `sql/migrations/YYYYMMDD_NNN_*.sql` (fonte canônica ÚNICA)
- Docs → APENAS sob demanda, nunca automático em cada run
- SOFIA_AUTODOC=false (env var, sem exceção)

## Runner — Assinatura canônica (não mude)

```python
run(skill_name, params, *, trace_id=None, actor="system", dry_run=False, env="prod")
```

- `*` torna kwargs obrigatórios por nome (impede posicional)
- trace_id NUNCA vai dentro de params (runner filtra se vier)
- Toda skill expõe `execute(trace_id, actor, dry_run, params, context)` — é a interface padrão
- Convenience aliases (ex: `log()`) são atalhos internos, nunca chamados pelo runner

## Nomenclatura de collectors

- `collector_id`: ID canônico no inventory (ex: "acled") — OBRIGATÓRIO
- `collector_path`: path do script — OPCIONAL (resolvido do inventory)
- `collector_name`: NÃO USE (legado, alias de collector_id em collector_runs)

## Error codes

Códigos vivem em `02_error_codes.md`. Se o código não existir lá, use `UNKNOWN_ERROR`.
NUNCA invente códigos novos inline.

## Estrutura por skill
```
skills/<name_underscore>/
  __init__.py    # vazio
  skill.yaml
  schemas/input.json, output.json
  src/__init__.py  # implementação
  README.md
```

## Stack
Python 3.11+, PostgreSQL 15+ pgvector, psycopg2 raw SQL, cron, dotenv.
Logs → SOFIA_LOG_DIR (default /var/log/sofia, fallback /tmp/sofia).
Sem Redis, filas, ORM.

## Notificações
Todas notificações DEVEM usar `notify.whatsapp` skill (não chamar Baileys direto).
WhatsApp é o canal primário de alertas operacionais.

```python
# Exemplo: Alerta crítico
run("notify.whatsapp", {
    "to": "admin",
    "severity": "critical",
    "title": "Daily Pipeline UNHEALTHY",
    "message": "3 collectors falharam...",
    "summary": {"Failed": 3}
})
```

Ver: `skills/notify_whatsapp/README.md` para detalhes.
