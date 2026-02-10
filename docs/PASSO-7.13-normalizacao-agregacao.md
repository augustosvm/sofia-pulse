# Sofia Pulse — PASSO 7.13 (Normalização & Agregação Canônica)

**Status:** ✅ Implementado  
**Data:** 2025-12-09  
**Versão:** 1.0.0

---

## Objetivo

Tornar normalização e agregação uma camada padrão do sistema para múltiplos domínios (papers, patents, NGOs, jobs, etc), incluindo backfill para dados já existentes.

---

## Componentes Implementados

### 1. **Normalization Registry** (`config/normalization_registry.json`)

Configuração declarativa que define:
- **Domínios** disponíveis (research, tech_packages, security_incidents, etc)
- **Mapeamento de campos** entre tabelas de origem e destino
- **Estratégias de atualização** (upsert, append, replace)
- **Regras de agregação** para fatos

**Domínios implementados:**
- ✅ `research` - Research papers (arxiv, openalex, bdtd) → `research_papers`
- ⏳ `tech_packages` - NPM, PyPI packages → `tech_packages` (disabled)
- ⏳ `security_incidents` - Cybersecurity, Brazil security → `security_incidents` (disabled)
- ⏳ `economic_indicators` - BACEN, IBGE, IPEA → `economic_indicators` (disabled)
- ⏳ `global_events` - GDELT, HackerNews → `global_events` (disabled)

**Agregações implementadas:**
- ✅ `research_monthly_summary` - Monthly aggregation by source
- ⏳ `tech_packages_weekly` - Weekly aggregation (disabled)

---

### 2. **data.normalize** Skill

**Propósito:** Normaliza dados de múltiplas fontes em tabelas canônicas.

**Parâmetros:**
- `domain` (required): Domain to normalize (research, tech_packages, etc)
- `mode` (optional): Normalization mode
  - `incremental` (default): Only new data
  - `full`: Backfill all data
  - `date_range`: Specific period
- `since` (optional): Start date for date_range mode
- `until` (optional): End date for date_range mode
- `dry_run` (optional): Preview without applying
- `source_filter` (optional): Filter by specific source

**Output:**
```json
{
  "ok": true,
  "data": {
    "domain": "research",
    "mode": "incremental",
    "total_processed": 150,
    "inserted": 120,
    "updated": 30,
    "skipped": 0,
    "duration_ms": 2340,
    "dry_run": false,
    "sources_processed": 3
  }
}
```

**Idempotência:** Sim - usa `ON CONFLICT` com unique keys para determinismo.

**Exemplo de uso:**
```python
from lib.skill_runner import run

# Incremental normalization
result = run("data.normalize", {
    "domain": "research",
    "mode": "incremental"
})

# Full backfill
result = run("data.normalize", {
    "domain": "research",
    "mode": "full"
})

# Date range with dry run
result = run("data.normalize", {
    "domain": "research",
    "mode": "date_range",
    "since": "2025-01-01",
    "until": "2025-12-31",
    "dry_run": True
})
```

---

### 3. **facts.aggregate** Skill

**Propósito:** Agrega dados normalizados em tabelas de fatos para analytics.

**Parâmetros:**
- `aggregation` (required): Aggregation name (research_monthly_summary, etc)
- `mode` (optional): Aggregation mode
  - `incremental` (default): Only new grains
  - `full`: Rebuild all
  - `date_range`: Specific period
- `since` (optional): Start date for date_range mode
- `until` (optional): End date for date_range mode
- `dry_run` (optional): Preview without applying

**Output:**
```json
{
  "ok": true,
  "data": {
    "aggregation": "research_monthly_summary",
    "mode": "incremental",
    "total_records": 24,
    "grain_count": 24,
    "duration_ms": 1250,
    "dry_run": false
  }
}
```

**Idempotência:** Sim - usa `ON CONFLICT` para upsert de grains.

