# Sofia Skills — Error Codes

Códigos oficiais. Não invente sem registrar aqui.

| Code | Retryable | Quando |
|------|-----------|--------|
| INVALID_INPUT | false | params não bateu schema |
| TIMEOUT | true | Passou do limite |
| UNKNOWN_ERROR | false | Catch genérico |
| DB_CONNECTION_FAILED | true | Conexão caiu |
| DB_QUERY_FAILED | false | SQL erro |
| HTTP_REQUEST_FAILED | true | Erro transitório |
| HTTP_RATE_LIMITED | true | 429 |
| HTTP_AUTH_FAILED | false | 401/403 |
| BUDGET_EXCEEDED | false | budget.guard bloqueou |
| BUDGET_WARNING | — | Warning |
| COLLECT_EMPTY | false | fetched==0 ou saved==0 |
| COLLECT_SOURCE_DOWN | true | API fora |
| COLLECT_PARSE_ERROR | false | Formato mudou |
| NORMALIZE_FAILED | false | Campo obrigatório faltando |
| NORMALIZE_PARTIAL | false | Warning parcial |
| INSUFFICIENT_DATA | false | Poucos sinais |
| INSUFFICIENT_EVIDENCE | false | Brief sem fontes |
| SEARCH_NO_RESULTS | false | RAG vazio |
| SEARCH_EMBEDDING_FAILED | true | API de embedding |
| LLM_REQUEST_FAILED | true | Erro transitório |
| LLM_BUDGET_BLOCKED | false | budget.guard |
| INVENTORY_NOT_FOUND | false | Collector path não existe |
| DEPENDENCY_MISSING | false | Python/Node module ou comando ausente |
| FS_ERROR | false | Permission denied, No such file/directory (FS) |
| SCRIPT_ERROR | false | Exit code != 0 (erro no script) |
| AUDIT_NO_RUNS_TODAY | false | Nenhum run registrado |
