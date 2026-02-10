# runs.audit
Auditoria diária. Sem LLM. Responde: "o sistema está saudável hoje?"

Critérios objetivos de `healthy`:
- missing_daily_collectors == 0
- failed_runs == 0
- zero_record_runs == 0 (quando expected_min > 0)

`health_check` retorna cada critério individualmente.
Depende de `collector_inventory` + `collector_runs`.
