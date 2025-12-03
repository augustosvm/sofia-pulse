# Sofia Pulse - Critical Features (Pre-Sprint 2)

**Data:** 2025-11-23
**Status:** Implementado e testado

---

## Resumo Executivo

Antes da Sprint 2, implementamos **4 funcionalidades críticas** que faltavam no Sofia Pulse:

| Feature | Status | Impacto |
|---------|--------|---------|
| **1. Canonical Keys** | ✅ Completo | Permite ligar entidades entre fontes (GitHub ↔ ArXiv ↔ Funding) |
| **2. Universal Changesets** | ✅ Completo | Time-travel queries, auditoria, análise de delta |
| **3. Data Provenance** | ✅ Completo | Transparência de licenças, qualidade, atribuição |
| **4. Intelligent Scheduler** | ✅ Completo | Orquestração robusta com retry, fallback, circuit breaker |

---

## 1. Canonical Keys — Universal Entity Resolution

### Problema
Cada coletor tinha sua própria chave:
- GitHub: `repo_id`
- ArXiv: `paper_id`
- World Bank: `indicator_code`
- NGOs: `name`

**Resultado:** Não era possível cruzar dados entre fontes.

### Solução
Criamos um sistema de **entidades canônicas universais** com UUID:

```sql
-- Tabela principal
canonical_entities (
    entity_id UUID,              -- Identificador universal
    entity_type ENUM,            -- company, person, paper, repository, etc.
    canonical_name TEXT,         -- Nome normalizado
    name_embedding vector(384),  -- Embedding para matching semântico
    aliases TEXT[],              -- Nomes alternativos
    ...
)

-- Mapeamento para fontes originais
entity_mappings (
    entity_id UUID,              -- Link para canonical_entities
    source_name TEXT,            -- 'github', 'arxiv', 'world_bank'
    source_table TEXT,           -- Tabela original
    source_id TEXT,              -- ID na fonte
    match_method TEXT,           -- 'exact', 'fuzzy', 'embedding'
    match_confidence FLOAT       -- 0.0-1.0
)

-- Relações entre entidades
entity_relationships (
    entity_id_from UUID,
    entity_id_to UUID,
    relationship_type TEXT,      -- 'founded_by', 'authored', 'funded'
    strength FLOAT
)
```

### Como Usar

#### Python
```python
from entity_resolver import EntityResolver

resolver = EntityResolver()

# Extrair entidades do GitHub
resolver.extract_github_repos(limit=500)

# Extrair papers do ArXiv
resolver.extract_arxiv_papers(limit=500)

# Encontrar entidades similares
similar = resolver.find_similar_entities('OpenAI GPT-4', entity_type='technology')
```

#### SQL
```sql
-- Criar ou encontrar entidade
SELECT sofia.find_or_create_entity(
    'OpenAI',
    'company',
    'crunchbase',
    'AI research company',
    ARRAY['OpenAI Inc.', 'Open AI'],
    '{"website": "https://openai.com"}'::JSONB
);

-- Ligar fonte ao canonical ID
SELECT sofia.link_entity_to_source(
    'uuid-da-entidade',
    'github',
    'github_trending',
    'openai-chatgpt',
    42,
    'exact',
    1.0
);

-- Buscar entidades similares por embedding
SELECT * FROM sofia.find_similar_entities(
    embedding_vector,
    'company',
    10,
    0.8
);
```

### Queries Úteis

```sql
-- Ver estatísticas por tipo
SELECT * FROM sofia.entity_stats_by_type;

-- Ver cobertura de fontes
SELECT * FROM sofia.cross_source_coverage;

-- Ver rede de relações
SELECT * FROM sofia.relationship_network_summary;

-- Encontrar todas as aparições de uma empresa
SELECT
    ce.canonical_name,
    em.source_name,
    em.source_table,
    em.source_id,
    em.match_confidence
FROM sofia.canonical_entities ce
JOIN sofia.entity_mappings em ON ce.entity_id = em.entity_id
WHERE ce.canonical_name ILIKE '%OpenAI%';
```

### Casos de Uso Habilitados

✅ **Founder Graph**: Link pessoas → empresas → funding → papers
✅ **Innovation Map**: Link papers → tecnologias → repos → produtos
✅ **Patent Intelligence**: Link patentes → empresas → repos GitHub
✅ **Research Impact**: Link papers → citações → implementações GitHub

---

## 2. Universal Changesets — Delta Tracking & Time-Travel

### Problema
Não tínhamos histórico de mudanças nos dados:
- Impossível saber o que mudou e quando
- Sem auditoria
- Sem time-travel queries
- Sem análise de tendências (delta)

