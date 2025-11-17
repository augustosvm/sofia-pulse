# 🌍 Sofia Pulse - Expansão de Fontes de Dados

Mapeamento completo de fontes de dados **GRATUITAS** para expansão global, com foco especial na **China** e outras regiões estratégicas.

---

## 🎯 Gap Analysis Atual

### ✅ O Que Já Temos

**Academia (Ocidental)**:
- ArXiv (global, inglês)
- BDTD (Brasil)
- SciELO (América Latina)

**Tech (Global)**:
- GitHub (global)
- npm/PyPI (global)
- StackOverflow (global)

**Finance (Brasil + EUA)**:
- B3 (Brasil)
- NASDAQ (EUA)
- Funding rounds (mock data)

**Inovação**:
- Clinical Trials (global)
- Patents (USPTO - EUA)

### ❌ O Que Está FALTANDO

**CHINA** - **ZERO** cobertura! 🚨
- ❌ Papers chineses
- ❌ Patentes chinesas (CNIPA - maior escritório do mundo!)
- ❌ Startups chinesas
- ❌ IPOs China (Hong Kong, Shanghai, Shenzhen)
- ❌ Universidades chinesas
- ❌ Funding rounds China

**Europa**:
- ❌ EPO Patents (temos USPTO, falta Europa)
- ❌ Exchanges europeias (LSE, Euronext, DAX)
- ❌ Universidades europeias

**Outros**:
- ❌ Índia (NASSCOM, startups indianas)
- ❌ Israel (startup nation)
- ❌ Sudeste Asiático (Singapura, Coreia)

---

## 🇨🇳 CHINA - Fontes Gratuitas (Prioridade ALTA)

### 1. **Academia & Research**

#### CNKI (China National Knowledge Infrastructure)
- **URL**: https://www.cnki.net
- **Dados**: Papers, dissertações, jornais acadêmicos chineses
- **Acesso**: Parcialmente gratuito (abstracts)
- **Volume**: 50M+ documentos
- **API**: Sim (limitada)
- **Idioma**: Chinês + Inglês (alguns)

**Implementação**:
```typescript
// scripts/collect-cnki.ts
// Coletar abstracts de papers recentes
// Tradução automática com Google Translate API (gratuito até 500k chars/mês)
```

#### Wanfang Data
- **URL**: http://www.wanfangdata.com.cn
- **Dados**: Papers, patentes, conferências
- **Acesso**: Gratuito (limitado)
- **Foco**: Ciência e tecnologia

---

### 2. **Patentes Chinesas**

#### CNIPA (China National Intellectual Property Administration)
- **URL**: http://english.cnipa.gov.cn
- **Dados**: Patentes chinesas (maior volume do mundo!)
- **API**: Patent Search API
- **Acesso**: **100% GRATUITO** 🎉
- **Volume**: 4M+ patentes/ano

**Por que é CRÍTICO**:
- China registra **MAIS PATENTES** que EUA + Europa + Japão **JUNTOS**
- Áreas fortes: AI, 5G, batteries, solar, biotech

**Implementação**:
```typescript
// scripts/collect-cnipa-patents.ts
interface CNIPAPatent {
  applicationNumber: string;
  title: string;
  titleEn?: string; // Nem todas têm tradução
  applicant: string;
  inventors: string[];
  ipcClassification: string[];
  filingDate: string;
  publicationDate: string;
  abstract: string;
}
```

---

### 3. **Startups & Venture Capital**

#### 36Kr (36氪)
- **URL**: https://36kr.com
- **Dados**: Startups chinesas, funding rounds, tech news
- **Acesso**: Web scraping (permitido)
- **Foco**: Tech startups China

**Dados coletáveis**:
- Company profiles
- Funding announcements
- Valuation estimates
- Investors

#### ITJuzi (IT桔子)
- **URL**: https://www.itjuzi.com
- **Dados**: Database de startups e investimentos China
- **Acesso**: Freemium (basic data grátis)

**Implementação**:
```typescript
// scripts/collect-china-startups.ts
// Scraping de 36Kr + ITJuzi
// Consolidar dados de funding rounds chineses
```

---

### 4. **Stock Exchanges China**

#### Hong Kong Stock Exchange (HKEX)
- **URL**: https://www.hkex.com.hk
- **API**: Market Data API (gratuita para delayed data)
- **Dados**: IPOs, stock prices (15min delay)
- **Empresas**: Alibaba, Tencent, Xiaomi, etc.

