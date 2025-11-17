# 🗄️ Sofia Pulse - Database Schema

Documentação completa do schema do banco de dados PostgreSQL (`sofia_db`).

---

## 📋 Visão Geral

**Database**: `sofia_db`
**SGBD**: PostgreSQL 15+
**Extensions**: pgvector, pg_trgm
**Total de Tabelas**: 11

### Módulos

```
sofia_db/
├── Academia (3 tabelas)
├── Inovação (2 tabelas)
├── Tech (3 tabelas)
└── Finance (3 tabelas)
```

---

## 📚 Módulo: Academia

### arxiv_papers

Papers científicos do ArXiv.

```sql
CREATE TABLE arxiv_papers (
  id SERIAL PRIMARY KEY,
  arxiv_id VARCHAR(50) UNIQUE NOT NULL,
  title TEXT NOT NULL,
  abstract TEXT,
  authors TEXT[] NOT NULL,
  categories VARCHAR(100)[] NOT NULL,
  published_date DATE NOT NULL,
  updated_date DATE,
  citation_count INT DEFAULT 0,
  pdf_url TEXT,
  doi VARCHAR(100),
  journal_ref TEXT,
  comments TEXT,
  collected_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_arxiv_published ON arxiv_papers(published_date DESC);
CREATE INDEX idx_arxiv_categories ON arxiv_papers USING GIN(categories);
CREATE INDEX idx_arxiv_authors ON arxiv_papers USING GIN(authors);
CREATE INDEX idx_arxiv_fulltext ON arxiv_papers
  USING gin(to_tsvector('english', title || ' ' || abstract));
```

**Campos principais**:
- `arxiv_id`: ID único do ArXiv (ex: "2401.12345")
- `categories`: Array de categorias (ex: ["cs.AI", "stat.ML"])
- `authors`: Array de autores
- `citation_count`: Número de citações (atualizado periodicamente)

**Queries comuns**:
```sql
-- Papers recentes de IA
SELECT * FROM arxiv_papers
WHERE 'cs.AI' = ANY(categories)
  AND published_date > NOW() - INTERVAL '30 days'
ORDER BY citation_count DESC;

-- Busca full-text
SELECT * FROM arxiv_papers
WHERE to_tsvector('english', title || ' ' || abstract)
  @@ to_tsquery('english', 'machine & learning');
```

---

### bdtd_theses

Teses e dissertações brasileiras (BDTD).

```sql
CREATE TABLE bdtd_theses (
  id SERIAL PRIMARY KEY,
  bdtd_id VARCHAR(100) UNIQUE NOT NULL,
  title TEXT NOT NULL,
  author VARCHAR(255) NOT NULL,
  advisor VARCHAR(255),
  co_advisor VARCHAR(255),
  university VARCHAR(255) NOT NULL,
  program VARCHAR(255),
  degree_type VARCHAR(50) NOT NULL, -- 'mestrado' | 'doutorado'
  area VARCHAR(100),
  keywords TEXT[],
  abstract TEXT,
  defense_date DATE,
  language VARCHAR(10) DEFAULT 'pt',
  pdf_url TEXT,
  collected_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_bdtd_university ON bdtd_theses(university);
CREATE INDEX idx_bdtd_area ON bdtd_theses(area);
CREATE INDEX idx_bdtd_defense_date ON bdtd_theses(defense_date DESC);
CREATE INDEX idx_bdtd_keywords ON bdtd_theses USING GIN(keywords);
```

**Queries comuns**:
```sql
-- Top universidades por produção
SELECT university, COUNT(*) as theses_count
FROM bdtd_theses
WHERE defense_date > '2020-01-01'
GROUP BY university
ORDER BY theses_count DESC
LIMIT 20;

-- Áreas em crescimento
SELECT area,
  COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM defense_date) = 2024) as y2024,
  COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM defense_date) = 2023) as y2023
FROM bdtd_theses
GROUP BY area
HAVING COUNT(*) > 50
ORDER BY (y2024::float / NULLIF(y2023, 0)) DESC;
```

