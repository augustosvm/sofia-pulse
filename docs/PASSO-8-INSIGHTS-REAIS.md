# Sofia Pulse — PASSO 8 (Geração Real de Insights)

**Status:** ✅ IMPLEMENTADO  
**Data:** 2025-12-09  
**Versão:** 1.0.0

---

## 🎯 Objetivo

Transformar Sofia Pulse de um coletor burro em um **sistema cognitivo de dados** que:
- Gera insights reais diariamente
- Baseados apenas em dados normalizados
- Alertas inteligentes via WhatsApp
- Zero processamento inútil

---

## 📦 Componentes Implementados

### 1. PARTE 1 - Auditoria e Correção do PASSO 7.13

✅ **Entidades Normalizadas:**
- `sofia.countries` - Países normalizados
- `sofia.organizations` - Universidades e instituições
- `sofia.authors` - Autores normalizados
- `sofia.paper_authors` - Junction papers ↔ authors
- `sofia.paper_countries` - Junction papers ↔ countries
- `sofia.paper_organizations` - Junction papers ↔ organizations

✅ **Migration:** `20250209_006_normalize_entities.sql`

✅ **Skill data.normalize atualizada:**
- Função `normalize_entities_for_research()` adicionada
- Extrai authors, countries, organizations de research_papers
- Popula tabelas junction automaticamente
- Idempotente (ON CONFLICT DO NOTHING)

✅ **Resultados:**
- 9 authors normalizados
- 1 organization (USP)
- 10 countries (seed data)
- 9 paper-author links
- 1 paper-organization link

---

### 2. PARTE 2 - PASSO 8: Geração Real de Insights

#### 8.1 - Tabela `sofia.insights`

**Migration:** `20250209_007_create_insights_table.sql`

**Schema:**
```sql
CREATE TABLE sofia.insights (
  insight_id SERIAL PRIMARY KEY,
  domain VARCHAR(50) NOT NULL,        -- research, tech, jobs, security, economy
  insight_type VARCHAR(100) NOT NULL, -- growth_spike, technology_trend, anomaly
  title VARCHAR(500) NOT NULL,
  summary TEXT NOT NULL,
  severity VARCHAR(20) NOT NULL,      -- info, warning, critical
  evidence JSONB NOT NULL,            -- Prova do insight
  generated_at TIMESTAMP DEFAULT NOW(),
  trace_id UUID,
  watermark TIMESTAMP,                -- last_processed_at
  evidence_hash VARCHAR(64) UNIQUE,   -- Deduplicação
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Views:**
- `sofia.latest_insights_by_domain` - Últimos insights por domínio
- `sofia.critical_insights` - Top 50 insights críticos

---

#### 8.2 - Skill `insights.generate`

**Localização:** `skills/insights_generate/`

**Responsabilidades:**
- ✅ Consumir APENAS dados normalizados e agregados
- ✅ Gerar insights para: research, tech, jobs, security, economy
- ✅ Nunca ler dados brutos
- ✅ Usar watermark para incremental processing
- ✅ Deduplicação via evidence_hash
- ✅ Salvar em `sofia.insights`

**Parâmetros:**
```python
run("insights.generate", {
    "domains": ["research"],         # Opcional, default = ["research"]
    "since": "2025-12-08T00:00:00Z", # Watermark (opcional)
    "dry_run": False                 # Preview (opcional)
})
```

**Output:**
```json
{
  "ok": true,
  "data": {
    "insights_generated": 5,
    "by_domain": {"research": 5},
    "by_severity": {"info": 3, "warning": 2, "critical": 0},
    "watermark": "2025-12-09T12:00:00Z",
    "duration_ms": 234
  }
}
```

---

#### 8.3 - Detectores de Insights Implementados

**Research Domain:**

1. **Crescimento Anormal por Organização**
   - Detecta organizações com 2x+ publicações acima da média histórica
   - Severity: warning (>3x), info (2x-3x)
   - Evidence: organization, recent_papers, historical_avg, growth_factor

2. **Concentração de Breakthrough Papers**
   - Detecta fontes com ≥3 papers breakthrough em 90 dias
   - Severity: info
   - Evidence: source, breakthrough_count, percentage

3. **Crescimento Mensal (Aggregation)**
   - Detecta crescimento >50% mês-a-mês em facts_research_monthly
   - Severity: warning (>100%), info (50%-100%)
   - Evidence: source, year, month, current_papers, previous_papers, growth_pct

---

#### 8.4 - Integração ao Daily Pipeline

**PHASE 5 adicionada:** (após Normalize & Aggregate, antes do Audit)

```python
# 7. Generate Insights (PHASE 5)
insights_result = run("insights.generate", {
    "domains": ["research"]
}, trace_id=trace)