#### Shanghai Stock Exchange (SSE)
- **URL**: http://english.sse.com.cn
- **Dados**: A-shares chinesas
- **Acesso**: Web scraping + RSS feeds

#### Shenzhen Stock Exchange (SZSE)
- **URL**: http://www.szse.cn/English
- **Dados**: Tech companies chinesas
- **Acesso**: Similar SSE

**Implementação**:
```typescript
// scripts/collect-china-ipos.ts
// Coletar IPOs recentes de HKEX, SSE, SZSE
// Integrar com funding_rounds table (adicionar exchange field)
```

---

### 5. **Universidades Chinesas**

#### QS Rankings - China
- **Dados**: Top 100 universidades chinesas
- **Free**: Sim
- **Complemento**: Correlacionar com CNKI papers

**Top Unis**:
- Tsinghua University
- Peking University
- Fudan University
- Shanghai Jiao Tong
- Zhejiang University

---

## 🌍 Outras Fontes Globais GRATUITAS

### Europa

#### EPO (European Patent Office)
- **URL**: https://www.epo.org
- **API**: Open Patent Services (OPS) - **GRATUITA** 🎉
- **Dados**: Patentes europeias
- **Volume**: 180k+ applications/ano

```typescript
// scripts/collect-epo-patents.ts
```

#### Euronext Exchange
- **URL**: https://www.euronext.com
- **Dados**: Paris, Amsterdam, Brussels, Dublin stocks
- **API**: Market data API

#### LSE (London Stock Exchange)
- **URL**: https://www.londonstockexchange.com
- **Dados**: UK stocks, AIM (small caps)
- **RSS**: Free data feeds

---

### Índia

#### NASSCOM (National Association Software & Services Companies)
- **URL**: https://nasscom.in
- **Dados**: Indian tech companies, startups
- **Reports**: Quarterly reports (free)

#### BSE/NSE (Bombay/National Stock Exchange)
- **URL**: https://www.bseindia.com, https://www.nseindia.com
- **Dados**: Indian stocks
- **API**: Limited free access

#### Indian Patent Office
- **URL**: https://ipindiaonline.gov.in
- **Dados**: Indian patents
- **Acesso**: Public search

---

### Sudeste Asiático

#### SGX (Singapore Exchange)
- **URL**: https://www.sgx.com
- **Dados**: Singapore stocks, REITs
- **API**: Market data

#### Korea Exchange (KRX)
- **URL**: http://global.krx.co.kr
- **Dados**: Samsung, LG, Hyundai, etc.
- **Acesso**: Market data feeds

---

### Research Global (Faltando)

#### PubMed
- **URL**: https://pubmed.ncbi.nlm.nih.gov
- **API**: E-utilities (100% gratuita!) 🎉
- **Dados**: 35M+ biomedical papers
- **Foco**: Medicina, biologia, farmacêutica

**CRÍTICO para**:
- Clinical trials correlation
- Drug development
- Biotech signals

```typescript
// scripts/collect-pubmed.ts
```

#### bioRxiv
- **URL**: https://www.biorxiv.org
- **Dados**: Biology preprints
- **API**: RSS feeds + API
- **Foco**: Cutting-edge biology research

#### medRxiv
- **URL**: https://www.medrxiv.org
- **Dados**: Medical research preprints
- **Importante**: COVID-19, doenças, tratamentos

#### SSRN (Social Science Research Network)
- **URL**: https://www.ssrn.com
- **Dados**: Economics, finance, social science papers
- **Acesso**: Gratuito
- **Importante**: Para finance + economics insights

---

### Governo & Open Data

#### Data.gov (EUA)
- **URL**: https://data.gov
- **Datasets**: 300k+ government datasets
- **Categorias**: Climate, health, education, finance
- **API**: Gratuita

#### Dados.gov.br (Brasil)
- **URL**: https://dados.gov.br
- **Datasets**: Dados públicos brasileiros
- **Categorias**: Educação, saúde, economia

#### European Data Portal
- **URL**: https://data.europa.eu
- **Datasets**: EU open data
- **Volume**: 1M+ datasets

---

### Crypto & Web3 (Novo módulo?)

#### CoinGecko
- **URL**: https://www.coingecko.com
- **API**: **100% GRATUITA** (até 50 calls/min) 🎉
- **Dados**: 13k+ cryptocurrencies
- **Métricas**: Price, volume, market cap, developer activity

