# logger.event
Logging JSON com trace_id. Substitui print(). Grava em SOFIA_LOG_DIR com rotação diária.
Fallback: /tmp/sofia se /var/log/sofia sem permissão.

**Atalho:** `from skills.logger_event.src import log`
`log(trace_id, "collect.run", "collector.started", fetched=150)`
