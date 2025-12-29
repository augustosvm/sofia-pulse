# 🌟 Sofia Pulse - Plataforma de Inteligência Agregada Multi-Fonte

[![Status](https://img.shields.io/badge/status-production-green.svg)](https://github.com/augustosvm/sofia-pulse)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Node](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen.svg)](https://nodejs.org)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15%2B-blue.svg)](https://postgresql.org)

**Sofia Pulse** é um ecossistema integrado de inteligência que coleta, processa e gera insights a partir de múltiplas fontes de dados sobre inovação, pesquisa acadêmica, tecnologia e mercado financeiro.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Fontes de Dados](#-fontes-de-dados)
- [Quick Start](#-quick-start)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Automação](#-automação)
- [API & Schema](#-api--schema)
- [Dashboards](#-dashboards)
- [Desenvolvimento](#-desenvolvimento)
- [Deploy](#-deploy)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

---

## 🎯 Visão Geral

Sofia Pulse combina dados de **11+ fontes diferentes** para gerar inteligência acionável sobre:

- 📚 **Pesquisa Acadêmica**: Papers, teses, artigos científicos
- 🏥 **Inovação em Saúde**: Ensaios clínicos, patentes médicas
- 💻 **Tecnologia**: Repositórios GitHub, pacotes npm/pip, Q&A
- 💰 **Mercado Financeiro**: Ações B3/NASDAQ, funding rounds
- 🔬 **Propriedade Intelectual**: Patentes de inovação

### Diferenciais

✅ **Multi-fonte**: Correlaciona dados de diferentes domínios
✅ **Automático**: Coleta e processamento agendados via cron
✅ **Escalável**: Arquitetura modular e extensível
✅ **Open Data**: Foco em fontes públicas e gratuitas
✅ **Insights Únicos**: Detecção de tendências cross-domain

---

## 🚀 Funcionalidades

### Coleta de Dados

| Módulo | Fonte | Tipo | Frequência |
|--------|-------|------|------------|
| **Academia** | ArXiv | Papers científicos | Diária |
| | BDTD | Teses/dissertações BR | Mensal |
| | SciELO | Artigos peer-reviewed | Semanal |
| **Inovação** | Clinical Trials | Ensaios clínicos | Semanal |
| | Patents | Patentes USPTO/INPI | Mensal |
| **Tech** | GitHub | Repositórios trending | Diária |
| | NPM/PyPI | Downloads de pacotes | Semanal |
| | StackOverflow | Perguntas Q&A | Diária |
| **Finance** | B3 | Ações brasileiras | Diária |
| | NASDAQ | Stocks US | Diária |
| | Funding Rounds | Rodadas investimento | Semanal |

### Processamento & Insights

- 🎯 **Geração de Sinais**: Scores compostos de inovação/investimento
- 📊 **Correlações**: Cruzamento entre fontes para insights únicos
- 🔍 **Tendências**: Detecção de tecnologias e áreas emergentes
- 📈 **Predições**: Identificação de startups/empresas promissoras
- 🎨 **Visualizações**: Dashboards Grafana integrados

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    FONTES DE DADOS                          │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  Academia   │  Inovação   │  Tech       │  Finance        │
│  • ArXiv    │  • Trials   │  • GitHub   │  • B3           │
│  • BDTD     │  • Patents  │  • Packages │  • NASDAQ       │
│  • SciELO   │             │  • Stack    │  • Funding      │
└──────┬──────┴──────┬──────┴──────┬──────┴────────┬─────────┘
       │             │             │                │
       └─────────────┴─────────────┴────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  COLETA & PROCESSAMENTO                     │
│  • Scripts TypeScript (.ts)                                 │
│  • Rate limiting & retry logic                              │
│  • Data validation & cleaning                               │
│  • Metadata extraction                                      │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              ARMAZENAMENTO (PostgreSQL)                     │
│  • sofia_db (11+ tabelas especializadas)                    │
│  • Indexes otimizados para queries                          │
│  • Backup automatizado diário                               │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│               ANÁLISE & INTELIGÊNCIA                        │
│  • Correlações multi-fonte                                  │
│  • Score de inovação composto                               │
│  • Detecção de tendências                                   │
│  • Sinais de investimento                                   │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                      OUTPUTS                                │
│  • JSON reports (diários/semanais)                          │
│  • Dashboards Grafana                                       │
│  • API REST (integração externa)                            │
│  • Alertas (Telegram/Discord)                               │
└─────────────────────────────────────────────────────────────┘
```

### Stack Tecnológica

- **Backend**: Node.js 18+, TypeScript 5.3+
- **Database**: PostgreSQL 15+ (com pgvector)
- **Containerização**: Docker & Docker Compose
- **Orquestração**: Cron jobs (daily/weekly/monthly)
- **Visualização**: Grafana, Metabase
- **Backup**: Automated PostgreSQL dumps (gzip)

---

## 📊 Fontes de Dados (EM PRODUÇÃO)

> **Status**: ✅ 14 collectors ativos | ⏰ Automação via cron | 💾 PostgreSQL 15+

Sofia Pulse coleta dados de **14 fontes diferentes** em produção. Abaixo está a lista COMPLETA de todos os collectors atualmente rodando no sistema.

---

### 📈 1. Finance & Market Intelligence (3 collectors)

Dados de mercado financeiro brasileiro e internacional.

#### 1.1. B3 Stocks (`collect:brazil`)
- **Script**: `finance/scripts/collect-brazil-stocks.ts`
- **Tabela**: `market_data_brazil`
- **Dados**: Ações da Bolsa Brasileira (B3)
- **Frequência**: Segunda a Sexta, 21:00 UTC (18:00 BRT)
- **Empresas**: PETR4, VALE3, ITUB4, BBDC4, WEGE3, ABEV3, RENT3, etc
- **Campos**: ticker, company, sector, price, change_pct, volume, market_cap

**Schema:**
```sql
CREATE TABLE market_data_brazil (
  id SERIAL PRIMARY KEY,
  ticker VARCHAR(10),
  company VARCHAR(255),
  sector VARCHAR(100),
  price DECIMAL(10,2),
  change_pct DECIMAL(5,2),
  volume BIGINT,
  market_cap BIGINT,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

#### 1.2. NASDAQ Stocks (`collect:nasdaq`)
- **Script**: `finance/scripts/collect-nasdaq-momentum.ts`
- **Tabela**: `market_data_nasdaq`
- **Dados**: High-momentum tech stocks (NASDAQ)
- **Frequência**: Segunda a Sexta, 21:00 UTC (18:00 BRT)
- **Empresas**: NVDA, TSLA, MSFT, AAPL, GOOGL, META, AMD, etc
- **Campos**: ticker, company, sector, price, change_pct, volume, market_cap
- **Rate Limit**: 60s de delay (Alpha Vantage API)

**Schema:**
```sql
CREATE TABLE market_data_nasdaq (
  id SERIAL PRIMARY KEY,
  ticker VARCHAR(10),
  company VARCHAR(255),
  sector VARCHAR(100),
  price DECIMAL(10,2),
  change_pct DECIMAL(5,2),
  volume BIGINT,
  market_cap BIGINT,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

#### 1.3. Funding Rounds (`collect:funding`)
- **Script**: `finance/scripts/collect-funding-rounds.ts`
- **Tabela**: `sofia.funding_rounds`
- **Dados**: Rodadas de investimento VC/PE
- **Frequência**: Segunda a Sexta, 21:00 UTC (18:00 BRT)
- **Setores**: AI, Defense AI, Fintech, Biotech, SaaS, etc
- **Rounds**: Seed, Series A-H, Growth, etc
- **Campos**: company, sector, round_type, amount_usd, valuation_usd, investors, announced_date, country

**Schema:**
```sql
CREATE TABLE sofia.funding_rounds (
  id SERIAL PRIMARY KEY,
  company VARCHAR(255),
  sector VARCHAR(100),
  round_type VARCHAR(50),
  amount_usd BIGINT,
  valuation_usd BIGINT,
  investors TEXT[],
  announced_date DATE,
  country VARCHAR(100),
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 🔬 2. Research & Academia (2 collectors)

Papers científicos e artigos de pesquisa ANTES de serem publicados.

#### 2.1. ArXiv AI/ML Papers (`collect:arxiv-ai`)
- **Script**: `scripts/collect-arxiv-ai.ts`
- **Tabela**: `arxiv_ai_papers`
- **Fonte**: ArXiv.org (pre-prints)
- **Frequência**: Diário, 20:00 UTC
- **Categorias**: cs.AI, cs.LG, cs.CV, cs.CL, cs.NE, cs.RO
- **Por que é crítico**: Papers aparecem 6-12 MESES ANTES de journals. GPT, BERT, Transformers, Diffusion - todos no ArXiv primeiro!
- **Campos**: arxiv_id, title, authors, categories, abstract, published_date, pdf_url, keywords, is_breakthrough

**Schema:**
```sql
CREATE TABLE arxiv_ai_papers (
  id SERIAL PRIMARY KEY,
  arxiv_id VARCHAR(50) UNIQUE,
  title TEXT NOT NULL,
  authors TEXT[],
  categories VARCHAR(20)[],
  abstract TEXT,
  published_date DATE,
  updated_date DATE,
  pdf_url TEXT,
  primary_category VARCHAR(20),
  keywords TEXT[],
  is_breakthrough BOOLEAN DEFAULT FALSE,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

#### 2.2. OpenAlex Papers (`collect:openalex`)
- **Script**: `scripts/collect-openalex.ts`
- **Tabela**: `openalex_papers`
- **Fonte**: OpenAlex.org (catálogo global de pesquisa científica)
- **Frequência**: Diário, 20:05 UTC
- **Dados**: 240M+ papers, citações, autores, instituições
- **Campos**: openalex_id, doi, title, authors, institutions, concepts, publication_year, cited_by_count

**Schema:**
```sql
CREATE TABLE openalex_papers (
  id SERIAL PRIMARY KEY,
  openalex_id VARCHAR(100) UNIQUE,
  doi VARCHAR(100),
  title TEXT,
  authors TEXT[],
  institutions TEXT[],
  concepts TEXT[],
  publication_year INT,
  cited_by_count INT,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 🤖 3. AI & Innovation (1 collector)

Empresas de IA e suas tecnologias.

#### 3.1. AI Companies (`collect:ai-companies`)
- **Script**: `scripts/collect-ai-companies.ts`
- **Tabela**: `ai_companies`
- **Frequência**: Diário, 20:10 UTC
- **Dados**: Empresas de IA, tecnologias, casos de uso
- **Campos**: company, description, category, technologies, use_cases, founded_year, funding_total, website

**Schema:**
```sql
CREATE TABLE ai_companies (
  id SERIAL PRIMARY KEY,
  company VARCHAR(255),
  description TEXT,
  category VARCHAR(100),
  technologies TEXT[],
  use_cases TEXT[],
  founded_year INT,
  funding_total BIGINT,
  website TEXT,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 📜 4. Patents & IP (2 collectors)

Propriedade intelectual e patentes de inovação.

#### 4.1. WIPO China Patents (`collect:wipo-china`)
- **Script**: `scripts/collect-wipo-china-patents.ts`
- **Tabela**: `wipo_china_patents`
- **Fonte**: WIPO (World Intellectual Property Organization)
- **Frequência**: Diário, 01:00 UTC
- **Foco**: Patentes chinesas (líder global em patentes AI, hardware, manufacturing)
- **Campos**: publication_number, title, abstract, applicant, filing_date, publication_date, ipc_codes

**Schema:**
```sql
CREATE TABLE wipo_china_patents (
  id SERIAL PRIMARY KEY,
  publication_number VARCHAR(50) UNIQUE,
  title TEXT,
  abstract TEXT,
  applicant VARCHAR(255),
  filing_date DATE,
  publication_date DATE,
  ipc_codes VARCHAR(20)[],
  collected_at TIMESTAMP DEFAULT NOW()
);
```

#### 4.2. EPO Patents (`collect:epo`)
- **Script**: `scripts/collect-epo-patents.ts`
- **Tabela**: `epo_patents`
- **Fonte**: EPO (European Patent Office)
- **Frequência**: Diário, 01:00 UTC
- **Foco**: Patentes europeias (Green Tech, Privacy Tech, Mobility)
- **Campos**: publication_number, title, abstract, applicants, inventors, filing_date, ipc_codes

**Schema:**
```sql
CREATE TABLE epo_patents (
  id SERIAL PRIMARY KEY,
  publication_number VARCHAR(50) UNIQUE,
  title TEXT,
  abstract TEXT,
  applicants TEXT[],
  inventors TEXT[],
  filing_date DATE,
  publication_date DATE,
  ipc_codes VARCHAR(20)[],
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 💼 5. IPOs & Public Markets (1 collector)

#### 5.1. HKEX IPOs (`collect:hkex`)
- **Script**: `scripts/collect-hkex-ipos.ts`
- **Tabela**: `hkex_ipos`
- **Fonte**: Hong Kong Exchanges and Clearing Limited
- **Frequência**: Segunda a Sexta, 02:00 UTC
- **Dados**: IPOs de empresas asiáticas (China, Hong Kong, etc)
- **Campos**: stock_code, company_name, listing_date, offer_price, shares_offered, market_cap

**Schema:**
```sql
CREATE TABLE hkex_ipos (
  id SERIAL PRIMARY KEY,
  stock_code VARCHAR(10),
  company_name VARCHAR(255),
  listing_date DATE,
  offer_price DECIMAL(10,2),
  shares_offered BIGINT,
  market_cap BIGINT,
  sector VARCHAR(100),
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 🏥 6. Biotech & Healthcare (1 collector)

#### 6.1. NIH Grants (`collect:nih-grants`)
- **Script**: `scripts/collect-nih-grants.ts`
- **Tabela**: `nih_grants`
- **Fonte**: NIH Reporter (National Institutes of Health)
- **Frequência**: Semanal (Segunda, 03:00 UTC)
- **Dados**: Grants federais para pesquisa biomédica
- **Campos**: project_num, pi_name, org_name, project_title, fiscal_year, award_amount, project_start, project_end

**Schema:**
```sql
CREATE TABLE nih_grants (
  id SERIAL PRIMARY KEY,
  project_num VARCHAR(50) UNIQUE,
  pi_name VARCHAR(255),
  org_name VARCHAR(255),
  project_title TEXT,
  fiscal_year INT,
  award_amount BIGINT,
  project_start DATE,
  project_end DATE,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 🎓 7. Universities & Academia (1 collector)

#### 7.1. Asia Universities (`collect:asia-universities`)
- **Script**: `scripts/collect-asia-universities.ts`
- **Tabela**: `asia_universities`
- **Frequência**: Mensal (dia 1, 04:00 UTC)
- **Dados**: Universidades asiáticas, rankings, especialização
- **Campos**: university_name, country, rank_global, rank_regional, specializations, research_output

**Schema:**
```sql
CREATE TABLE asia_universities (
  id SERIAL PRIMARY KEY,
  university_name VARCHAR(255),
  country VARCHAR(100),
  rank_global INT,
  rank_regional INT,
  specializations TEXT[],
  research_output INT,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 📦 8. Economic Indicators (1 collector)

#### 8.1. Cardboard Production (`collect:cardboard`)
- **Script**: `scripts/collect-cardboard-production.ts`
- **Tabela**: `cardboard_production`
- **Fonte**: Leading indicator de atividade econômica
- **Frequência**: Semanal (Segunda, 05:00 UTC)
- **Por que é relevante**: Produção de papelão correlaciona com e-commerce, manufatura, logística. Antecede PIB em 3-6 meses!
- **Campos**: country, month, production_tons, change_pct, sector

**Schema:**
```sql
CREATE TABLE cardboard_production (
  id SERIAL PRIMARY KEY,
  country VARCHAR(100),
  month DATE,
  production_tons BIGINT,
  change_pct DECIMAL(5,2),
  sector VARCHAR(50),
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 📅 9. IPO Calendar (1 collector)

#### 9.1. IPO Calendar (`collect:ipo-calendar`)
- **Script**: `collectors/ipo-calendar.ts`
- **Tabela**: `sofia.ipo_calendar`
- **Fontes**: NASDAQ, B3, SEC/EDGAR
- **Frequência**: Diário, 06:00 UTC
- **Dados**: Empresas que VÃO abrir capital (próximos 30 dias)
- **Campos**: company, exchange, expected_date, sector, price_range_low, price_range_high, shares_offered

**Schema:**
```sql
CREATE TABLE sofia.ipo_calendar (
  id SERIAL PRIMARY KEY,
  company VARCHAR(255),
  exchange VARCHAR(20),
  expected_date DATE,
  sector VARCHAR(100),
  price_range_low DECIMAL(10,2),
  price_range_high DECIMAL(10,2),
  shares_offered BIGINT,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 💼 10. Jobs Market (1 collector)

#### 10.1. Tech Jobs (`collect:jobs`)
- **Script**: `collectors/jobs-collector.ts`
- **Tabela**: `sofia.jobs`
- **Fontes**: Indeed, LinkedIn Jobs API, AngelList/Wellfound
- **Frequência**: Diário, 07:00 UTC
- **Dados**: Vagas de emprego tech por país, setor, remote
- **Campos**: title, company, location, country, sector, remote, salary_range, posted_date, url

**Schema:**
```sql
CREATE TABLE sofia.jobs (
  id SERIAL PRIMARY KEY,
  title TEXT,
  company VARCHAR(255),
  location VARCHAR(255),
  country VARCHAR(100),
  sector VARCHAR(100),
  remote BOOLEAN,
  salary_range VARCHAR(100),
  posted_date DATE,
  url TEXT,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

## ⚡ Quick Start

### Pré-requisitos

- Node.js 18+ e npm 9+
- PostgreSQL 15+
- Docker & Docker Compose (opcional)
- Git

### Instalação Rápida

```bash
# 1. Clone o repositório
git clone https://github.com/augustosvm/sofia-pulse.git
cd sofia-pulse

# 2. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 3. Instale dependências
npm install

# 4. Configure banco de dados
npm run migrate

# 5. Teste coleta (finance module - mais rápido)
cd finance
npm install
npm run demo

# 6. Ver resultados
cat output/sofia-signals-*.json | jq
```

---

## 💾 Instalação

### Opção 1: Docker (Recomendado)

```bash
# Subir PostgreSQL + serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Executar coleta
docker-compose exec sofia npm run collect:all

# Parar serviços
docker-compose down
```

### Opção 2: Instalação Local

#### 1. PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql-15 postgresql-contrib

# macOS
brew install postgresql@15

# Iniciar serviço
sudo systemctl start postgresql
```

#### 2. Criar Database

```bash
sudo -u postgres psql

CREATE DATABASE sofia_db;
CREATE USER sofia WITH PASSWORD 'sofia123strong';
GRANT ALL PRIVILEGES ON DATABASE sofia_db TO sofia;
\q
```

#### 3. Node.js & Dependências

```bash
# Instalar Node.js 18+
# Via nvm (recomendado)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Instalar dependências
npm install
```

#### 4. Rodar Migrações

```bash
npm run migrate
```

---

## 🎮 Uso

### Coleta de Dados

#### Comandos Disponíveis

```bash
# Academia
npm run collect:arxiv          # Papers ArXiv
npm run collect:bdtd           # Teses BDTD
npm run collect:scielo         # Artigos SciELO

# Inovação
npm run collect:clinical       # Clinical Trials
npm run collect:patents        # Patentes

# Tech
npm run collect:github         # GitHub trending
npm run collect:packages       # NPM/PyPI downloads
npm run collect:stackoverflow  # Stack Q&A

# Finance (módulo separado)
cd finance
npm run collect:brazil         # B3 stocks
npm run collect:nasdaq         # NASDAQ
npm run collect:funding        # Funding rounds

# Coletar tudo
npm run collect:all
```

#### Coleta Manual

```bash
# Exemplo: Coletar papers do ArXiv
npm run collect:arxiv

# Com filtros (editar script)
npm run collect:arxiv -- --category=cs.AI --since=2024-01-01
```

### Geração de Insights

```bash
# Gerar sinais de investimento (finance module)
cd finance
npm run signals

# Gerar score de inovação multi-fonte
npm run analyze:innovation

# Detectar tendências tech
npm run analyze:trends

# Correlação pesquisa → mercado
npm run analyze:research-to-market
```

### Queries & Análises

```bash
# Conectar ao banco
docker exec -it sofia-postgres psql -U sofia -d sofia_db

# Ou localmente
psql -U sofia -d sofia_db
```

#### Exemplos de Queries

**Top empresas inovadoras (patentes + funding):**
```sql
SELECT
  p.assignee as company,
  COUNT(DISTINCT p.patent_number) as patents,
  f.round_type,
  f.amount_usd / 1000000000 as funding_billions
FROM patents p
JOIN funding_rounds f ON p.assignee = f.company
WHERE p.grant_date > NOW() - INTERVAL '2 years'
GROUP BY p.assignee, f.round_type, f.amount_usd
HAVING COUNT(DISTINCT p.patent_number) > 10
ORDER BY patents DESC, funding_billions DESC
LIMIT 20;
```

**Tecnologias emergentes (GitHub + StackOverflow):**
```sql
SELECT
  g.language,
  SUM(g.stars) as total_stars,
  COUNT(DISTINCT g.repo_id) as repos,
  COUNT(DISTINCT sq.question_id) as so_questions
FROM github_repos g
LEFT JOIN stackoverflow_questions sq
  ON g.language = ANY(sq.tags)
WHERE g.created_at > NOW() - INTERVAL '6 months'
GROUP BY g.language
ORDER BY total_stars DESC
LIMIT 15;
```

**Pipeline pesquisa → produto (ArXiv → Patents → Funding):**
```sql
SELECT
  a.categories[1] as research_area,
  COUNT(DISTINCT a.arxiv_id) as papers,
  COUNT(DISTINCT p.patent_number) as patents,
  COUNT(DISTINCT f.company) as funded_companies,
  AVG(f.amount_usd) as avg_funding
FROM arxiv_papers a
LEFT JOIN patents p ON a.categories && p.classifications
LEFT JOIN funding_rounds f ON p.assignee = f.company
WHERE a.published_date > '2023-01-01'
GROUP BY research_area
HAVING COUNT(DISTINCT a.arxiv_id) > 100
ORDER BY papers DESC;
```

---

## ⚙️ Automação

### Cron Jobs (EM PRODUÇÃO)

> **Status**: ✅ Cron LIMPO instalado | 📊 14 collectors + 2 insights/email + 5 backups = 21 jobs

Sofia Pulse usa cron jobs para automação completa. O sistema roda 24/7 sem intervenção manual.

#### Instalação Rápida

```bash
# No servidor
cd /home/ubuntu/sofia-pulse
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE
bash install-clean-crontab.sh
```

Ver guia completo: [`GUIA-INSTALACAO-CRON-LIMPO.md`](GUIA-INSTALACAO-CRON-LIMPO.md)

---

#### Cronograma Completo (todos os horários em UTC)

**Diário:**
```bash
20:00 - ArXiv AI Papers
20:05 - OpenAlex Papers
20:10 - AI Companies
01:00 - Patentes (WIPO China + EPO)
06:00 - IPO Calendar (NASDAQ, B3, SEC)
07:00 - Jobs (Indeed, LinkedIn, AngelList)
```

**Segunda a Sexta (dias úteis):**
```bash
21:00 - Finance (B3, NASDAQ, Funding)
22:00 - Premium Insights v2.0
23:00 - Email com Insights + CSVs
02:00 - HKEX IPOs
```

**Semanal (Segundas):**
```bash
03:00 - NIH Grants (biomedicina)
05:00 - Cardboard Production (leading indicator)
```

**Mensal (Dia 1):**
```bash
04:00 - Universidades Ásia
```

**Backups (mantidos do cron original):**
```bash
*/1 * * * * - Auto-recovery
03:00 - Comprehensive backup
02:00 - Dashboard backup
02:00 (Qua) - Full backup
04:00 - Sofia backup
```

---

### Crontab Completo (Copy-Paste)

```bash
# ============================================================================
# SOFIA PULSE - Cron Jobs (LIMPO - v2.0)
# ============================================================================

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# ============================================================================
# 1. COLLECTORS - Dados Reais
# ============================================================================

# Finance (B3, NASDAQ, Funding) - Seg-Sex às 21:00 UTC (18:00 BRT)
0 21 * * 1-5 cd /home/ubuntu/sofia-pulse && ./collect-finance.sh >> /var/log/sofia-finance.log 2>&1

# ArXiv AI Papers - Diário às 20:00 UTC
0 20 * * * cd /home/ubuntu/sofia-pulse && npm run collect:arxiv-ai >> /var/log/sofia-arxiv.log 2>&1

# OpenAlex Papers - Diário às 20:05 UTC
5 20 * * * cd /home/ubuntu/sofia-pulse && npm run collect:openalex >> /var/log/sofia-openalex.log 2>&1

# AI Companies - Diário às 20:10 UTC
10 20 * * * cd /home/ubuntu/sofia-pulse && npm run collect:ai-companies >> /var/log/sofia-ai-companies.log 2>&1

# Patentes (WIPO China, EPO) - Diário às 01:00 UTC
0 1 * * * cd /home/ubuntu/sofia-pulse && npm run collect:patents-all >> /var/log/sofia-patents.log 2>&1

# IPOs Hong Kong - Seg-Sex às 02:00 UTC
0 2 * * 1-5 cd /home/ubuntu/sofia-pulse && npm run collect:hkex >> /var/log/sofia-hkex.log 2>&1

# NIH Grants (Biotech) - Semanal (segunda às 03:00 UTC)
0 3 * * 1 cd /home/ubuntu/sofia-pulse && npm run collect:nih-grants >> /var/log/sofia-nih.log 2>&1

# Universidades Ásia - Mensal (dia 1 às 04:00 UTC)
0 4 1 * * cd /home/ubuntu/sofia-pulse && npm run collect:asia-universities >> /var/log/sofia-unis.log 2>&1

# Cardboard Production - Semanal (segunda às 05:00 UTC)
0 5 * * 1 cd /home/ubuntu/sofia-pulse && npm run collect:cardboard >> /var/log/sofia-cardboard.log 2>&1

# IPO Calendar (NASDAQ, B3, SEC) - Diário às 06:00 UTC
0 6 * * * cd /home/ubuntu/sofia-pulse && npm run collect:ipo-calendar >> /var/log/sofia-ipo.log 2>&1

# Jobs (Indeed, LinkedIn, AngelList) - Diário às 07:00 UTC
0 7 * * * cd /home/ubuntu/sofia-pulse && npm run collect:jobs >> /var/log/sofia-jobs.log 2>&1

# ============================================================================
# 2. INSIGHTS GENERATION (v2.0 - Com Análise Temporal!)
# ============================================================================

# Premium Insights v2.0 - Seg-Sex às 22:00 UTC (19:00 BRT)
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && source venv-analytics/bin/activate && ./generate-insights-v2.0.sh >> /var/log/sofia-insights-v2.log 2>&1

# ============================================================================
# 3. EMAIL & REPORTING
# ============================================================================

# Email com Insights - Seg-Sex às 23:00 UTC (20:00 BRT)
0 23 * * 1-5 cd /home/ubuntu/sofia-pulse && ./send-insights-email.sh >> /var/log/sofia-email.log 2>&1

# ============================================================================
# 4. BACKUPS
# ============================================================================

# Auto-recovery (a cada 1 minuto)
*/1 * * * * /home/ubuntu/infraestrutura/scripts/auto-recovery.sh

# Backups diversos
0 3 * * * /home/ubuntu/infraestrutura/scripts/comprehensive-backup.sh
0 2 * * * /home/ubuntu/infraestrutura/scripts/backup-dashboards.sh
0 2 * * 3 /home/ubuntu/infraestrutura/scripts/full-backup.sh

# Sofia Pulse backup
0 4 * * * cd /home/ubuntu/sofia-pulse && ./scripts/backup-complete.sh >> /var/log/sofia-backup.log 2>&1
```

---

### Comandos Úteis

```bash
# Ver cron instalado
crontab -l

# Ver logs em tempo real
tail -f /var/log/sofia-*.log

# Ver último erro de um collector
grep -i error /var/log/sofia-arxiv.log | tail -20

# Testar collector manualmente
npm run collect:arxiv-ai

# Ver status dos jobs
ps aux | grep "collect"
```

---

## 📡 API & Schema

### REST API (Em Desenvolvimento)

#### Endpoints Planejados

```
GET  /api/v1/signals              # Investment signals
GET  /api/v1/trends               # Technology trends
GET  /api/v1/innovation/:company  # Innovation score
GET  /api/v1/research/areas       # Research areas trending
GET  /api/v1/patents/:company     # Company patents
GET  /api/v1/clinical-trials      # Active trials
```

### Database Schema Completo

**Resumo das tabelas (14 em produção):**

```
sofia_db
├── Finance (3 tabelas)
│   ├── market_data_brazil        # B3 stocks
│   ├── market_data_nasdaq        # NASDAQ stocks
│   └── sofia.funding_rounds      # VC/PE deals
├── Research & Academia (2 tabelas)
│   ├── arxiv_ai_papers           # AI/ML pre-prints
│   └── openalex_papers           # Global research papers
├── AI & Innovation (1 tabela)
│   └── ai_companies              # AI companies & tech
├── Patents & IP (2 tabelas)
│   ├── wipo_china_patents        # Patentes China
│   └── epo_patents               # Patentes Europa
├── Public Markets (1 tabela)
│   └── hkex_ipos                 # IPOs Hong Kong
├── Biotech (1 tabela)
│   └── nih_grants                # NIH biomedical grants
├── Academia (1 tabela)
│   └── asia_universities         # Universidades Ásia
├── Economic Indicators (1 tabela)
│   └── cardboard_production      # Leading indicator
├── IPO Pipeline (1 tabela)
│   └── sofia.ipo_calendar        # Upcoming IPOs
└── Jobs Market (1 tabela)
    └── sofia.jobs                # Tech jobs
```

**Total**: 14 tabelas coletando dados 24/7

---

## 📊 Dashboards

### Grafana

#### Setup

```bash
# Adicionar datasource PostgreSQL
docker exec -it grafana grafana-cli plugins install postgres

# Import dashboard
# Ver dashboards/ para JSONs prontos
```

#### Dashboards Disponíveis

1. **Innovation Overview**
   - Top companies by innovation score
   - Patents vs Funding correlation
   - Research areas trending

2. **Tech Trends**
   - GitHub languages popularity
   - NPM/PyPI downloads
   - StackOverflow questions by tag

3. **Finance Intelligence**
   - Investment signals
   - B3 vs NASDAQ performance
   - Funding rounds timeline

4. **Research Pipeline**
   - ArXiv publications by category
   - Clinical trials by phase
   - BDTD theses by university

---

## 🛠️ Desenvolvimento

### Estrutura de Projeto

```
sofia-pulse/
├── src/                    # Código core
│   ├── collectors/         # Módulos de coleta
│   ├── analyzers/          # Análise e insights
│   ├── utils/              # Utilitários
│   └── types/              # TypeScript types
├── scripts/                # Scripts executáveis
├── migrations/             # Migrações SQL
├── tests/                  # Testes automatizados
├── docs/                   # Documentação
├── finance/                # Módulo finance separado
└── workflows/              # GitHub Actions CI/CD
```

### Adicionar Nova Fonte de Dados

#### 1. Criar Collector

```typescript
// scripts/collect-nova-fonte.ts
import { Client } from 'pg';
import axios from 'axios';

interface NovaFonteData {
  id: string;
  title: string;
  // ... outros campos
}

async function collectNovaFonte() {
  const client = new Client({
    host: process.env.POSTGRES_HOST,
    // ...config
  });

  try {
    await client.connect();

    // Criar tabela se não existir
    await client.query(`
      CREATE TABLE IF NOT EXISTS nova_fonte (
        id SERIAL PRIMARY KEY,
        external_id VARCHAR(100) UNIQUE,
        title TEXT,
        collected_at TIMESTAMP DEFAULT NOW()
      );
    `);

    // Coletar dados
    const response = await axios.get('https://api.novafonte.com/data');
    const data: NovaFonteData[] = response.data;

    // Inserir no banco
    for (const item of data) {
      await client.query(`
        INSERT INTO nova_fonte (external_id, title)
        VALUES ($1, $2)
        ON CONFLICT (external_id) DO NOTHING
      `, [item.id, item.title]);
    }

    console.log(`✅ ${data.length} items coletados`);
  } finally {
    await client.end();
  }
}

collectNovaFonte();
```

#### 2. Adicionar ao package.json

```json
{
  "scripts": {
    "collect:nova-fonte": "tsx scripts/collect-nova-fonte.ts"
  }
}
```

#### 3. Adicionar ao cron

```bash
# Em cron-daily.sh
npm run collect:nova-fonte
```

### Testes

```bash
# Rodar todos testes
npm test

# Teste específico
npm test -- collect-arxiv

# Coverage
npm run test:coverage
```

---

## 🚀 Deploy

### Deploy Produção (Docker)

```bash
# Build images
docker-compose build

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Verificar saúde
docker-compose ps
docker-compose logs -f
```

### Deploy em VPS

Ver guia completo em [`DEPLOY.md`](DEPLOY.md)

**Resumo:**

1. Configurar servidor (Ubuntu 20.04+)
2. Instalar Docker & Docker Compose
3. Configurar firewall e SSL
4. Deploy via docker-compose
5. Configurar cron jobs
6. Setup monitoring (Grafana + Prometheus)

---

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão PostgreSQL

```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres

# Testar conexão
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "SELECT 1;"

# Ver logs
docker logs sofia-postgres --tail 100
```

#### 2. Rate Limit em APIs

```bash
# GitHub: Verificar rate limit
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/rate_limit

# Solução: Aguardar reset ou usar autenticação
```

#### 3. Backup Falhando

```bash
# Verificar permissões
ls -la /var/backups/postgres/

# Criar diretório se necessário
sudo mkdir -p /var/backups/postgres
sudo chown -R $(whoami) /var/backups/postgres

# Rodar backup manualmente
./scripts/backup-complete.sh
```

#### 4. Coleta Travando

```bash
# Ver processos Node rodando
ps aux | grep node

# Matar processo travado
kill -9 <PID>

# Ver logs para debugar
tail -f logs/sofia-*.log
```

### Logs

```bash
# Logs de coleta
tail -f /var/log/sofia-daily.log
tail -f /var/log/sofia-weekly.log

# Logs PostgreSQL
docker logs sofia-postgres --tail 100 -f

# Logs de backup
tail -f /var/log/sofia-backup.log
```

---

## 🗺️ Roadmap

### Q1 2025

- [x] Finance module completo (B3, NASDAQ, Funding)
- [x] Backup automatizado PostgreSQL
- [x] Docker & Docker Compose setup
- [ ] API REST v1
- [ ] Dashboard Grafana completo
- [ ] Testes automatizados

### Q2 2025

- [ ] Machine Learning para predição de scores
- [ ] Backtesting de sinais financeiros
- [ ] Integração n8n para workflows
- [ ] Alertas Telegram/Discord
- [ ] Mobile app (React Native)

### Q3 2025

- [ ] Coleta de criptomoedas (Binance, Coinbase)
- [ ] Análise de sentimento (Twitter, Reddit)
- [ ] Sistema de recomendação personalizado
- [ ] Export para TradingView

### Q4 2025

- [ ] Multi-tenancy
- [ ] API pública (freemium model)
- [ ] Marketplace de sinais
- [ ] Integração Bloomberg Terminal

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, leia nosso [Guia de Contribuição](CONTRIBUTING.md).

### Como Contribuir

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add: AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Code Style

- TypeScript com strict mode
- ESLint + Prettier
- Commits semânticos: `Add:`, `Fix:`, `Update:`, `Remove:`

---

## 📄 Licença

Este projeto está sob a licença MIT. Ver [`LICENSE`](LICENSE) para mais detalhes.

---

## 📞 Suporte & Contato

- **Issues**: [GitHub Issues](https://github.com/augustosvm/sofia-pulse/issues)
- **Discussões**: [GitHub Discussions](https://github.com/augustosvm/sofia-pulse/discussions)
- **Email**: contato@sofia-pulse.com

---

## 🙏 Agradecimentos

- ArXiv por fornecer API gratuita
- BDTD e SciELO pela pesquisa científica brasileira
- GitHub, npm, PyPI por dados abertos
- Comunidade open source

---

## 📚 Documentação Adicional

- [Architecture](docs/ARCHITECTURE.md) - Arquitetura detalhada
- [API Reference](docs/API.md) - Referência completa da API
- [Database Schema](docs/SCHEMA.md) - Schema e relacionamentos
- [Finance Module](finance/README.md) - Documentação do módulo finance
- [Deployment Guide](DEPLOY.md) - Guia de deploy em produção
- [Contributing Guide](CONTRIBUTING.md) - Como contribuir
- [Changelog](CHANGELOG.md) - Histórico de versões

---

<p align="center">
  <strong>🌟 Sofia Pulse - Transformando dados em inteligência acionável</strong>
</p>

<p align="center">
  Feito com ❤️ pela comunidade Sofia
</p>