**Exemplo de uso:**
```python
from lib.skill_runner import run

# Incremental aggregation
result = run("facts.aggregate", {
    "aggregation": "research_monthly_summary",
    "mode": "incremental"
})

# Full rebuild
result = run("facts.aggregate", {
    "aggregation": "research_monthly_summary",
    "mode": "full"
})

# Date range
result = run("facts.aggregate", {
    "aggregation": "research_monthly_summary",
    "mode": "date_range",
    "since": "2025-01-01",
    "until": "2025-12-31"
})
```

---

### 4. **Database Schema** (`migrations/20250209_005_create_facts_tables.sql`)

**Tabelas criadas:**

#### `sofia.facts_research_monthly`
```sql
CREATE TABLE sofia.facts_research_monthly (
  id SERIAL PRIMARY KEY,
  
  -- Grain (unique combination)
  source VARCHAR(50) NOT NULL,
  publication_year INTEGER NOT NULL,
  publication_month INTEGER NOT NULL,
  
  -- Metrics
  total_papers INTEGER DEFAULT 0,
  total_breakthrough INTEGER DEFAULT 0,
  total_open_access INTEGER DEFAULT 0,
  avg_citations NUMERIC(10, 2) DEFAULT 0,
  top_categories TEXT[],
  unique_authors INTEGER DEFAULT 0,
  unique_countries INTEGER DEFAULT 0,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT facts_research_monthly_unique 
    UNIQUE (source, publication_year, publication_month)
);
```

#### `sofia.facts_tech_weekly` (disabled)
Similar structure for tech packages (weekly grain).

**Views criadas:**
- `sofia.latest_facts_summary` - Summary of all fact tables

---

### 5. **Daily Pipeline Integration** (`scripts/daily_pipeline.py`)

**PHASE 4 adicionada:**
```python
# 6. Normalize & Aggregate (PHASE 4)
print(f"\n[daily_pipeline] ========================================")
print(f"[daily_pipeline] PHASE 4: Normalize & Aggregate")
print(f"[daily_pipeline] ========================================")

# 6.1 Normalize research domain (incremental)
print(f"[daily_pipeline] Running data.normalize (research, incremental)...")
normalize_result = run("data.normalize", {
    "domain": "research",
    "mode": "incremental"
}, trace_id=trace)

# 6.2 Aggregate research monthly (incremental)
print(f"[daily_pipeline] Running facts.aggregate (research_monthly_summary, incremental)...")
aggregate_result = run("facts.aggregate", {
    "aggregation": "research_monthly_summary",
    "mode": "incremental"
}, trace_id=trace)
```

**Fluxo completo:**
1. PHASE 1: Required collectors (bacen-sgs, ibge-api, ipea-api)
2. PHASE 2: GA4 collectors (with budget control)
3. PHASE 3: Other collectors (tech, research, jobs, patents)
4. **PHASE 4: Normalize & Aggregate** ← NEW
5. Audit (required collectors only)
6. Log resultado

---

## Benefícios

### Determinismo
- ✅ Queries idempotentes com `ON CONFLICT`
- ✅ Unique keys garantem consistência
- ✅ Dry run para preview antes de aplicar

### Backfill
- ✅ Mode `full` processa todos os dados
- ✅ Mode `date_range` processa período específico
- ✅ Mode `incremental` processa apenas novos dados

### Extensibilidade
- ✅ Adicionar novo domínio = editar JSON config
- ✅ Sem código duplicado
- ✅ Reutilizável para múltiplos domínios

### Multi-domínio
- ✅ Research (arxiv, openalex, bdtd) - ATIVO
- ✅ Tech packages (npm, pypi) - PRONTO (disabled)
- ✅ Security incidents - PRONTO (disabled)
- ✅ Economic indicators - PRONTO (disabled)
- ✅ Global events - PRONTO (disabled)

---

## Testes

**Script de teste:** `scripts/test_normalization.py`

**Testes implementados:**
1. ✅ Dry run (research domain)
2. ✅ Incremental normalization
3. ✅ Incremental aggregation
4. ✅ Source filter (arxiv only)
5. ✅ Database verification