---

### scielo_articles

Artigos científicos do SciELO.

```sql
CREATE TABLE scielo_articles (
  id SERIAL PRIMARY KEY,
  doi VARCHAR(100) UNIQUE NOT NULL,
  title TEXT NOT NULL,
  authors TEXT[] NOT NULL,
  journal VARCHAR(255) NOT NULL,
  volume VARCHAR(20),
  issue VARCHAR(50),
  pages VARCHAR(50),
  year INT NOT NULL,
  abstract TEXT,
  keywords TEXT[],
  language VARCHAR(10) DEFAULT 'pt',
  citations INT DEFAULT 0,
  url TEXT,
  pdf_url TEXT,
  collected_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_scielo_journal ON scielo_articles(journal);
CREATE INDEX idx_scielo_year ON scielo_articles(year DESC);
CREATE INDEX idx_scielo_keywords ON scielo_articles USING GIN(keywords);
```

---

## 🏥 Módulo: Inovação

### clinical_trials

Ensaios clínicos (ClinicalTrials.gov, REBEC).

```sql
CREATE TABLE clinical_trials (
  id SERIAL PRIMARY KEY,
  trial_id VARCHAR(50) UNIQUE NOT NULL,
  registry VARCHAR(50), -- 'clinicaltrials.gov' | 'rebec'
  title TEXT NOT NULL,
  sponsor VARCHAR(255),
  collaborators TEXT[],
  phase VARCHAR(20), -- 'Phase I' | 'Phase II' | 'Phase III' | 'Phase IV'
  status VARCHAR(50), -- 'Recruiting' | 'Active' | 'Completed' | 'Terminated'
  condition TEXT NOT NULL,
  intervention TEXT,
  intervention_type VARCHAR(50), -- 'Drug' | 'Device' | 'Procedure' | etc
  start_date DATE,
  completion_date DATE,
  primary_completion_date DATE,
  enrollment INT,
  country VARCHAR(100),
  locations TEXT[],
  age_group VARCHAR(50),
  gender VARCHAR(20),
  url TEXT,
  last_updated TIMESTAMP,
  collected_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_trials_sponsor ON clinical_trials(sponsor);
CREATE INDEX idx_trials_phase ON clinical_trials(phase);
CREATE INDEX idx_trials_status ON clinical_trials(status);
CREATE INDEX idx_trials_condition ON clinical_trials(condition);
CREATE INDEX idx_trials_country ON clinical_trials(country);
```

**Queries comuns**:
```sql
-- Trials ativos de COVID-19
SELECT * FROM clinical_trials
WHERE condition ILIKE '%covid%'
  AND status IN ('Recruiting', 'Active, not recruiting')
ORDER BY enrollment DESC;

-- Empresas mais ativas em Phase III
SELECT sponsor, COUNT(*) as phase3_count
FROM clinical_trials
WHERE phase = 'Phase III'
  AND start_date > '2023-01-01'
GROUP BY sponsor
ORDER BY phase3_count DESC;
```

---

### patents

Patentes de invenção (USPTO, EPO, INPI).

```sql
CREATE TABLE patents (
  id SERIAL PRIMARY KEY,
  patent_number VARCHAR(50) UNIQUE NOT NULL,
  patent_office VARCHAR(20), -- 'USPTO' | 'EPO' | 'INPI'
  title TEXT NOT NULL,
  abstract TEXT,
  inventors TEXT[] NOT NULL,
  assignee VARCHAR(255), -- Empresa/instituição detentora
  assignee_type VARCHAR(50), -- 'company' | 'university' | 'individual'
  filing_date DATE NOT NULL,
  grant_date DATE,
  publication_date DATE,
  application_number VARCHAR(50),
  classifications VARCHAR(50)[], -- IPC/CPC codes
  citations_count INT DEFAULT 0,
  backward_citations INT DEFAULT 0,
  forward_citations INT DEFAULT 0,
  claims_count INT,
  country VARCHAR(10) NOT NULL,
  status VARCHAR(50), -- 'Granted' | 'Pending' | 'Abandoned'
  pdf_url TEXT,
  collected_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_patents_assignee ON patents(assignee);
CREATE INDEX idx_patents_filing_date ON patents(filing_date DESC);
CREATE INDEX idx_patents_classifications ON patents USING GIN(classifications);
CREATE INDEX idx_patents_inventors ON patents USING GIN(inventors);
CREATE INDEX idx_patents_country ON patents(country);
```

