# 📡 Collectors System - Sofia Pulse

## 🎯 Overview

**PROBLEMA RESOLVIDO**: Tínhamos 88 collectors separados com código duplicado (99% igual).

**SOLUÇÃO**: Sistema modular com collectors especializados por tipo de dado.

## 🏗️ Nova Arquitetura (Opção C - Híbrida)

```
scripts/
├── collectors/                          # Collectors engines por tipo
│   ├── tech-trends-collector.ts         # ✅ GitHub, NPM, PyPI, HN
│   ├── research-papers-collector.ts     # ⏳ ArXiv, OpenAlex, NIH
│   ├── jobs-collector.ts                # ⏳ LinkedIn, RemoteOK
│   └── funding-collector.ts             # ⏳ Crunchbase, YC
│
├── configs/                             # Configurações por tipo
│   ├── tech-trends-config.ts            # ✅ Configs de tech trends
│   ├── research-papers-config.ts        # ⏳ Configs de papers
│   ├── jobs-config.ts                   # ⏳ Configs de vagas
│   └── funding-config.ts                # ⏳ Configs de funding
│
├── shared/                              # Lógica compartilhada (funções)
│   ├── trends-inserter.ts               # ✅ Insere em tech_trends
│   ├── papers-inserter.ts               # ⏳ Insere em arxiv_ai_papers, etc
│   ├── jobs-inserter.ts                 # ⏳ Insere em jobs
│   ├── funding-inserter.ts              # ⏳ Insere em funding_rounds
│   └── collector-utils.ts               # ⏳ Rate limiter, tracking, logging
│
├── collect.ts                           # Entry point único
├── generate-crontab.ts                  # Gera crontab de TODOS collectors
└── collector-status.ts                  # Status de TODOS collectors
```

## 💡 Princípio Arquitetural

**"Trate os iguais como iguais e os diferentes como diferentes"**

- **Tech Trends** (GitHub, NPM, PyPI) → `tech_trends` table (schema simples)
- **Research Papers** (ArXiv, OpenAlex) → `arxiv_ai_papers`, `openalex_papers` (schema rico)
- **Jobs** (LinkedIn, RemoteOK) → `jobs` table (schema de vagas)
- **Funding** (Crunchbase, YC) → `funding_rounds` table (schema de investimento)

Cada tipo tem:
- ✅ Collector engine específico
- ✅ Configs específicas
- ✅ Inserter específico
- ✅ Schema otimizado

Todos compartilham:
- ✅ Rate limiting (`collector-utils.ts`)
- ✅ Error handling (`collector-utils.ts`)
- ✅ Tracking via `collector_runs` table
- ✅ Cron generation via `generate-crontab.ts`
- ✅ Status dashboard via `collector-status.ts`

## 📦 Benefícios

✅ **Zero duplicação**: Código de fetch/parse/track centralizado
✅ **Nomenclatura clara**: tech-trends, research-papers, jobs, funding
✅ **Sem OOP desnecessário**: Funções puras compartilhadas
✅ **Schemas otimizados**: Cada tipo usa table ideal
✅ **Rastreamento total**: `collector_runs` para TODOS
✅ **Cron unificado**: 1 crontab para os 88 collectors

## 🚀 Usage

### Rodar 1 collector

```bash
npx tsx scripts/collect.ts github
npx tsx scripts/collect.ts npm
npx tsx scripts/collect.ts hackernews
```

### Rodar todos

```bash
npx tsx scripts/collect.ts --all
```

### Ver collectors disponíveis

```bash
npx tsx scripts/collect.ts --help
```

## 📅 Crontab Management

### Gerar crontab (preview)

```bash
npx tsx scripts/generate-crontab.ts
```

### Instalar crontab

```bash
npx tsx scripts/generate-crontab.ts --install
```

### Ver estatísticas

```bash
npx tsx scripts/generate-crontab.ts --stats
```

**IMPORTANTE**: Nunca edite o crontab manualmente! Sempre use `generate-crontab.ts --install`.

## 📊 Collector Status Dashboard

### Ver status geral

```bash
npx tsx scripts/collector-status.ts
```

### Ver estatísticas

```bash
npx tsx scripts/collector-status.ts --stats
```

### Health check