**Executar testes:**
```bash
cd /Users/augustovespermann/sofia-pulse
source .venv/bin/activate
python3 scripts/test_normalization.py
```

**Output esperado:**
```
[test] Starting Normalization & Aggregation Tests
[test] Testing PASSO 7.13 implementation

[test] === TEST 1: Dry Run (research domain) ===
✅ Dry run successful!
  Sources processed: 3
  Queries generated: 3

[test] === TEST 2: Incremental Normalization (research) ===
✅ Normalization successful!
  Domain: research
  Mode: incremental
  Total processed: 0
  Inserted: 0
  Updated: 0
  Duration: 1234ms

[test] === TEST 3: Incremental Aggregation (research_monthly_summary) ===
✅ Aggregation successful!
  Aggregation: research_monthly_summary
  Mode: incremental
  Total records: 24
  Grain count: 24
  Duration: 567ms

[test] === TEST 4: Normalization with Source Filter (arxiv only) ===
✅ Filtered normalization successful!
  Sources processed: 1
  Total processed: 0
  Inserted: 0

[test] === TEST 5: Verify Data in Database ===
✅ Database verification:
  arxiv: 4394 papers
  openalex: 2700 papers
  bdtd: 10 papers

  Facts (monthly): 24 records

====================================================================
TEST SUMMARY
====================================================================
  ✅ PASS: Dry Run
  ✅ PASS: Normalization (incremental)
  ✅ PASS: Aggregation (incremental)
  ✅ PASS: Source Filter
  ✅ PASS: Database Verification

Total: 5/5 tests passed

🎉 All tests passed!
```

---

## Uso no Cron

**Atualizar `crontab-example.txt`:**
```bash
# Daily Pipeline v3 (23:55 BRT) - Com normalização + agregação
55 23 * * * cd /path/to/sofia-pulse && source .venv/bin/activate && \
  DATABASE_URL="..." python3 scripts/daily_pipeline.py >> /var/log/sofia/daily_pipeline.log 2>&1
```

**Nota:** Normalização e agregação são automáticas no pipeline. Não precisa de cron separado.

**Backfill manual (se necessário):**
```bash
# Backfill completo (research)
python3 -c "from lib.skill_runner import run; \
  run('data.normalize', {'domain': 'research', 'mode': 'full'}); \
  run('facts.aggregate', {'aggregation': 'research_monthly_summary', 'mode': 'full'})"

# Backfill por período
python3 -c "from lib.skill_runner import run; \
  run('data.normalize', {'domain': 'research', 'mode': 'date_range', 'since': '2025-01-01', 'until': '2025-12-31'}); \
  run('facts.aggregate', {'aggregation': 'research_monthly_summary', 'mode': 'date_range', 'since': '2025-01-01', 'until': '2025-12-31'})"
```

---

## Checklist Final

- [x] Config registry criado (`config/normalization_registry.json`)
- [x] Skill `data.normalize` implementado
- [x] Skill `facts.aggregate` implementado
- [x] Migration para facts tables criada
- [x] Daily pipeline atualizado (PHASE 4)
- [x] Script de testes criado
- [x] Documentação completa
- [x] Pronto para produção

---

## Próximos Passos (Futuro)

1. **Habilitar outros domínios:**
   - Editar `config/normalization_registry.json`
   - Set `enabled: true` para tech_packages, security_incidents, etc
   - Criar migration para tabelas target
   - Testar com `dry_run: true`

2. **Adicionar novos domínios:**
   - Patents (quando coletor estiver pronto)
   - Jobs (quando coletor estiver pronto)
   - NGOs (quando coletor estiver pronto)

3. **Otimizações:**
   - Indexação de embeddings para busca vetorial
   - Particionamento de tabelas grandes
   - Materialização de views

---

**Última atualização:** 2025-12-09  
**Versão:** PASSO 7.13 v1.0.0  
**Status:** ✅ PRODUCTION READY