### Solução
Tabela universal de **changesets** com delta automático:

```sql
changesets (
    id BIGSERIAL,
    source_name TEXT,              -- Fonte (github, world_bank, etc.)
    source_table TEXT,             -- Tabela
    source_pk TEXT,                -- Chave primária
    operation ENUM,                -- INSERT, UPDATE, DELETE
    payload_before JSONB,          -- Estado anterior
    payload_after JSONB,           -- Estado posterior
    delta JSONB GENERATED,         -- Delta automático
    collected_at TIMESTAMP,        -- Quando foi coletado
    ...
)
```

### Como Usar

#### Tracking Manual
```python
# Trackear uma mudança
changeset_id = track_changeset(
    source_name='github',
    source_table='github_trending',
    source_pk='12345',
    operation='UPDATE',
    payload_before={'stars': 100},
    payload_after={'stars': 150},
    change_magnitude=0.5  # 50% increase
)
```

#### Tracking Automático (Trigger)
```sql
-- Habilitar tracking automático para uma tabela
CREATE TRIGGER track_github_trending_changes
    AFTER INSERT OR UPDATE OR DELETE ON sofia.github_trending
    FOR EACH ROW EXECUTE FUNCTION sofia.changeset_trigger('github');
```

#### Time-Travel Queries
```sql
-- Ver estado de um registro em 1º de novembro
SELECT sofia.get_state_at_time(
    'github',
    'github_trending',
    '12345',
    '2025-11-01 00:00:00'
);

-- Ver histórico completo de mudanças
SELECT * FROM sofia.get_change_history(
    'github',
    'github_trending',
    '12345'
);

-- Resumo de deltas entre datas
SELECT * FROM sofia.get_delta_summary(
    'world_bank',
    'women_world_bank_data',
    '2025-11-01',
    '2025-11-23'
);
```

#### Undo Operations
```sql
-- Desfazer última mudança
SELECT sofia.undo_last_change(
    'github',
    'github_trending',
    '12345'
);
```

### Queries Úteis

```sql
-- Mudanças recentes (últimas 24h)
SELECT * FROM sofia.recent_changes;

-- Velocidade de mudanças por hora
SELECT * FROM sofia.change_velocity;

-- Registros mais modificados
SELECT * FROM sofia.top_modified_records;

-- Análise de tendências (forecasting)
SELECT
    source_table,
    operation,
    DATE_TRUNC('day', collected_at) as day,
    COUNT(*) as changes,
    AVG(change_magnitude) as avg_magnitude
FROM sofia.changesets
WHERE source_name = 'world_bank'
  AND collected_at >= NOW() - INTERVAL '30 days'
GROUP BY source_table, operation, DATE_TRUNC('day', collected_at)
ORDER BY day DESC;
```

### Casos de Uso

✅ **Auditoria**: Rastrear quem mudou o quê e quando
✅ **Undo/Redo**: Reverter mudanças indesejadas
✅ **Delta Analysis**: Análise de tendências para forecasting
✅ **Time-Travel**: Ver dados como estavam em qualquer data
✅ **Version Diff**: Comparar estados de dados

---

## 3. Data Provenance — Metadata & Transparency

### Problema
Não tínhamos metadados sobre as fontes:
- Qual licença? Pode vender?
- Qualidade dos dados?
- Frequência de atualização?
- Como citar?

### Solução
Sistema completo de **proveniência de dados**:

```sql
-- Registry de fontes
data_sources (
    source_id TEXT PRIMARY KEY,
    source_name TEXT,
    license_type ENUM,              -- CC_BY, CC0, GOVT_PUBLIC, etc.
    commercial_use_allowed BOOLEAN,
    attribution_required BOOLEAN,
    attribution_text TEXT,
    update_frequency ENUM,          -- DAILY, WEEKLY, MONTHLY, etc.
    data_quality_score FLOAT,
    ...
)

-- Proveniência por tabela
table_provenance (
    table_name TEXT PRIMARY KEY,
    source_id TEXT,
    collector_script TEXT,
    last_collection_run TIMESTAMP,
    collection_success_rate FLOAT,
    current_record_count BIGINT,
    ...
)

-- Proveniência por coluna
column_provenance (
    table_name TEXT,
    column_name TEXT,
    source_id TEXT,
    source_field TEXT,
    null_percentage FLOAT,
    ...
)
```

### Como Usar

#### Registrar Fonte
```python
from populate_data_provenance import *

# Já registramos 15+ fontes principais
# Execute: python3 scripts/populate_data_provenance.py
```