```bash
npx tsx scripts/collector-status.ts --health
```

### Falhas recentes

```bash
npx tsx scripts/collector-status.ts --failures
```

### Histórico de um collector

```bash
npx tsx scripts/collector-status.ts --history github
```

## 🔧 Como Adicionar Novos Collectors

### Tech Trends Collector

#### 1. Adicionar config em `configs/tech-trends-config.ts`

```typescript
export const meuCollector: CollectorConfig = {
  name: 'meucollector',
  displayName: '🎯 Meu Collector',
  description: 'Coleta dados de X',

  url: 'https://api.example.com/data',

  headers: (env) => ({
    'Authorization': `Bearer ${env.MY_API_KEY}`,
  }),

  parseResponse: (data) => {
    return data.items.map(item => ({
      source: 'meucollector',
      name: item.name,
      score: item.score,
      metadata: { /* dados extras */ }
    }));
  },

  schedule: '0 8 * * *', // 1x/dia às 8h
  rateLimit: 1000, // 1 req/segundo
};
```

### 2. Adicionar ao registry

```typescript
export const collectors: Record<string, CollectorConfig> = {
  // ... existing
  meucollector: meuCollector,
};
```

### 3. Testar

```bash
npx tsx scripts/collect.ts meucollector
```

#### 4. Atualizar crontab

```bash
npx tsx scripts/generate-crontab.ts --install
```

**Pronto!** Seu collector está funcionando.

---

### Jobs Collector

#### 1. Adicionar config em `configs/jobs-config.ts`

```typescript
export const meuJobsCollector: JobsCollectorConfig = {
  name: 'meujobscollector',
  displayName: '💼 Meu Jobs Collector',
  description: 'Coleta vagas de X',

  url: 'https://api.example.com/jobs',

  headers: (env) => ({
    'Authorization': `Bearer ${env.MY_JOBS_API_KEY}`,
  }),

  parseResponse: (data) => {
    return data.jobs.map(job => ({
      job_id: job.id,
      platform: 'meujobscollector',
      title: job.title,
      company: job.company,
      location: job.location,
      remote_type: job.is_remote ? 'remote' : 'onsite',
      description: job.description,
      url: job.url,
      posted_date: job.created_at,
      salary_min: job.salary_min,
      salary_max: job.salary_max,
      salary_currency: 'USD',
      salary_period: 'yearly',
      employment_type: 'full-time',
      skills_required: job.skills || [],
    }));
  },

  schedule: '0 */6 * * *', // 4x/dia (vagas mudam rápido)
  rateLimit: 1000, // 1 req/segundo
};
```

#### 2. Adicionar ao registry

```typescript
export const jobsCollectors: Record<string, JobsCollectorConfig> = {
  // ... existing
  meujobscollector: meuJobsCollector,
};
```

#### 3. Testar

```bash
npx tsx scripts/collect.ts meujobscollector
```

#### 4. Atualizar crontab

```bash
npx tsx scripts/generate-crontab.ts --install
```

**Pronto!** Seu jobs collector está funcionando.

## 📊 Schedules Recomendados

| Frequência | Cron | Uso |
|------------|------|-----|
| 2x/dia | `0 */12 * * *` | GitHub, HackerNews (dados mudam rápido) |
| 1x/dia | `0 8 * * *` | NPM, PyPI, APIs de stats |
| 1x/semana | `0 8 * * 1` | ArXiv (papers só aos domingos) |
| 1x/mês | `0 8 1 * *` | WHO, UNICEF (dados lentos) |

## 🔍 Debugging

### Ver logs de um collector

```bash
tail -f logs/github-collector.log
```

### Rodar em modo verbose

```bash
DEBUG=* npx tsx scripts/collect.ts github
```

### Testar sem salvar no banco

Edite a config e comente o `await inserter.insert()`.

## 🎨 Status da Migração

### ✅ Fase 1: Tech Trends (COMPLETO)

**Arquitetura:**
- ✅ `collectors/tech-trends-collector.ts` - Core engine
- ✅ `configs/tech-trends-config.ts` - Configurações
- ✅ `shared/trends-inserter.ts` - Inserção unificada

