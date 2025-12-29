# 🎯 TODO: Tech Intelligence v3.0 - Sofia Pulse

**Objetivo**: Transformar Sofia Pulse em **Bloomberg Terminal da Tech Intelligence** para colunistas.

**Baseado em**: Sugestões do Gemini + Lista de APIs gratuitas do GPT

---

## 📊 VISÃO GERAL

### O que vamos construir:

1. **Prever tendências de carreira** (linguagens, frameworks, skills)
2. **Prever setores com funding** (antes dos VCs)
3. **Detectar sinais fracos** (tecnologias emergentes)
4. **Mapear geopolítica → tech** (GDELT + funding)
5. **Recomendar localização de filiais** (papers + vagas + funding)
6. **Gerar playbooks** (carreira, investimento)
7. **Detectar dark horses** (patentes ↑ mas funding ↓)

---

## 🚀 FASE 1: APIs SEM CADASTRO (1-2 dias)

**Status**: 🔴 NÃO INICIADO → 🟡 EM PROGRESSO → 🟢 CONCLUÍDO

### 1.1. GitHub Public API 🟡 EM PROGRESSO

**Collector**: `scripts/collect-github-trending.ts`
**Tabela**: `github_trending`
**Frequência**: Diário, 08:00 UTC
**API**: https://api.github.com

**Dados coletados**:
- Repos trending (diário, semanal, mensal)
- Stars, forks, contributors
- Linguagens por popularidade
- Topics (AI, blockchain, web3, etc)
- Commits recentes (atividade)