**Queries comuns**:
```sql
-- Top empresas inovadoras (patentes recentes)
SELECT assignee, COUNT(*) as patent_count,
  AVG(forward_citations) as avg_impact
FROM patents
WHERE grant_date > NOW() - INTERVAL '2 years'
  AND assignee_type = 'company'
GROUP BY assignee
HAVING COUNT(*) > 5
ORDER BY patent_count DESC, avg_impact DESC;

-- Áreas tecnológicas em alta
SELECT UNNEST(classifications) as ipc_code, COUNT(*) as count
FROM patents
WHERE filing_date > NOW() - INTERVAL '1 year'
GROUP BY ipc_code
ORDER BY count DESC
LIMIT 20;
```

---

## 💻 Módulo: Tech

### github_repos

Repositórios GitHub trending.

```sql
CREATE TABLE github_repos (
  id SERIAL PRIMARY KEY,
  repo_id BIGINT UNIQUE NOT NULL,
  full_name VARCHAR(255) UNIQUE NOT NULL,
  owner VARCHAR(255),
  description TEXT,
  language VARCHAR(50),
  stars INT DEFAULT 0,
  forks INT DEFAULT 0,
  watchers INT DEFAULT 0,
  open_issues_count INT DEFAULT 0,
  size_kb INT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  pushed_at TIMESTAMP,
  topics TEXT[],
  license VARCHAR(50),
  homepage TEXT,
  is_fork BOOLEAN DEFAULT FALSE,
  is_archived BOOLEAN DEFAULT FALSE,
  collected_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_github_language ON github_repos(language);
CREATE INDEX idx_github_stars ON github_repos(stars DESC);
CREATE INDEX idx_github_topics ON github_repos USING GIN(topics);
CREATE INDEX idx_github_created ON github_repos(created_at DESC);
```

**Queries comuns**:
```sql
-- Trending repos last month
SELECT full_name, language, stars, forks
FROM github_repos
WHERE created_at > NOW() - INTERVAL '30 days'
ORDER BY stars DESC
LIMIT 50;

-- Language popularity
SELECT language,
  COUNT(*) as repos,
  SUM(stars) as total_stars,
  AVG(stars) as avg_stars
FROM github_repos
WHERE language IS NOT NULL
GROUP BY language
ORDER BY total_stars DESC;
```

---

### software_packages

Downloads de pacotes (npm, PyPI, etc).

```sql
CREATE TABLE software_packages (
  id SERIAL PRIMARY KEY,
  package_name VARCHAR(255) NOT NULL,
  registry VARCHAR(20) NOT NULL, -- 'npm' | 'pypi' | 'rubygems' | 'maven'
  version VARCHAR(50),
  description TEXT,
  author VARCHAR(255),
  license VARCHAR(50),
  homepage TEXT,
  repository TEXT,
  keywords TEXT[],
  dependencies JSONB,
  downloads_day BIGINT,
  downloads_week BIGINT,
  downloads_month BIGINT,
  downloads_total BIGINT,
  published_at TIMESTAMP,
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(package_name, registry, collected_at::DATE)
);

-- Indexes
CREATE INDEX idx_packages_registry ON software_packages(registry);
CREATE INDEX idx_packages_downloads_month ON software_packages(downloads_month DESC);
CREATE INDEX idx_packages_keywords ON software_packages USING GIN(keywords);
```

---

### stackoverflow_questions

Perguntas do StackOverflow.