#### Etherscan
- **URL**: https://etherscan.io
- **API**: Gratuita (limitada)
- **Dados**: Ethereum transactions, smart contracts, gas prices

#### DeFiLlama
- **URL**: https://defillama.com
- **API**: Gratuita
- **Dados**: DeFi protocols, TVL (Total Value Locked)

---

### Business Intelligence

#### Crunchbase (Limited)
- **URL**: https://www.crunchbase.com
- **Free tier**: Basic company data
- **Dados**: Startups, funding, acquisitions
- **Scraping**: Permitido (robots.txt)

#### AngelList
- **URL**: https://angel.co
- **Dados**: Startups, jobs, investors
- **Scraping**: Sim

#### ProductHunt
- **URL**: https://www.producthunt.com
- **API**: GraphQL API (gratuita)
- **Dados**: New products, launches, upvotes

---

### Tech News & Trends

#### Hacker News
- **URL**: https://news.ycombinator.com
- **API**: Firebase API (gratuita)
- **Dados**: Tech news, discussions, trends
- **Útil**: Correlacionar com GitHub trends

#### TechCrunch RSS
- **URL**: https://techcrunch.com/feed
- **Dados**: Tech news, funding announcements
- **Scraping**: RSS feeds

#### Reddit (r/technology, r/startups, etc)
- **API**: Reddit API (gratuita)
- **Dados**: Discussions, trends, sentiment

---

## 📊 Priorização por ROI

### Prioridade 🔥 CRÍTICA (Implementar AGORA)

| Fonte | País/Região | Tipo | ROI | Dificuldade |
|-------|-------------|------|-----|-------------|
| **CNIPA Patents** | 🇨🇳 China | Patentes | ⭐⭐⭐⭐⭐ | 🟡 Média |
| **HKEX IPOs** | 🇨🇳 Hong Kong | Finance | ⭐⭐⭐⭐⭐ | 🟢 Fácil |
| **36Kr Startups** | 🇨🇳 China | Startups | ⭐⭐⭐⭐⭐ | 🟡 Média |
| **PubMed** | 🌍 Global | Research | ⭐⭐⭐⭐⭐ | 🟢 Fácil |
| **EPO Patents** | 🇪🇺 Europa | Patentes | ⭐⭐⭐⭐ | 🟢 Fácil |
| **CoinGecko** | 🌍 Global | Crypto | ⭐⭐⭐⭐ | 🟢 Fácil |

### Prioridade ⭐ ALTA (Next Sprint)

| Fonte | País/Região | Tipo | ROI | Dificuldade |
|-------|-------------|------|-----|-------------|
| CNKI Papers | 🇨🇳 China | Academia | ⭐⭐⭐⭐ | 🔴 Alta |
| SSE/SZSE | 🇨🇳 China | Finance | ⭐⭐⭐⭐ | 🟡 Média |
| bioRxiv | 🌍 Global | Research | ⭐⭐⭐⭐ | 🟢 Fácil |
| Euronext | 🇪🇺 Europa | Finance | ⭐⭐⭐ | 🟡 Média |
| Crunchbase | 🌍 Global | Startups | ⭐⭐⭐⭐ | 🟡 Média |

### Prioridade ➡️ MÉDIA (Backlog)

| Fonte | País/Região | Tipo | ROI | Dificuldade |
|-------|-------------|------|-----|-------------|
| NASSCOM | 🇮🇳 Índia | Tech | ⭐⭐⭐ | 🟡 Média |
| SGX | 🇸🇬 Singapura | Finance | ⭐⭐ | 🟡 Média |
| Data.gov | 🇺🇸 EUA | Open Data | ⭐⭐⭐ | 🟢 Fácil |
| Hacker News | 🌍 Global | News | ⭐⭐ | 🟢 Fácil |

---

## 🚀 Plano de Implementação

### Sprint 1: China Core (2 semanas)

**Objetivo**: Cobrir gaps críticos da China

```bash
# Semana 1
✅ Dia 1-2: collect-cnipa-patents.ts
✅ Dia 3-4: collect-hkex-ipos.ts
✅ Dia 5: collect-china-exchanges.ts (SSE/SZSE basic)

# Semana 2
✅ Dia 1-3: collect-36kr-startups.ts (scraping)
✅ Dia 4-5: collect-cnki-papers.ts (abstracts)
✅ Testing & integration
```