# Alertas WhatsApp inteligentes
critical_count = ins_data['by_severity'].get('critical', 0)
total_insights = ins_data['insights_generated']

if critical_count > 0 or total_insights >= 5:
    run("notify.whatsapp", {
        "to": "admin",
        "severity": "critical" if critical_count > 0 else "warning",
        "title": "🔔 Sofia Pulse - Insights Críticos",
        "message": alert_message,
        "summary": {...}
    }, trace_id=trace)
```

**Fluxo Completo:**
1. PHASE 1: Required collectors
2. PHASE 2: GA4 collectors (OBRIGATÓRIO)
3. PHASE 3: Other collectors (best-effort)
4. PHASE 4: Normalize & Aggregate
5. **PHASE 5: Generate Insights** ⭐ **NOVO**
6. PHASE 6: Audit
7. PHASE 7: Log resultado

---

#### 8.5 - Alertas WhatsApp Inteligentes

**Critérios para Envio:**
- ✅ `severity = 'critical'` - Sempre envia
- ✅ `total_insights >= 5` - Volume alto
- ❌ Caso contrário - Não envia (anti-spam)

**Formato da Mensagem:**
```
🔔 Sofia Pulse - Insights Críticos

*Resumo Diário de Insights*

Total: 7 insights gerados
• Info: 4
• Warning: 2
• Critical: 1

Por domínio:
• research: 7
```

**Integração:**
- Usa skill `notify.whatsapp` existente (Baileys)
- Best-effort (não falha pipeline se alertas falharem)

---

## 🛑 Anti-Lixo & Anti-Entropia

**Implementado:**

1. **Nada roda sem necessidade**
   - Watermark tracking (`since` parameter)
   - Insights só rodam se houver novos dados normalizados

2. **Nada duplica**
   - `evidence_hash` unique constraint
   - `ON CONFLICT (evidence_hash) DO NOTHING`

3. **Nada obscuro**
   - Tudo passa por `skill_runner`
   - Tudo tem `trace_id`
   - Logs estruturados

4. **Zero BigQuery (exceto GA4)**
   - ✅ Cumprido - Insights baseados em dados normalizados locais

5. **Zero collectors novos**
   - ✅ Cumprido - Usa collectors existentes

6. **Zero processamento inútil**
   - ✅ Cumprido - Insights só quando há novos dados

---

## ⏰ CRON (OBRIGATÓRIO)

**Atualizado:** `docs/crontab-example.txt`

```bash
# Daily Pipeline v3 (23:55 BRT) - COM INSIGHTS
55 23 * * * cd /path/to/sofia-pulse && source .venv/bin/activate && \
  DATABASE_URL="$DATABASE_URL" python3 scripts/daily_pipeline.py >> /var/log/sofia/daily_pipeline.log 2>&1