```sql
CREATE TABLE stackoverflow_questions (
  id SERIAL PRIMARY KEY,
  question_id BIGINT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  body TEXT,
  tags VARCHAR(50)[] NOT NULL,
  score INT DEFAULT 0,
  view_count INT DEFAULT 0,
  answer_count INT DEFAULT 0,
  accepted_answer_id BIGINT,
  is_answered BOOLEAN DEFAULT FALSE,
  owner_id BIGINT,
  owner_reputation INT,
  created_at TIMESTAMP NOT NULL,
  last_activity_date TIMESTAMP,
  link TEXT,
  collected_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_so_tags ON stackoverflow_questions USING GIN(tags);
CREATE INDEX idx_so_score ON stackoverflow_questions(score DESC);
CREATE INDEX idx_so_created ON stackoverflow_questions(created_at DESC);
```

**Queries comuns**:
```sql
-- Top problems por tecnologia
SELECT UNNEST(tags) as tag,
  COUNT(*) as questions,
  AVG(view_count) as avg_views
FROM stackoverflow_questions
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY tag
ORDER BY questions DESC
LIMIT 30;

-- Unanswered difficult questions
SELECT title, tags, score, view_count
FROM stackoverflow_questions
WHERE is_answered = FALSE
  AND score > 5
  AND created_at > NOW() - INTERVAL '7 days'
ORDER BY score DESC;
```

---

## 💰 Módulo: Finance

### market_data_brazil

Ações da B3 (Bolsa brasileira).

```sql
CREATE TABLE market_data_brazil (
  id SERIAL PRIMARY KEY,
  ticker VARCHAR(10) NOT NULL,
  company VARCHAR(255) NOT NULL,
  sector VARCHAR(100),
  price DECIMAL(12, 2),
  change_pct DECIMAL(6, 2),
  volume BIGINT,
  market_cap BIGINT,
  pe_ratio DECIMAL(8, 2),
  dividend_yield DECIMAL(5, 2),
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(ticker, collected_at::DATE)
);

-- Indexes
CREATE INDEX idx_b3_ticker ON market_data_brazil(ticker);
CREATE INDEX idx_b3_sector ON market_data_brazil(sector);
CREATE INDEX idx_b3_collected ON market_data_brazil(collected_at DESC);
```

---

### market_data_nasdaq

Stocks do NASDAQ.

```sql
CREATE TABLE market_data_nasdaq (
  id SERIAL PRIMARY KEY,
  ticker VARCHAR(10) NOT NULL,
  company VARCHAR(255) NOT NULL,
  sector VARCHAR(100),
  price DECIMAL(12, 2),
  change_pct DECIMAL(6, 2),
  volume BIGINT,
  market_cap BIGINT,
  pe_ratio DECIMAL(8, 2),
  eps DECIMAL(8, 2),
  beta DECIMAL(5, 2),
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(ticker, collected_at::DATE)
);

-- Indexes
CREATE INDEX idx_nasdaq_ticker ON market_data_nasdaq(ticker);
CREATE INDEX idx_nasdaq_sector ON market_data_nasdaq(sector);
CREATE INDEX idx_nasdaq_collected ON market_data_nasdaq(collected_at DESC);
```

---

### funding_rounds

Rodadas de investimento.

```sql
CREATE TABLE funding_rounds (
  id SERIAL PRIMARY KEY,
  company VARCHAR(255) NOT NULL,
  sector VARCHAR(100),
  round_type VARCHAR(50), -- 'Seed' | 'Series A' | 'Series B' | etc
  amount_usd BIGINT,
  valuation_usd BIGINT,
  investors TEXT[],
  lead_investor VARCHAR(255),
  announced_date DATE NOT NULL,
  country VARCHAR(100),
  description TEXT,
  source TEXT,
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(company, round_type, announced_date)
);

-- Indexes
CREATE INDEX idx_funding_company ON funding_rounds(company);
CREATE INDEX idx_funding_sector ON funding_rounds(sector);
CREATE INDEX idx_funding_announced ON funding_rounds(announced_date DESC);
CREATE INDEX idx_funding_investors ON funding_rounds USING GIN(investors);
```

