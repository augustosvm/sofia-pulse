# 🏗️ Sofia Pulse - Arquitetura do Sistema

Este documento descreve a arquitetura completa do Sofia Pulse, incluindo componentes, fluxos de dados, decisões de design e padrões arquiteturais.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Componentes Principais](#componentes-principais)
- [Fluxo de Dados](#fluxo-de-dados)
- [Módulos](#módulos)
- [Database Design](#database-design)
- [Segurança](#segurança)
- [Escalabilidade](#escalabilidade)
- [Monitoramento](#monitoramento)
- [Decisões de Design](#decisões-de-design)

---

## 🎯 Visão Geral

Sofia Pulse utiliza uma **arquitetura modular** baseada em:

- **Event-driven collection**: Coleta acionada por eventos (cron, webhooks)
- **Data lake approach**: Armazenamento raw + processado
- **Microserviços light**: Módulos independentes mas integrados
- **API-first**: Todas funcionalidades expostas via API

### Princípios Arquiteturais

1. **Separation of Concerns**: Cada módulo tem responsabilidade única
2. **Fail Fast**: Erros detectados e reportados rapidamente
3. **Idempotency**: Coletas podem ser re-executadas sem duplicação
4. **Observability**: Logs, métricas e tracing em todos os componentes
5. **Scalability**: Componentes escaláveis horizontalmente

---

## 🧩 Componentes Principais

```
┌─────────────────────────────────────────────────────────────────┐
│                        SOFIA PULSE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Collectors │  │  Processors │  │  Analyzers  │            │
│  │  (Coleta)   │─▶│ (Transform) │─▶│  (Insights) │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         │                 │                 │                   │
│         └─────────────────┴─────────────────┘                   │
│                           │                                     │
│                           ▼                                     │
│                  ┌─────────────────┐                            │
│                  │   PostgreSQL    │                            │
│                  │    (sofia_db)   │                            │
│                  └─────────────────┘                            │
│                           │                                     │
│         ┌─────────────────┴─────────────────┐                   │
│         ▼                                   ▼                   │
│  ┌─────────────┐                    ┌─────────────┐            │
│  │  REST API   │                    │  Dashboards │            │
│  │   (Future)  │                    │   (Grafana) │            │
│  └─────────────┘                    └─────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1. Collectors (Coletores)

**Responsabilidade**: Buscar dados de fontes externas

**Características**:
- Um collector por fonte de dados
- Stateless (sem estado entre execuções)
- Retry logic com exponential backoff
- Rate limiting respeitado
- Data validation antes de persistir

**Localização**: `scripts/collect-*.ts`

**Exemplo**:
```typescript
// scripts/collect-arxiv.ts
class ArXivCollector {
  async collect(since?: Date): Promise<Paper[]> {
    // 1. Fetch from ArXiv API
    // 2. Validate data
    // 3. Transform to internal format
    // 4. Return papers
  }

  async persist(papers: Paper[]): Promise<void> {
    // 1. Connect to DB
    // 2. Insert with UPSERT logic
    // 3. Log results
  }
}
```

### 2. Processors (Processadores)

**Responsabilidade**: Transformar e enriquecer dados

**Características**:
- Normalização de dados
- Feature extraction
- Data cleaning
- Enrichment (adicionar metadata)

**Localização**: `src/processors/`

**Exemplo**:
```typescript
// src/processors/paper-processor.ts
class PaperProcessor {
  extractKeywords(abstract: string): string[] {
    // NLP para extrair keywords
  }

  calculateRelevanceScore(paper: Paper): number {
    // Score baseado em citações, autores, etc
  }

  enrichWithCitations(paper: Paper): EnrichedPaper {
    // Buscar citações externas
  }
}
```

### 3. Analyzers (Analisadores)

**Responsabilidade**: Gerar insights e correlações

**Características**:
- Correlação multi-fonte
- Score computation
- Trend detection
- Anomaly detection

**Localização**: `src/analyzers/`

**Exemplo**:
```typescript
// src/analyzers/innovation-analyzer.ts
class InnovationAnalyzer {
  async computeInnovationScore(company: string): Promise<Score> {
    const patents = await getPatents(company);
    const papers = await getPapers(company);
    const funding = await getFunding(company);

    return {
      score: this.weightedAverage([
        { value: patents.length, weight: 0.3 },
        { value: papers.length, weight: 0.2 },
        { value: funding.total, weight: 0.5 }
      ]),
      breakdown: { patents, papers, funding }
    };
  }
}
```

### 4. Database (PostgreSQL)

**Responsabilidade**: Persistência e queries

**Características**:
- PostgreSQL 15+ com pgvector extension
- Indexes otimizados para queries comuns
- Partitioning por data em tabelas grandes
- Materialized views para agregações

**Schema**: Ver [SCHEMA.md](docs/SCHEMA.md)

### 5. API Layer (Futuro)

**Responsabilidade**: Expor dados via REST/GraphQL

**Características**:
- RESTful endpoints
- Authentication (JWT)
- Rate limiting
- Caching (Redis)
- API versioning

---

## 🔄 Fluxo de Dados

### Coleta → Armazenamento

```
┌──────────┐
│ External │
│   API    │
└────┬─────┘
     │ HTTP Request
     ▼
┌──────────────┐
│  Collector   │
│  - Fetch     │
│  - Validate  │
│  - Transform │
└────┬─────────┘
     │ Validated Data
     ▼
┌──────────────┐
│  Processor   │
│  - Normalize │
│  - Enrich    │
│  - Clean     │
└────┬─────────┘
     │ Processed Data
     ▼
┌──────────────┐
│ PostgreSQL   │
│  INSERT/     │
│  UPSERT      │
└──────────────┘
```

### Análise → Insights

```
┌──────────────┐
│ PostgreSQL   │
│  Raw Data    │
└────┬─────────┘
     │ SQL Query
     ▼
┌──────────────┐
│  Analyzer    │
│  - Correlate │
│  - Score     │
│  - Rank      │
└────┬─────────┘
     │ Insights
     ▼
┌──────────────┐
│   Output     │
│  - JSON      │
│  - Dashboard │
│  - API       │
└──────────────┘
```

### Automação (Cron)

```
┌──────────┐
│  Cron    │
│  Job     │
└────┬─────┘
     │ Scheduled Time
     ▼
┌──────────────┐
│  cron-*.sh   │
│  Script      │
└────┬─────────┘
     │ Execute
     ▼
┌──────────────┐
│ Collectors   │
│ (sequential) │
└────┬─────────┘
     │ Data Collected
     ▼
┌──────────────┐
│   Logger     │
│  - Success   │
│  - Errors    │
└──────────────┘
```

---

## 📦 Módulos

### Module: Academia

**Fontes**: ArXiv, BDTD, SciELO

**Responsabilidades**:
- Coleta de papers, teses, artigos
- Extração de metadata científica
- Tracking de citações
- Identificação de autores/instituições

**Arquivos**:
```
scripts/
  collect-arxiv.ts
  collect-bdtd.ts
  collect-scielo.ts
src/processors/
  paper-processor.ts
  thesis-processor.ts
```

### Module: Innovation

**Fontes**: Clinical Trials, Patents

**Responsabilidades**:
- Coleta de ensaios clínicos
- Coleta de patentes
- Linking entre research → patent
- Trend detection em inovação

**Arquivos**:
```
scripts/
  collect-clinical-trials.ts
  collect-patents.ts
src/analyzers/
  innovation-analyzer.ts
```

### Module: Tech

**Fontes**: GitHub, Packages, StackOverflow

**Responsabilidades**:
- Tracking de repositórios trending
- Downloads de pacotes
- Tech problems detection (SO)
- Language/framework trends

**Arquivos**:
```
scripts/
  collect-github.ts
  collect-packages.ts
  collect-stackoverflow.ts
src/analyzers/
  tech-trends-analyzer.ts
```

### Module: Finance

**Fontes**: B3, NASDAQ, Funding Rounds

**Responsabilidades**:
- Coleta de ações/stocks
- Coleta de funding rounds
- Geração de sinais de investimento
- Correlação research → funding

**Arquivos**:
```
finance/
  scripts/
    collect-brazil-stocks.ts
    collect-nasdaq-momentum.ts
    collect-funding-rounds.ts
    generate-signals.ts
```

**Documentação**: Ver [finance/README.md](finance/README.md)

---

## 🗄️ Database Design

### Design Principles

1. **Normalization**: 3NF para evitar redundância
2. **Denormalization**: Quando performance > storage
3. **Partitioning**: Por data em tabelas grandes (>10M rows)
4. **Indexing**: Indexes em foreign keys e campos de busca
5. **Constraints**: UNIQUE, NOT NULL, CHECK quando aplicável

### Schema Overview

```sql
-- Academia
arxiv_papers (id, arxiv_id, title, abstract, authors[], categories[], ...)
bdtd_theses (id, bdtd_id, title, author, university, ...)
scielo_articles (id, doi, title, journal, ...)

-- Innovation
clinical_trials (id, trial_id, sponsor, phase, ...)
patents (id, patent_number, assignee, inventors[], ...)

-- Tech
github_repos (id, repo_id, language, stars, ...)
software_packages (id, package_name, registry, downloads, ...)
stackoverflow_questions (id, question_id, tags[], score, ...)

-- Finance
market_data_brazil (id, ticker, price, change_pct, ...)
market_data_nasdaq (id, ticker, price, ...)
funding_rounds (id, company, amount_usd, valuation_usd, ...)
```

### Relationships

```
patents ──< assignee >── funding_rounds (company)
arxiv_papers ──< categories >── patents (classifications)
github_repos ──< language >── stackoverflow_questions (tags)
```

### Indexes Strategy

**Primary Indexes**:
- Todas tabelas: `id` (SERIAL PRIMARY KEY)
- External IDs: `UNIQUE` constraints

**Secondary Indexes**:
```sql
-- Busca por data
CREATE INDEX idx_arxiv_published ON arxiv_papers(published_date DESC);
CREATE INDEX idx_funding_announced ON funding_rounds(announced_date DESC);

-- Busca por empresa/company
CREATE INDEX idx_patents_assignee ON patents(assignee);
CREATE INDEX idx_funding_company ON funding_rounds(company);

-- Full-text search
CREATE INDEX idx_papers_fulltext ON arxiv_papers
  USING gin(to_tsvector('english', title || ' ' || abstract));
```

### Partitioning (Future)

Para tabelas grandes:

```sql
-- Particionar arxiv_papers por ano
CREATE TABLE arxiv_papers_2024 PARTITION OF arxiv_papers
  FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE arxiv_papers_2025 PARTITION OF arxiv_papers
  FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

---

## 🔒 Segurança

### Database Security

1. **Authentication**:
   - Usuário específico `sofia` com permissões limitadas
   - Senha forte (min 16 chars)
   - Rotação de senha a cada 90 dias

2. **Network**:
   - PostgreSQL não exposto publicamente
   - Acesso apenas via Docker network
   - Whitelist de IPs se necessário

3. **Encryption**:
   - SSL/TLS para conexões
   - Backups encriptados (gpg)
   - Dados sensíveis hasheados

### API Security (Future)

1. **Authentication**: JWT tokens
2. **Authorization**: Role-based access control (RBAC)
3. **Rate Limiting**: Por IP e por usuário
4. **Input Validation**: Sanitização de todos inputs
5. **CORS**: Whitelist de domínios

### Secrets Management

```bash
# Usar .env para secrets
# NUNCA commitar .env no git
.env        # Local secrets
.env.example # Template sem secrets
```

---

## 📈 Escalabilidade

### Horizontal Scaling

**Collectors**: Paralelizáveis
```bash
# Rodar múltiplas instâncias
docker-compose scale collector=5
```

**Database**: Read replicas
```yaml
# docker-compose.yml
postgres-primary:
  image: postgres:15
postgres-replica-1:
  image: postgres:15
  environment:
    POSTGRES_MASTER_SERVICE_HOST: postgres-primary
```

### Vertical Scaling

**Database tuning**:
```sql
-- postgresql.conf
shared_buffers = 4GB
work_mem = 256MB
maintenance_work_mem = 1GB
effective_cache_size = 12GB
max_connections = 200
```

### Caching Strategy

**Redis** para:
- API responses (TTL 5-60min)
- Trending queries results
- Rate limiting counters

```typescript
// Exemplo
const cached = await redis.get(`signals:${date}`);
if (cached) return JSON.parse(cached);

const signals = await generateSignals();
await redis.setex(`signals:${date}`, 3600, JSON.stringify(signals));
return signals;
```

### Queue System (Future)

**Bull/BullMQ** para:
- Processamento assíncrono
- Retry de jobs falhados
- Priorização de tarefas

```typescript
// Exemplo
const queue = new Queue('data-collection');

queue.add('collect-arxiv', { since: '2024-01-01' }, {
  priority: 1,
  attempts: 3,
  backoff: { type: 'exponential', delay: 2000 }
});
```

---

## 📊 Monitoramento

### Metrics

**Prometheus** para coletar:
- Request rate
- Error rate
- Response time
- Database connections
- Queue size

**Grafana** para visualizar:
- Dashboards customizados
- Alertas via Slack/Email
- SLA monitoring

### Logging

**Structured Logging**:
```typescript
logger.info('Collection completed', {
  source: 'arxiv',
  count: 150,
  duration: 45,
  timestamp: new Date()
});
```

**Centralização**:
- Logs salvos em `/var/log/sofia-*.log`
- Rotação diária (logrotate)
- Retenção: 30 dias

### Alerting

**Alertas críticos**:
- Database down
- Coleta falhando por >24h
- Disk usage >80%
- Memory usage >90%

**Canais**:
- Telegram/Discord webhooks
- Email
- PagerDuty (produção)

---

## 🧠 Decisões de Design

### Por que PostgreSQL?

✅ **Prós**:
- ACID compliant
- Excelente para queries complexas (JOINs)
- pgvector para embeddings (future ML)
- Maturidade e comunidade

❌ **Contras considerados**:
- NoSQL seria mais rápido para writes
- Mas sacrificaria consistência

**Decisão**: Consistência > Performance raw

### Por que TypeScript?

✅ **Prós**:
- Type safety (menos bugs)
- Melhor DX (autocomplete, refactoring)
- Ecosistema npm rico

**Alternativas consideradas**:
- Python: Boa para ML, mas TypeScript better para infra
- Go: Performance, mas menos libs científicas

### Por que Cron vs Event-driven?

**Cron escolhido porque**:
- Maioria das fontes não tem webhooks
- Polling é necessário de qualquer forma
- Simplicidade operacional

**Future**: Hybrid (Cron + Webhooks quando disponível)

### Por que Monorepo?

✅ **Prós**:
- Compartilhamento de código (types, utils)
- Versionamento sincronizado
- CI/CD simplificado

❌ **Contras**:
- Pode crescer muito
- Build times maiores

**Mitigação**: Module boundaries bem definidos

---

## 🔮 Evolução Futura

### Fase 1: MVP (Atual)
- ✅ Coleta multi-fonte
- ✅ Armazenamento PostgreSQL
- ✅ Backup automatizado
- ✅ Finance module completo

### Fase 2: Intelligence (Q1 2025)
- [ ] API REST pública
- [ ] Dashboard Grafana completo
- [ ] Alertas automatizados
- [ ] Machine Learning básico

### Fase 3: Scale (Q2 2025)
- [ ] Kubernetes deployment
- [ ] Redis caching
- [ ] Queue system (Bull)
- [ ] Multi-region

### Fase 4: Platform (Q3-Q4 2025)
- [ ] Multi-tenancy
- [ ] Marketplace de sinais
- [ ] Mobile app
- [ ] Real-time streaming

---

## 📚 Referências

- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Node.js Production Best Practices](https://github.com/goldbergyoni/nodebestpractices)
- [Twelve-Factor App](https://12factor.net/)
- [Microservices Patterns](https://microservices.io/patterns/)

---

<p align="center">
  <strong>Arquitetura construída para escalar de MVP a plataforma enterprise</strong>
</p>