```sql
-- Registrar manualmente
SELECT sofia.register_data_source(
    'world_bank',
    'World Bank Gender Data Portal',
    'economic',
    'CC_BY',
    'https://data.worldbank.org/',
    true,  -- commercial use allowed
    'Source: World Bank Gender Data Portal (CC BY 4.0)',
    'MONTHLY'
);

-- Ligar tabela à fonte
SELECT sofia.link_table_to_source(
    'women_world_bank_data',
    'world_bank',
    'scripts/collect-women-world-bank.py'
);
```

#### Queries de Metadados
```sql
-- Ver todas as fontes
SELECT * FROM sofia.sources_summary;

-- Ver tabelas por fonte
SELECT * FROM sofia.tables_by_source;

-- Ver apenas fontes comerciais
SELECT * FROM sofia.commercial_sources;

-- Dashboard de qualidade
SELECT * FROM sofia.data_quality_dashboard;

-- Obter atribuição para uma tabela
SELECT sofia.get_attribution('women_world_bank_data');
```

### Fontes Registradas

| Fonte | Licença | Comercial? | Tabelas |
|-------|---------|-----------|---------|
| World Bank | CC BY 4.0 | ✅ Sim | 3 |
| Eurostat | Govt Public | ✅ Sim | 1 |
| FRED | Govt Public | ❌ Não (revenda) | 1 |
| ILO | CC BY 4.0 | ✅ Sim | 1 |
| IBGE | LAI (Govt) | ✅ Sim | 2 |
| ArXiv | CC BY | ✅ Sim | 1 |
| GitHub | Custom | ✅ Sim | 1 |
| OpenAlex | CC0 | ✅ Sim | 1 |
| UNODC | Govt Public | ✅ Sim | 1 |
| WHO | CC BY-NC-SA | ❌ Não comercial | 1 |
| ... | ... | ... | ... |

**Total:** 15+ fontes registradas
**Comercialmente permitido:** 76%
**Restrições:** 24%

### Casos de Uso

✅ **Sales**: Mostrar transparência para clientes
✅ **Portal**: Exibir atribuições e licenças
✅ **Compliance**: Verificar licenças antes de vender
✅ **Journalism**: Citar fontes corretamente
✅ **Quality Control**: Monitorar qualidade dos dados

---

## 4. Intelligent Scheduler — Orchestration Layer

### Problema
Cron simples não é suficiente:
- Sem retry quando falha
- Sem fallback
- Sem gestão de dependências
- Sem rate limiting
- Sem circuit breaker

### Solução
**Orquestrador inteligente** com:

```python
class IntelligentScheduler:
    """
    Features:
    - Retry com exponential backoff
    - Circuit breakers (open após N falhas)
    - Fallback para dados cacheados
    - Gestão de dependências
    - Priority queuing
    - Rate limiting
    - WhatsApp alerts
    """
```

### Como Usar

#### Registrar Collectors
```python
from intelligent_scheduler import IntelligentScheduler

scheduler = IntelligentScheduler()

# Registrar todos os collectors
scheduler.register_all_collectors()

# Ou registrar manualmente
scheduler.register_collector(
    collector_name='github_trending',
    script_path='scripts/incremental-loader-template.py',
    priority='critical',
    retry_max=5,
    retry_delay_sec=300,  # 5 min
    fallback_enabled=True,
    dependencies=[]
)

scheduler.register_collector(
    collector_name='brazil_security',
    script_path='scripts/collect-security-brazil.py',
    priority='normal',
    retry_max=2,
    dependencies=['brazil_ibge']  # Depende do IBGE
)
```

#### Executar
```bash
# Rodar uma vez
python3 scripts/intelligent_scheduler.py --run-once

# Rodar continuamente (loop a cada 5 min)
python3 scripts/intelligent_scheduler.py --run --interval 300
```

### Features

#### 1. Retry com Exponential Backoff
```python
# Configuração
retry_policy = RetryPolicy(
    max_attempts=3,
    initial_delay_sec=60,      # 1 min
    max_delay_sec=3600,        # 1 hora
    backoff_multiplier=2.0     # 2x a cada tentativa
)

# Tentativas:
# 1ª falha → espera 1 min
# 2ª falha → espera 2 min
# 3ª falha → espera 4 min
# Esgotado → fallback
```

#### 2. Circuit Breaker
```python
# Após 5 falhas consecutivas, abre circuito
# Espera 5 minutos (recovery timeout)
# Testa com 1 chamada (half-open)
# Se sucesso → fecha circuito
# Se falha → reabre circuito

circuit_breaker = CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout_sec=300,
    half_open_max_calls=1
)
```