**Queries comuns**:
```sql
-- Top funding rounds recentes
SELECT company, round_type,
  amount_usd / 1000000000.0 as amount_billions,
  valuation_usd / 1000000000.0 as valuation_billions
FROM funding_rounds
WHERE announced_date > NOW() - INTERVAL '6 months'
ORDER BY amount_usd DESC
LIMIT 20;

-- Setores mais aquecidos
SELECT sector,
  COUNT(*) as rounds,
  SUM(amount_usd) / 1000000000.0 as total_billions
FROM funding_rounds
WHERE announced_date > NOW() - INTERVAL '1 year'
GROUP BY sector
ORDER BY total_billions DESC;
```

---

## 🔗 Relationships & Views

### Materialized Views

**innovation_scores**: Score de inovação por empresa

```sql
CREATE MATERIALIZED VIEW innovation_scores AS
SELECT
  COALESCE(p.assignee, f.company) as company,
  COUNT(DISTINCT p.patent_number) as patents,
  COUNT(DISTINCT ct.trial_id) as clinical_trials,
  SUM(f.amount_usd) as total_funding,
  (
    COUNT(DISTINCT p.patent_number) * 10 +
    COUNT(DISTINCT ct.trial_id) * 20 +
    COALESCE(SUM(f.amount_usd) / 1000000000, 0) * 5
  ) as innovation_score
FROM patents p
FULL OUTER JOIN funding_rounds f ON p.assignee = f.company
LEFT JOIN clinical_trials ct ON p.assignee = ct.sponsor
GROUP BY COALESCE(p.assignee, f.company)
HAVING COUNT(DISTINCT p.patent_number) > 0
   OR COUNT(DISTINCT ct.trial_id) > 0
   OR SUM(f.amount_usd) > 0;

CREATE UNIQUE INDEX idx_innovation_company ON innovation_scores(company);
```

**tech_trends**: Tendências de tecnologias

```sql
CREATE MATERIALIZED VIEW tech_trends AS
SELECT
  g.language as technology,
  COUNT(DISTINCT g.repo_id) as github_repos,
  SUM(g.stars) as total_stars,
  COUNT(DISTINCT sq.question_id) as so_questions,
  COUNT(DISTINCT sp.id) as packages,
  SUM(sp.downloads_month) as total_downloads
FROM github_repos g
LEFT JOIN stackoverflow_questions sq
  ON g.language = ANY(sq.tags)
LEFT JOIN software_packages sp
  ON g.language = ANY(sp.keywords)
WHERE g.language IS NOT NULL
GROUP BY g.language;
```

---

## 🔧 Manutenção

### Refresh Materialized Views

```sql
-- Manual
REFRESH MATERIALIZED VIEW CONCURRENTLY innovation_scores;
REFRESH MATERIALIZED VIEW CONCURRENTLY tech_trends;

-- Automatizado (cron)
-- daily: 5h
0 5 * * * psql -U sofia -d sofia_db -c "REFRESH MATERIALIZED VIEW CONCURRENTLY innovation_scores;"
```

### Vacuum & Analyze

```sql
-- Weekly maintenance
VACUUM ANALYZE arxiv_papers;
VACUUM ANALYZE patents;
VACUUM ANALYZE github_repos;

-- Automatizado (cron)
-- sunday: 3h
0 3 * * 0 psql -U sofia -d sofia_db -c "VACUUM ANALYZE;"
```

### Partitioning (Large Tables)

```sql
-- Quando arxiv_papers > 1M rows
CREATE TABLE arxiv_papers_partitioned (
  LIKE arxiv_papers INCLUDING ALL
) PARTITION BY RANGE (published_date);

CREATE TABLE arxiv_papers_2024 PARTITION OF arxiv_papers_partitioned
  FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

---

<p align="center">
  <strong>Schema otimizado para queries analíticas e correlações multi-fonte</strong>
</p>