**Collectors migrados:**
- ✅ **GitHub Trending** - 2x/dia (0h, 12h)
- ✅ **NPM Stats** - 1x/dia (8h)
- ✅ **PyPI Stats** - 1x/dia (20h)
- ✅ **HackerNews** - 2x/dia (0h, 12h)

**Total**: 4/88 collectors migrados (5%)

### ✅ Fase 2: Research Papers (COMPLETO - 100%)

**Arquitetura:**
- ✅ `collectors/research-papers-collector.ts` - Core engine para papers
- ✅ `configs/research-papers-config.ts` - Configurações
- ✅ `shared/papers-inserter.ts` - Inserção unificada (Fase 2.1)

**Collectors migrados:**
- ✅ **ArXiv AI Papers** - 1x/semana (segunda 8h) - 1000 papers - `arxiv_ai_papers` table
- ✅ **OpenAlex Papers** - 1x/semana (segunda 8h) - 1000 papers - `openalex_papers` table
- ⏳ **NIH Grants** - Aguardando API config - estrutura pronta

**Total**: 6/88 collectors migrados (7% - 4 tech + 2 papers)

**Features Fase 2.1:**
- ✅ Inserção real em `arxiv_ai_papers` (11 campos)
- ✅ Inserção real em `openalex_papers` (16 campos)
- ✅ Batch insert com transações
- ✅ Auto-detecção de tipo de paper
- ✅ ON CONFLICT para updates automáticos

### ✅ Fase 3: Jobs (COMPLETO - 100%)

**Arquitetura:**
- ✅ `collectors/jobs-collector.ts` - Core engine para jobs
- ✅ `configs/jobs-config.ts` - Configurações
- ✅ `shared/jobs-inserter.ts` - Inserção unificada

**Collectors migrados:**
- ✅ **Himalayas** - 4x/dia (0h, 6h, 12h, 18h) - Remote jobs com salário - `sofia.jobs` table
- ✅ **RemoteOK** - 4x/dia (0h, 6h, 12h, 18h) - Remote jobs worldwide - `sofia.jobs` table
- ✅ **Arbeitnow** - 2x/dia (0h, 12h) - Europe tech jobs - `sofia.jobs` table
- ⏳ **GitHub Jobs** - Aguardando GITHUB_TOKEN - estrutura pronta

**Total**: 9/88 collectors migrados (10% - 4 tech + 2 papers + 3 jobs)

**Features Fase 3:**
- ✅ Inserção real em `sofia.jobs` (20 campos)
- ✅ Normalização de localização (city, country, remote_type)
- ✅ Normalização de salário (USD, EUR, BRL + conversão)
- ✅ Extração de skills de descrição
- ✅ Batch insert com transações
- ✅ ON CONFLICT para updates automáticos (preserva salários)
- ✅ Statistics por plataforma

### ⏳ Fase 4: Funding (FUTURO)

**Collectors:**
- Crunchbase, YC, AngelList, etc.
- Usam `funding_rounds` table

## 📝 Notas Técnicas

### Rate Limiting

O sistema usa `rateLimiters` do `rate-limiter.ts`:

- `github`: Exponential backoff, respeita X-RateLimit headers
- `reddit`: 60 req/minuto
- Número: Delay fixo em ms

### Error Handling

- HTTP errors são caught e logados
- Inserção no banco é por item (1 falha não para tudo)
- Retry automático para rate limits (via rate-limiter)

### Tracking

TODOS os collectors (independente do tipo) são rastreados via `collector_runs` table:
- Quando rodou
- Duração
- Sucesso/falha
- Items coletados
- Erros

### Performance

- Collectors rodam **sequencialmente** quando usa `--all`
- Para rodar em paralelo: use múltiplos cron jobs
- Batch insert quando possível

## 🔮 Roadmap

1. ✅ **Fase 1**: Tech Trends (4 collectors) - COMPLETO
2. ✅ **Fase 2**: Research Papers (2 collectors) - COMPLETO
3. ✅ **Fase 3**: Jobs (3 collectors) - COMPLETO
4. ⏳ **Fase 4**: Funding (5+ collectors)
5. ⏳ **Fase 5**: Specialized (70+ collectors)

**Meta**: 88/88 collectors organizados por tipo.

**Progresso Atual**: 9/88 collectors migrados (10%)