**Entregável**:
- 4 novos collectors funcionando
- Database schema atualizado
- Cron jobs configurados

---

### Sprint 2: Research Global (1 semana)

```bash
✅ Dia 1-2: collect-pubmed.ts
✅ Dia 3: collect-biorxiv.ts
✅ Dia 4: collect-ssrn.ts
✅ Dia 5: Integration & testing
```

---

### Sprint 3: Europa + Crypto (1 semana)

```bash
✅ Dia 1-2: collect-epo-patents.ts
✅ Dia 3: collect-euronext.ts
✅ Dia 4: collect-coingecko.ts
✅ Dia 5: Dashboard updates
```

---

## 💾 Database Schema - Novas Tabelas

### China

```sql
-- Patentes chinesas
CREATE TABLE cnipa_patents (
  id SERIAL PRIMARY KEY,
  application_number VARCHAR(50) UNIQUE,
  title TEXT,
  title_cn TEXT, -- Título em chinês
  title_en TEXT, -- Tradução inglês
  applicant VARCHAR(255),
  inventors TEXT[],
  ipc_classification VARCHAR(50)[],
  filing_date DATE,
  publication_date DATE,
  abstract TEXT,
  abstract_cn TEXT,
  status VARCHAR(50),
  collected_at TIMESTAMP DEFAULT NOW()
);

-- IPOs China (HKEX, SSE, SZSE)
CREATE TABLE china_ipos (
  id SERIAL PRIMARY KEY,
  ticker VARCHAR(20),
  company VARCHAR(255),
  company_cn VARCHAR(255),
  exchange VARCHAR(20), -- 'HKEX' | 'SSE' | 'SZSE'
  sector VARCHAR(100),
  ipo_date DATE,
  ipo_price DECIMAL(12,2),
  amount_raised_usd BIGINT,
  market_cap_usd BIGINT,
  collected_at TIMESTAMP DEFAULT NOW()
);

-- Startups China
CREATE TABLE china_startups (
  id SERIAL PRIMARY KEY,
  company VARCHAR(255),
  company_cn VARCHAR(255),
  sector VARCHAR(100),
  funding_stage VARCHAR(50),
  total_funding_usd BIGINT,
  valuation_usd BIGINT,
  investors TEXT[],
  founded_date DATE,
  city VARCHAR(100),
  description TEXT,
  source VARCHAR(50), -- '36kr' | 'itjuzi'
  collected_at TIMESTAMP DEFAULT NOW()
);

-- Papers chineses (CNKI)
CREATE TABLE cnki_papers (
  id SERIAL PRIMARY KEY,
  cnki_id VARCHAR(100) UNIQUE,
  title TEXT,
  title_cn TEXT,
  authors TEXT[],
  institution VARCHAR(255),
  journal VARCHAR(255),
  year INT,
  abstract TEXT,
  keywords TEXT[],
  citations INT,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

### Research Global

```sql
-- PubMed
CREATE TABLE pubmed_papers (
  id SERIAL PRIMARY KEY,
  pmid VARCHAR(20) UNIQUE,
  title TEXT,
  authors TEXT[],
  journal VARCHAR(255),
  publication_date DATE,
  abstract TEXT,
  mesh_terms TEXT[], -- Medical Subject Headings
  doi VARCHAR(100),
  citations INT,
  collected_at TIMESTAMP DEFAULT NOW()
);

-- bioRxiv/medRxiv
CREATE TABLE biorxiv_preprints (
  id SERIAL PRIMARY KEY,
  doi VARCHAR(100) UNIQUE,
  title TEXT,
  authors TEXT[],
  category VARCHAR(100),
  posted_date DATE,
  abstract TEXT,
  server VARCHAR(20), -- 'biorxiv' | 'medrxiv'
  collected_at TIMESTAMP DEFAULT NOW()
);
```

### Crypto

```sql
CREATE TABLE crypto_data (
  id SERIAL PRIMARY KEY,
  symbol VARCHAR(20),
  name VARCHAR(255),
  price_usd DECIMAL(20,8),
  market_cap_usd BIGINT,
  volume_24h_usd BIGINT,
  change_24h_pct DECIMAL(6,2),
  ath_usd DECIMAL(20,8), -- All-time high
  developer_score DECIMAL(5,2),
  community_score DECIMAL(5,2),
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(symbol, collected_at::DATE)
);
```

---

## 🎯 Correlações Poderosas com Novos Dados

### 1. China Innovation Score

```sql
SELECT
  cp.applicant as company,
  COUNT(DISTINCT cp.application_number) as cnipa_patents,
  COUNT(DISTINCT cs.company) as startup_matches,
  ci.market_cap_usd / 1000000000 as market_cap_billions