#### 3. Fallback
```python
# Se todas as tentativas falharem:
# 1. Tenta usar dados cacheados (últimas 24h)
# 2. Tenta usar dados de ontem
# 3. Envia alerta e pula

fallback_policy = FallbackPolicy(
    enabled=True,
    use_cached_data=True,
    cache_max_age_hours=24,
    fallback_to_yesterday=True,
    notify_on_fallback=True
)
```

#### 4. Dependency Management
```python
# Se dependency está down há >48h, pausa dependentes
# Exemplo: brazil_security depende de brazil_ibge

if ibge_down_for_48h:
    pause_brazil_security()
    send_alert("Security collector paused - IBGE down")
```

### Casos de Uso

✅ **HN falha** → Retry 3x com backoff → Fallback para cache
✅ **GitHub rate limit** → Pausa 1 hora → Resume
✅ **B3 API error** → Usa dados de ontem → Alerta WhatsApp
✅ **Collector travado** → Detecta após 2h → Mata e restart
✅ **Dependency down** → Pausa dependentes → Resume quando volta

---

## Deployment

### Deploy para o Servidor

```bash
# Executar script de deployment
./deploy-critical-features.sh

# O script faz:
# 1. Upload SQL migrations
# 2. Executa migrations no PostgreSQL
# 3. Upload Python scripts
# 4. Popula data provenance
# 5. Verifica deployment
# 6. Testa entity resolution
```

### Verificação Manual

```bash
# SSH no servidor
ssh ubuntu@91.98.158.19
cd /home/ubuntu/sofia-pulse

# Verificar tabelas criadas
docker exec -i sofia-postgres psql -U sofia -d sofia_db -c "\dt sofia.*"

# Ver canonical entities
docker exec -i sofia-postgres psql -U sofia -d sofia_db -c "SELECT * FROM sofia.entity_stats_by_type;"

# Ver data sources
docker exec -i sofia-postgres psql -U sofia -d sofia_db -c "SELECT * FROM sofia.sources_summary;"

# Ver changesets
docker exec -i sofia-postgres psql -U sofia -d sofia_db -c "SELECT COUNT(*) FROM sofia.changesets;"
```

### Próximos Passos

1. **Extrair entidades de dados existentes:**
   ```bash
   python3 scripts/entity_resolver.py --extract-all --limit 1000
   ```

2. **Iniciar scheduler inteligente:**
   ```bash
   python3 scripts/intelligent_scheduler.py --register-all --run
   ```

3. **Habilitar tracking de changesets:**
   ```sql
   CREATE TRIGGER track_github_changes
       AFTER INSERT OR UPDATE OR DELETE ON sofia.github_trending
       FOR EACH ROW EXECUTE FUNCTION sofia.changeset_trigger('github');
   ```

---

## Arquivos Criados

### SQL Migrations
- `sql/01-canonical-entities.sql` (600 linhas)
- `sql/02-changesets.sql` (500 linhas)
- `sql/03-data-provenance.sql` (550 linhas)

### Python Scripts
- `scripts/entity_resolver.py` (800 linhas)
- `scripts/intelligent_scheduler.py` (700 linhas)
- `scripts/populate_data_provenance.py` (350 linhas)

### Deployment
- `deploy-critical-features.sh` (200 linhas)
- `CRITICAL-FEATURES-README.md` (este arquivo)

---

## Impacto

### Antes
❌ Dados isolados por fonte (GitHub, ArXiv, World Bank separados)
❌ Sem histórico de mudanças
❌ Sem metadados de licenciamento
❌ Cron simples sem retry/fallback
❌ Impossível cruzar dados entre fontes
❌ Sem auditoria
❌ Sem transparência de qualidade

### Depois
✅ **Canonical Keys**: Entidades universais com UUID
✅ **Changesets**: Histórico completo + time-travel
✅ **Provenance**: Metadados de 15+ fontes
✅ **Scheduler**: Orquestração robusta
✅ **Cross-Source**: Founder Graph, Innovation Map
✅ **Auditoria**: Undo, version diff, audit trail
✅ **Transparência**: Licenças, qualidade, atribuição

---

## Conclusão

Todas as **4 funcionalidades críticas** estão implementadas e prontas para uso.

**Status:** ✅ **PRONTO PARA SPRINT 2**

---

**Próxima etapa:** Sprint 2 - Chat Sofia + Narrativas IA + Portal Web

Documento gerado em: 2025-11-23
Versão: 1.0