# GA4 roda DENTRO do pipeline (PHASE 2) - OBRIGATÓRIO DIARIAMENTE
```

---

## 📊 Arquitetura Final

```
┌─────────────────────────────────────────────────────────┐
│                  Daily Pipeline v3                      │
└────────────┬────────────────────────────────────────────┘
             │
             ├─ PHASE 1: Required Collectors
             │
             ├─ PHASE 2: GA4 Collectors (budget.guard) ⚠️ OBRIGATÓRIO
             │
             ├─ PHASE 3: Other Collectors (best-effort)
             │
             ├─ PHASE 4: Normalize & Aggregate
             │  ├─ data.normalize (research)
             │  │  └─ Normalize entities (authors, countries, orgs)
             │  └─ facts.aggregate (research_monthly_summary)
             │
             ├─ PHASE 5: Generate Insights ⭐ NOVO
             │  ├─ insights.generate (research)
             │  │  └─ Detect: growth spikes, breakthroughs, trends
             │  └─ notify.whatsapp (if critical or high volume)
             │
             ├─ PHASE 6: Audit
             └─ PHASE 7: Log resultado
```

---

## 🧪 Testes

### Teste Manual

```bash
cd /Users/augustovespermann/sofia-pulse
source .venv/bin/activate

# Test entity normalization
DATABASE_URL="..." python3 -c "
from lib.skill_runner import run
result = run('data.normalize', {'domain': 'research', 'mode': 'full'})
print(result['data']['entity_normalization'])
"

# Test insights generation (dry run)
DATABASE_URL="..." python3 -c "
from lib.skill_runner import run
result = run('insights.generate', {'domains': ['research'], 'dry_run': True})
print(f\"Insights: {result['data']['insights_generated']}\")
print(f\"By severity: {result['data']['by_severity']}\")
"

# Test full pipeline
DATABASE_URL="..." python3 scripts/daily_pipeline.py
```

### Output Esperado (Pipeline)

```
[daily_pipeline] ========================================
[daily_pipeline] PHASE 5: Generate Insights
[daily_pipeline] ========================================
[daily_pipeline] Running insights.generate...
  ✅ Insights generated: 5
     By severity: info=3, warning=2, critical=0
```

---

## ✅ Definição de Pronto (DoD)

- [x] Insights são gerados diariamente
- [x] Baseados apenas em dados normalizados
- [x] Persistidos no banco (`sofia.insights`)
- [x] WhatsApp alerta funciona (se critical ou volume alto)
- [x] Zero BigQuery fora GA4
- [x] Zero collectors novos
- [x] Zero processamento inútil (watermark + evidence_hash)
- [x] Código testável e legível
- [x] GA4 roda diariamente (PHASE 2 do pipeline)
- [x] Entidades normalizadas (authors, countries, organizations)

---

## 🚀 Próximos Passos (Futuro)

1. **Habilitar outros domínios:**
   - tech: GitHub trends, StackOverflow, Docker, npm/pypi
   - jobs: Vagas abertas, tendências de mercado
   - security: Incidentes, vulnerabilidades
   - economy: Indicadores BACEN, IBGE, IPEA

2. **Detectores adicionais:**
   - Correlações entre domínios (papers + GitHub + jobs)
   - Anomalias em séries temporais
   - Clustering de tópicos emergentes
   - Predições simples (regressão linear)

3. **Dashboard:**
   - Grafana dashboard para insights
   - Visualização de trends
   - Drill-down por domínio/severity

4. **API REST:**
   - `GET /api/insights` - Listar insights
   - `GET /api/insights/:id` - Detalhes
   - `GET /api/insights/critical` - Últimos críticos

---

**🎉 PASSO 8 CONCLUÍDO COM SUCESSO!**

**Última atualização:** 2025-12-09  
**Versão:** 1.0.0  
**Status:** PRODUCTION READY ✅

Sofia Pulse agora é um **sistema cognitivo de dados** que:
- ✅ Coleta dados automaticamente
- ✅ Normaliza e agrega canonicamente
- ✅ Gera insights reais diariamente
- ✅ Alerta via WhatsApp quando necessário
- ✅ Zero lixo, zero duplicação, zero entropia