FROM cnipa_patents cp
LEFT JOIN china_startups cs ON cp.applicant = cs.company
LEFT JOIN china_ipos ci ON cp.applicant = ci.company
WHERE cp.filing_date > NOW() - INTERVAL '2 years'
GROUP BY cp.applicant, ci.market_cap_usd
HAVING COUNT(DISTINCT cp.application_number) > 10
ORDER BY cnipa_patents DESC;
```

### 2. Global Biotech Pipeline

```sql
-- Correlacionar: PubMed papers → Clinical Trials → Patents → IPOs
SELECT
  p.mesh_terms[1] as disease_area,
  COUNT(DISTINCT p.pmid) as research_papers,
  COUNT(DISTINCT ct.trial_id) as clinical_trials,
  COUNT(DISTINCT pat.patent_number) as patents,
  COUNT(DISTINCT ipo.company) as recent_ipos
FROM pubmed_papers p
LEFT JOIN clinical_trials ct ON p.mesh_terms && ARRAY[ct.condition]
LEFT JOIN patents pat ON p.mesh_terms && pat.classifications
LEFT JOIN china_ipos ipo ON ipo.sector = 'Biotech'
WHERE p.publication_date > '2023-01-01'
GROUP BY disease_area
ORDER BY research_papers DESC;
```

### 3. Tech Stack Global Adoption

```sql
-- Correlacionar: GitHub (Ocidente) + Crypto (Web3) + China Startups
SELECT
  tech_stack,
  github_repos,
  china_startups,
  crypto_projects,
  (github_repos + china_startups + crypto_projects) as total_adoption
FROM (
  SELECT
    g.language as tech_stack,
    COUNT(DISTINCT g.repo_id) as github_repos,
    COUNT(DISTINCT cs.company) FILTER (WHERE cs.description ILIKE '%' || g.language || '%') as china_startups,
    COUNT(DISTINCT c.symbol) FILTER (WHERE c.name ILIKE '%' || g.language || '%') as crypto_projects
  FROM github_repos g
  LEFT JOIN china_startups cs ON TRUE
  LEFT JOIN crypto_data c ON TRUE
  WHERE g.language IS NOT NULL
  GROUP BY g.language
) subq
ORDER BY total_adoption DESC;
```

---

## 📋 Checklist de Implementação

### China 🇨🇳
- [ ] collect-cnipa-patents.ts
- [ ] collect-hkex-ipos.ts
- [ ] collect-sse-szse.ts
- [ ] collect-36kr-startups.ts
- [ ] collect-cnki-papers.ts (abstract only)
- [ ] Tradução automática (Google Translate API)

### Research Global 🌍
- [ ] collect-pubmed.ts
- [ ] collect-biorxiv.ts
- [ ] collect-medrxiv.ts
- [ ] collect-ssrn.ts

### Europa 🇪🇺
- [ ] collect-epo-patents.ts
- [ ] collect-euronext.ts
- [ ] collect-lse.ts

### Crypto 💰
- [ ] collect-coingecko.ts
- [ ] collect-etherscan.ts (smart contracts)
- [ ] collect-defillama.ts (DeFi TVL)

### Business Intelligence 📊
- [ ] collect-crunchbase.ts (free tier)
- [ ] collect-angellist.ts
- [ ] collect-producthunt.ts

### Open Data 🏛️
- [ ] collect-datagov.ts (EUA)
- [ ] collect-dadosgovbr.ts (Brasil)
- [ ] collect-europeandataportal.ts

---

## 💡 Próximos Passos

1. **Aprovar priorização** (China primeiro?)
2. **Implementar Sprint 1** (China Core - 2 semanas)
3. **Setup de tradução** (Google Translate API para conteúdo chinês)
4. **Criar dashboards** específicos para cada região
5. **Alertas multi-região** (China + EUA + Europa)

---

**🚀 Com essas fontes, Sofia Pulse terá cobertura GLOBAL verdadeira e insights impossíveis de obter com fontes isoladas!**

Quer que eu comece implementando os collectors da China (CNIPA, HKEX, 36Kr) agora?