**Schema**:
```sql
CREATE TABLE github_trending (
  id SERIAL PRIMARY KEY,
  repo_id BIGINT UNIQUE,
  full_name VARCHAR(255),
  description TEXT,
  language VARCHAR(50),
  stars INT,
  forks INT,
  stars_today INT,
  stars_week INT,
  stars_month INT,
  topics TEXT[],
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

**Caso de uso**:
- "Rust cresceu 300% em stars nos últimos 30 dias"
- "WebAssembly subiu de #15 para #5 em trending"

---

### 1.2. Hacker News API 🔴 NÃO INICIADO

**Collector**: `scripts/collect-hackernews.ts`
**Tabela**: `hackernews_stories`
**Frequência**: Diário, 09:00 UTC
**API**: https://hn.algolia.com/api/v1/search?tags=front_page

**Dados coletados**:
- Top stories (front page)
- Points, comments
- Keywords extraídos de títulos
- URLs de referência

**Schema**:
```sql
CREATE TABLE hackernews_stories (
  id SERIAL PRIMARY KEY,
  story_id BIGINT UNIQUE,
  title TEXT,
  url TEXT,
  points INT,
  num_comments INT,
  author VARCHAR(100),
  created_at TIMESTAMP,
  keywords TEXT[],
  collected_at TIMESTAMP DEFAULT NOW()
);
```

**Caso de uso**:
- "50 posts sobre 'Rust' nos últimos 7 dias (↑200%)"
- "DeepSeek dominando HN por 3 dias seguidos"

---

### 1.3. Reddit JSON API 🔴 NÃO INICIADO

**Collector**: `scripts/collect-reddit-tech.ts`
**Tabela**: `reddit_tech_posts`
**Frequência**: Diário, 10:00 UTC
**API**: https://www.reddit.com/r/{subreddit}.json

**Subreddits monitorados**:
- r/programming
- r/MachineLearning
- r/startups
- r/learnprogramming
- r/webdev
- r/rust
- r/javascript

**Schema**:
```sql
CREATE TABLE reddit_tech_posts (
  id SERIAL PRIMARY KEY,
  post_id VARCHAR(50) UNIQUE,
  subreddit VARCHAR(50),
  title TEXT,
  url TEXT,
  score INT,
  num_comments INT,
  author VARCHAR(100),
  created_utc TIMESTAMP,
  keywords TEXT[],
  collected_at TIMESTAMP DEFAULT NOW()
);
```

**Caso de uso**:
- "r/rust teve 3x mais posts esta semana"
- "Sentimento negativo sobre React cresceu 40%"

---

### 1.4. GDELT 2.0 (Global Events) 🔴 NÃO INICIADO

**Collector**: `scripts/collect-gdelt-events.ts`
**Tabela**: `gdelt_events`
**Frequência**: Diário, 11:00 UTC
**API**: http://data.gdeltproject.org/gdeltv2/lastupdate.txt

**Dados coletados**:
- Eventos geopolíticos por país
- Conflitos, protestos, acordos
- Menções de tech (AI regulation, crypto bans, etc)

**Schema**:
```sql
CREATE TABLE gdelt_events (
  id SERIAL PRIMARY KEY,
  event_id VARCHAR(50) UNIQUE,
  event_date DATE,
  country1 VARCHAR(100),
  country2 VARCHAR(100),
  event_type VARCHAR(100),
  goldstein_scale DECIMAL(5,2),
  num_mentions INT,
  avg_tone DECIMAL(5,2),
  source_url TEXT,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

**Caso de uso**:
- "Tensão US-China subiu 30% → Menos funding em startups chinesas"
- "AI regulation na UE → Migração de startups para UK"

---

### 1.5. GitHub Archive (Commits Históricos) 🔴 NÃO INICIADO

**Collector**: `scripts/collect-github-archive.ts`
**Tabela**: `github_commits_stats`
**Frequência**: Semanal (Segunda, 12:00 UTC)
**API**: https://www.gharchive.org

**Dados coletados**:
- Commits por linguagem (histórico)
- Atividade de desenvolvedores
- Crescimento/queda de frameworks

**Schema**:
```sql
CREATE TABLE github_commits_stats (
  id SERIAL PRIMARY KEY,
  week DATE,
  language VARCHAR(50),
  commit_count BIGINT,
  repo_count INT,
  developer_count INT,
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(week, language)
);
```

**Caso de uso**:
- "Rust commits cresceram 250% em 6 meses"
- "PHP commits caíram 40% (está morrendo)"

---

### 1.6. NPM Registry API 🔴 NÃO INICIADO

**Collector**: `scripts/collect-npm-stats.ts`
**Tabela**: `npm_packages_stats`
**Frequência**: Semanal (Segunda, 13:00 UTC)
**API**: https://api.npmjs.org/downloads/point/last-week/{package}

**Pacotes monitorados**:
- Frameworks: react, vue, angular, svelte, solid-js
- Build tools: webpack, vite, rollup, esbuild
- Testing: jest, vitest, cypress, playwright
- AI/ML: tensorflow.js, brain.js, ml5.js

**Schema**:
```sql
CREATE TABLE npm_packages_stats (
  id SERIAL PRIMARY KEY,
  package_name VARCHAR(255),
  week_start DATE,
  downloads_week BIGINT,
  downloads_change_pct DECIMAL(5,2),
  version VARCHAR(50),
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(package_name, week_start)
);
```

**Caso de uso**:
- "Vite ultrapassou Webpack em downloads (↑350%)"
- "Solid.js cresceu 500% em 3 meses (framework emergente)"

---

### 1.7. PyPI Stats API 🔴 NÃO INICIADO

**Collector**: `scripts/collect-pypi-stats.ts`
**Tabela**: `pypi_packages_stats`
**Frequência**: Semanal (Segunda, 14:00 UTC)
**API**: https://pypistats.org/api/packages/{package}/recent

**Pacotes monitorados**:
- AI/ML: pytorch, tensorflow, transformers, langchain, openai
- Data: pandas, numpy, polars, duckdb
- Web: fastapi, flask, django

**Schema**:
```sql
CREATE TABLE pypi_packages_stats (
  id SERIAL PRIMARY KEY,
  package_name VARCHAR(255),
  week_start DATE,
  downloads_week BIGINT,
  downloads_change_pct DECIMAL(5,2),
  version VARCHAR(50),
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(package_name, week_start)
);
```

**Caso de uso**:
- "LangChain downloads explodiram (10x em 2 meses)"
- "Polars está ultrapassando Pandas (↑800%)"

---

## 🔑 FASE 2: APIs COM CADASTRO (3-5 dias)

### 2.1. Crunchbase API 🔴 NÃO INICIADO

**Collector**: `scripts/collect-crunchbase-deals.ts`
**Tabela**: `crunchbase_funding`
**API**: https://data.crunchbase.com/docs

**Dados**:
- Early-stage funding (seed, pre-seed)
- Setores emergentes
- Geo de startups

---

### 2.2. AngelList API 🔴 NÃO INICIADO

**Collector**: `scripts/collect-angellist-deals.ts`
**Tabela**: `angellist_deals`

**Dados**:
- Angel rounds
- Aceleradoras
- Investidores anjo

---

### 2.3. WIPO Global API 🔴 NÃO INICIADO

**Collector**: `scripts/collect-wipo-global.ts`
**Tabela**: `wipo_global_patents`

**Dados**:
- Patentes globais (não só China)
- Patentes por tech (AI, biotech, green tech)

---

### 2.4. JPO (Japão) & KIPO (Korea) Patents 🔴 NÃO INICIADO

**Collector**: `scripts/collect-jpo-kipo-patents.ts`
**Tabelas**: `jpo_patents`, `kipo_patents`

**Dados**:
- Patentes Japão (robotics, hardware)
- Patentes Korea (semiconductors, displays)

---

### 2.5. FRED API (Federal Reserve) 🔴 NÃO INICIADO

**Collector**: `scripts/collect-fred-indicators.ts`
**Tabela**: `fred_indicators`

**Dados**:
- Juros (FED rate)
- Inflação (CPI)
- Liquidez (M2 money supply)
- Yield curve

**Caso de uso**:
- "Juros baixos → Mais funding em tech"
- "Yield curve invertida → Recessão → Menos IPOs"

---

### 2.6. World Bank Data API 🔴 NÃO INICIADO

**Collector**: `scripts/collect-worldbank-macro.ts`
**Tabela**: `worldbank_indicators`

**Dados**:
- PIB por país
- Inflação
- Desemprego
- Trade balance

---

## 📊 FASE 3: ANALYTICS & CORRELAÇÕES (1 semana)

### 3.1. Correlação Academia → Mercado 🔴 NÃO INICIADO

**Script**: `analytics/correlate-papers-funding.py`

**Análise**:
```python
# Papers sobre "AI safety" → Funding em "AI safety startups"
# Lag: 6-12 meses
```

---

### 3.2. Tech Trend Score 🔴 NÃO INICIADO

**Script**: `analytics/calculate-tech-trend-score.py`

**Formula**:
```
Trend Score =
  (GitHub stars growth * 0.3) +
  (NPM/PyPI downloads growth * 0.25) +
  (HN mentions * 0.15) +
  (Reddit posts * 0.1) +
  (Papers count * 0.1) +
  (Job postings * 0.1)
```

**Output**: `tech_trend_scores` table

---

### 3.3. Career Playbooks (NLG) 🔴 NÃO INICIADO

**Script**: `analytics/generate-career-playbooks.py`

**Input**: Tech trend scores + Job postings
**Output**: Markdown files

**Exemplo**:
```markdown
# Playbook: Backend Developer 2025

## Linguagens em alta:
- Rust (↑300%) - sistemas de alto desempenho
- Go (↑150%) - microservices
- TypeScript (↑100%) - full-stack

## Skills demandadas:
- Kubernetes (↑200%)
- GraphQL (↑150%)
- WASM (↑500% - emergente!)

## Onde há vagas:
- Brasil: São Paulo, Florianópolis
- USA: San Francisco, Austin, NYC
- Europa: Berlin, Amsterdam, London

## Salário médio:
- Júnior: $60k-$80k
- Pleno: $100k-$140k
- Sênior: $160k-$220k
```

---

### 3.4. Investment Playbooks 🔴 NÃO INICIADO

**Script**: `analytics/generate-investment-playbooks.py`

**Input**: Funding + Patents + Papers + GDELT
**Output**: Markdown files

**Exemplo**:
```markdown
# Playbook: Where to Invest in AI (Q1 2025)

## Setores em alta:
1. AI Safety (papers ↑500%, funding ↑200%)
2. AI Infrastructure (NVIDIA ecosystem)
3. AI Agents (LangChain, AutoGPT derivatives)

## Geo hotspots:
1. San Francisco (epicentro, mas caro)
2. Austin (emergente, ↑300% funding)
3. Singapore (Ásia, bridge China-USA)

## Early signals (dark horses):
- AI + Hardware (edge computing)
- AI + Biotech (protein folding)
- AI + Green Tech (energy optimization)

## Geopolítica:
- ⚠️ US-China tension → Evitar dual-use AI
- ✅ EU AI Act → Compliance startups ↑
```

---

### 3.5. Dark Horse Detection 🔴 NÃO INICIADO

**Script**: `analytics/detect-dark-horses.py`

**Lógica**:
```python
# Dark Horse = Alta atividade acadêmica MAS baixo funding

SELECT
  p.concept,
  COUNT(p.id) as papers_count,
  COALESCE(SUM(f.amount_usd), 0) as total_funding
FROM openalex_papers p
LEFT JOIN funding_rounds f ON p.concept = f.sector
WHERE p.published_date > NOW() - INTERVAL '6 months'
GROUP BY p.concept
HAVING COUNT(p.id) > 50 AND total_funding < 10000000
ORDER BY papers_count DESC;
```

**Output**: `dark_horse_techs` table

---

### 3.6. Entity Resolution (Papers → GitHub → Spin-offs) 🔴 NÃO INICIADO

**Script**: `analytics/entity-resolution.py`

**Stack**:
- Fuzzy name matching (fuzzywuzzy)
- RecordLinkage (dedupe)

**Objetivo**:
- Rastrear autor de paper → GitHub → Fundou startup

---

### 3.7. Confidence Score (TRL-based) 🔴 NÃO INICIADO

**Script**: `analytics/calculate-confidence-score.py`

**Formula**:
```
Confidence =
  (Papers count * TRL_weight_low) +
  (Angel funding * TRL_weight_med) +
  (VC funding * TRL_weight_high) +
  (Patents count * TRL_weight_high)

TRL weights:
- Low TRL (papers): 0.2
- Medium TRL (angel, aceleradoras): 0.5
- High TRL (VC, patents): 0.8
```

---

## 🗓️ CRONOGRAMA

### Semana 1 (Fase 1 - APIs sem cadastro)
- Dia 1: GitHub Trending ✅
- Dia 2: HackerNews + Reddit
- Dia 3: GDELT
- Dia 4: GitHub Archive + NPM
- Dia 5: PyPI

### Semana 2 (Fase 2 - APIs com cadastro)
- Dia 1: Cadastros (Crunchbase, AngelList, WIPO, FRED)
- Dia 2-3: Crunchbase + AngelList
- Dia 4: WIPO Global + JPO/KIPO
- Dia 5: FRED + World Bank

### Semana 3 (Fase 3 - Analytics)
- Dia 1-2: Correlações básicas
- Dia 3-4: Tech Trend Score + Playbooks
- Dia 5: Dark Horse Detection

### Semana 4 (Refinamento)
- Dia 1-2: Entity Resolution
- Dia 3: Confidence Score
- Dia 4-5: Testes, ajustes, documentação

---

## 📋 CHECKLIST GERAL

### Infraestrutura
- [ ] Criar migrations para novas tabelas
- [ ] Adicionar npm scripts ao package.json
- [ ] Adicionar ao cron
- [ ] Criar logs separados

### Collectors (Fase 1)
- [ ] GitHub Trending
- [ ] HackerNews
- [ ] Reddit Tech
- [ ] GDELT
- [ ] GitHub Archive
- [ ] NPM Stats
- [ ] PyPI Stats

### Collectors (Fase 2)
- [ ] Crunchbase
- [ ] AngelList
- [ ] WIPO Global
- [ ] JPO/KIPO Patents
- [ ] FRED Indicators
- [ ] World Bank Macro

### Analytics
- [ ] Correlação Papers → Funding
- [ ] Tech Trend Score
- [ ] Career Playbooks
- [ ] Investment Playbooks
- [ ] Dark Horse Detection
- [ ] Entity Resolution
- [ ] Confidence Score (TRL)

### Insights v3.0
- [ ] Integrar novos dados ao script de insights
- [ ] Email com playbooks
- [ ] Dashboard Grafana atualizado

---

## 🎯 CASOS DE USO FINAIS

### Para Colunistas (TI Especialistas):
1. "Rust está crescendo 300% - escreva sobre isso AGORA"
2. "LangChain vs LlamaIndex - quem vai ganhar?"
3. "5 dark horses para 2025: AI + Hardware, AI + Biotech..."

### Para Desenvolvedores:
1. "Aprenda Rust se você quer $200k/ano"
2. "React ainda domina mas Solid.js é o futuro (↑500%)"
3. "Top 10 skills para 2025"

### Para Investidores:
1. "Onde investir em AI: Austin > SF em custo-benefício"
2. "Dark horses: Edge AI, Protein Folding, Energy Optimization"
3. "Geopolítica: Evite dual-use AI (tensão US-China)"

### Para Empresas:
1. "Onde abrir filial: Berlin (papers ↑ + funding ↑ + custo ↓)"
2. "Recrutar devs Rust: MIT, Stanford, UFRGS"
3. "Seu framework está morrendo: AngularJS ↓40%"

---

**Última Atualização**: 2025-11-19
**Status**: 🟡 FASE 1 EM PROGRESSO
**Branch**: `claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE`
