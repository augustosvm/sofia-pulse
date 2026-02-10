# budget.guard
Block por padrão quando custo excede limite. Toda skill com LLM consulta ANTES.
`record_usage()` registra gasto após execução.
DDL: `sql/migrations/20250209_002_create_budget_tables.sql`
