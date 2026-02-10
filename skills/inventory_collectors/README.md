# inventory.collectors
Anti-entropia. Lista, valida, registra e audita collectors.
Actions: list, validate, register, deprecate, scan (auto-detect órfãos).
DDL: `sql/migrations/20250209_004_create_collector_inventory.sql`

**Scan:** encontra scripts no filesystem que não estão no inventário.
**Validate:** verifica se paths registrados existem no disco.
