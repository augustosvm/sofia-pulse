# 📊 Sofia Pulse - Dados REAIS e Acessíveis AGORA

Foco em fontes que **EXISTEM**, são **GRATUITAS** e podemos **COLETAR HOJE**.

---

## 🎯 Princípio: Dados ou Não Vale Nada

**Regra de Ouro**: Só entra na lista se:
- ✅ API/scraping funciona HOJE
- ✅ 100% gratuito OU freemium suficiente
- ✅ Dados úteis para ML/insights
- ✅ Podemos coletar automaticamente

---

## 🏭 Indicadores Econômicos Alternativos (OURO para ML!)

### 1. **Produção de Papelão** (Sua ideia! 🎯)

#### Por que é GENIAL:
- Leading indicator (antecede PIB em 2-3 meses)
- E-commerce = papelão
- Manufatura = embalagens
- Dados disponíveis ANTES do PIB oficial

#### Fontes REAIS:

**EUA - American Forest & Paper Association (AF&PA)**
- **URL**: https://www.afandpa.org/statistics-resources
- **Dados**: Monthly containerboard production
- **Acesso**: Public reports (PDF/Excel)
- **Histórico**: 20+ anos
- **Frequência**: Mensal

**Europa - FEFCO (European Federation of Corrugated Board)**
- **URL**: https://www.fefco.org
- **Dados**: European corrugated production
- **Acesso**: Quarterly reports
- **Cobertura**: 24 países EU

**China - China Paper Association**
- **URL**: http://www.chinappi.org (inglês limitado)
- **Dados**: Cardboard/corrugated production
- **Scraping**: Reports públicos

**Brasil - ABPO (Assoc. Brasileira do Papelão Ondulado)**
- **URL**: http://www.abpo.org.br
- **Dados**: Produção nacional de papelão
- **Acesso**: Estatísticas públicas

**Implementação**:
```typescript
// scripts/collect-cardboard-production.ts
interface CardboardData {
  country: string;
  period: string; // 'YYYY-MM'
  production_tons: number;
  yoy_change_pct: number;
  source: string;
}

// Coletar de AF&PA (EUA), FEFCO (EU), China, Brasil
// Correlacionar com:
// - GDP growth
// - Stock market indices
// - E-commerce sales
// - Manufacturing PMI
```

---

### 2. **Consumo de Energia Elétrica**

#### Por que funciona:
- Indústrias = grandes consumidores
- Dados quase real-time
- Correlação 0.9+ com atividade industrial

#### Fontes REAIS:

**EUA - EIA (Energy Information Administration)**
- **URL**: https://www.eia.gov/opendata/
- **API**: **100% GRATUITA** 🎉
- **Dados**: Hourly electricity consumption por estado
- **Real-time**: Delay de 2 horas!

**Europa - ENTSO-E (European Network TSOs)**
- **URL**: https://transparency.entsoe.eu
- **API**: RESTful API (grátis)
- **Dados**: Real-time load, generation

**China - China Electricity Council**
- **URL**: http://www.cec.org.cn
- **Dados**: Monthly electricity consumption
- **Acesso**: Public statistics

**Brasil - ONS (Operador Nacional do Sistema)**
- **URL**: http://www.ons.org.br
- **Dados**: Carga horária do sistema
- **API**: Alguns dados via API

```typescript
// scripts/collect-electricity-consumption.ts
// Real-time proxy de atividade industrial
```

---

### 3. **Tráfego Portuário** (Comércio Global)

**AIS (Automatic Identification System) - GRÁTIS!**
- **URL**: https://www.marinetraffic.com
- **API**: Limited free tier
- **Dados**: Ship positions, port calls
- **Insights**: Trade flows, supply chain

**Port Statistics**:
- Port of Los Angeles (EUA)
- Port of Rotterdam (Europa)
- Port of Shanghai (China)
- Port of Santos (Brasil)

Todos publicam estatísticas mensais GRATUITAS!

```typescript
// scripts/collect-port-traffic.ts
// Container movements = trade volumes
```

---

### 4. **Tráfego Aéreo** (Atividade Econômica)

**FlightRadar24**
- **API**: Freemium (limited calls grátis)
- **Dados**: Flight count por região
- **Proxy**: Business activity, tourism

**IATA - Air Cargo Stats**
- **URL**: https://www.iata.org/en/publications/economics/
- **Dados**: Air freight volumes
- **Acesso**: Some free reports

---

### 5. **Preços de Commodities** (Inflação, Supply Chain)

**World Bank - Commodity Prices**
- **URL**: https://www.worldbank.org/commodities
- **API**: World Bank API (grátis)
- **Dados**: 70+ commodities
- **Frequência**: Monthly

**FRED (Federal Reserve Economic Data)**
- **URL**: https://fred.stlouisfed.org
- **API**: **100% GRATUITA** 🎉
- **Dados**: 800k+ séries econômicas
- **Exemplos**: Oil, copper, steel, lumber prices

```typescript
// scripts/collect-commodity-prices.ts
// Cobre = leading indicator industrial
// Petróleo = custo de transporte
// Aço = construção
```

---

## 🌍 Dados GLOBAIS Acessíveis HOJE

### China (Gap CRÍTICO!)

#### ✅ O Que FUNCIONA Hoje:

**1. Patentes - CNIPA/WIPO**
- **URL**: https://patentscope.wipo.int
- **API**: WIPO API (gratuita)
- **Dados**: Chinese patents com tradução inglês!
- **Volume**: 1.5M+ patents/ano

```typescript
// scripts/collect-wipo-china-patents.ts
// WIPO tem dados chineses TRADUZIDOS!
```

**2. Trade Data - UN Comtrade**
- **URL**: https://comtrade.un.org
- **API**: Comtrade API (gratuita)
- **Dados**: China imports/exports detalhados
- **Categorias**: HS codes (10k+ produtos)

**3. GitHub China**
- **URL**: https://github.com
- **API**: GitHub API
- **Filtro**: `location:China` ou `location:Beijing`
- **Dados**: Chinese developers, repos

**4. Research - arXiv (Chinese authors)**
- **Filtro**: Authors com afiliação chinesa
- **Já temos**: Script collect-arxiv.ts
- **Adicionar**: Author affiliation parsing

**5. Crypto China** (antes do ban)**
- **Dados históricos**: Chinese exchanges, mining pools
- **CoinGecko**: Historical data

---

### Europa

#### ✅ APIs Gratuitas Funcionando:

**1. Eurostat**
- **URL**: https://ec.europa.eu/eurostat
- **API**: REST API (gratuita)
- **Dados**: GDP, unemployment, trade, todos os países EU
- **Frequência**: Quarterly/Monthly

**2. ECB (European Central Bank)**
- **URL**: https://sdw.ecb.europa.eu
- **API**: Statistical Data Warehouse API
- **Dados**: Interest rates, inflation, money supply

**3. EPO Patents**
- **URL**: https://www.epo.org
- **API**: OPS (Open Patent Services) - GRÁTIS
- **Dados**: European patents

---

### Índia

**1. RBI (Reserve Bank of India)**
- **URL**: https://www.rbi.org.in
- **API**: Database on Indian Economy (DBIE)
- **Dados**: Macro indicators, financials

**2. Indian Patent Office**
- **URL**: https://ipindiaservices.gov.in
- **Dados**: Indian patents
- **Scraping**: Public search

---

## 📊 Datasets Governamentais (Tesouro de Dados!)

### World Bank Open Data
- **URL**: https://data.worldbank.org
- **API**: World Bank API (gratuita)
- **Dados**:
  - GDP de 200+ países
  - Population, poverty, education
  - Health indicators
  - Infrastructure
- **Histórico**: 60+ anos!

### IMF (International Monetary Fund)
- **URL**: https://data.imf.org
- **API**: IMF Data API
- **Dados**:
  - Economic indicators globais
  - Exchange rates
  - Balance of payments

### OECD Data
- **URL**: https://data.oecd.org
- **API**: SDMX REST API
- **Dados**: 38 países desenvolvidos
  - Economic outlook
  - Science & tech indicators
  - Patents, R&D spending

### UN Data
- **URL**: http://data.un.org
- **API**: UN Data API
- **Dados**:
  - Population demographics
  - Trade (Comtrade)
  - Development indicators

---

## 🎓 Research - Além do ArXiv

### PubMed Central (PMC)
- **URL**: https://www.ncbi.nlm.nih.gov/pmc/
- **API**: E-utilities API (grátis)
- **Dados**: 8M+ full-text papers
- **Foco**: Biomedicina
- **Diferença do PubMed**: Full text vs abstracts

### CORE
- **URL**: https://core.ac.uk
- **API**: CORE API v3 (gratuita)
- **Dados**: 200M+ research papers open access
- **Cobertura**: Global

### OpenAlex
- **URL**: https://openalex.org
- **API**: **100% GRATUITA, SEM LIMITES** 🎉🎉🎉
- **Dados**:
  - 250M+ papers
  - Authors, institutions, citations
  - **Substitui**: Microsoft Academic (descontinuado)
- **Cobertura**: Melhor que ArXiv + PubMed juntos!

```typescript
// scripts/collect-openalex.ts
// Dados de papers WORLDWIDE
// Substituir/complementar ArXiv
```

---

## 💰 Finance - Além de B3/NASDAQ

### Yahoo Finance (Unofficial API)
- **URL**: https://finance.yahoo.com
- **Library**: yfinance (Python) ou yahoo-finance2 (npm)
- **Dados**: Stock prices worldwide **GRÁTIS**
- **Exchanges**: NYSE, NASDAQ, LSE, Euronext, HKEX, etc.

```typescript
// scripts/collect-yahoo-finance-global.ts
// Pegar stocks de TODAS exchanges
```

### Alpha Vantage (Já temos key!)
- **Forex**: Currency pairs
- **Crypto**: Bitcoin, Ethereum, etc.
- **Commodities**: Gold, oil, silver

### CoinMarketCap
- **URL**: https://coinmarketcap.com
- **API**: Free tier (10k calls/month)
- **Dados**: 20k+ cryptocurrencies
- **Melhor que CoinGecko**: Mais metadata

---

## 🏢 Business Data Acessível

### OpenCorporates
- **URL**: https://opencorporates.com
- **API**: Freemium (basic grátis)
- **Dados**: 200M+ companies worldwide
- **Países**: 140+

### Companies House (UK)
- **URL**: https://www.gov.uk/government/organisations/companies-house
- **API**: **100% GRATUITA**
- **Dados**: ALL UK companies
  - Filings, directors, financials

### SEC EDGAR (USA)
- **URL**: https://www.sec.gov/edgar
- **API**: EDGAR API
- **Dados**: Public companies filings (10-K, 10-Q, 8-K)
- **Scraping**: Permitido

---

## 📈 Dados Econômicos Real-Time

### FRED (Federal Reserve)
- **Categorias**:
  - Employment (nonfarm payrolls)
  - Inflation (CPI, PPI)
  - Housing starts
  - Retail sales
  - Consumer sentiment
- **API**: Grátis, sem limite!

### Trading Economics
- **URL**: https://tradingeconomics.com
- **API**: Freemium (limited grátis)
- **Dados**: Economic indicators 196 países
- **Calendar**: Economic events schedule

---

## 🔄 Plano de Implementação REAL

### Fase 1: Indicadores Econômicos (1 semana)

```bash
# Prioridade máxima - dados que não temos NADA
✅ collect-cardboard-production.ts (EUA, EU, China, Brasil)
✅ collect-electricity-consumption.ts (EIA API)
✅ collect-commodity-prices.ts (World Bank + FRED)
✅ collect-port-traffic.ts (LA, Rotterdam, Shanghai, Santos)
```

**Valor**: Leading indicators para TUDO (stocks, GDP, etc)

---

### Fase 2: China Coverage (1 semana)

```bash
# Fechar gap China
✅ collect-wipo-china-patents.ts (WIPO tem tradução!)
✅ collect-comtrade-china.ts (UN Comtrade - trade data)
✅ collect-github-china.ts (filtrar location:China)
✅ collect-yahoo-finance-hkex.ts (Hong Kong stocks)
```

**Valor**: Cobertura China sem precisar ler chinês!

---

### Fase 3: Research Global (1 semana)

```bash
# Melhor cobertura research
✅ collect-openalex.ts (250M papers - MELHOR FONTE!)
✅ collect-pubmed-central.ts (full text biomédica)
✅ collect-core.ts (200M papers open access)
```

**Valor**: ML precisa de MUITOS papers para treinar

---

### Fase 4: Macro Global (1 semana)

```bash
# Macro indicators todos países
✅ collect-worldbank.ts (GDP, demographics, etc)
✅ collect-imf.ts (economic indicators)
✅ collect-eurostat.ts (Europa detalhado)
✅ collect-fred.ts (EUA real-time)
```

**Valor**: Contexto econômico para TODOS os outros dados

---

## 🎯 Correlações Poderosas com Novos Dados

### 1. Papelão → PIB → Stocks (Leading Indicator Chain)

```sql
-- Predizer GDP growth 2-3 meses antes!
SELECT
  c.country,
  c.period,
  c.production_tons,
  c.yoy_change_pct as cardboard_growth,
  LEAD(wb.gdp_growth, 2) OVER (PARTITION BY c.country ORDER BY c.period) as gdp_2months_later,
  LEAD(s.index_return, 3) OVER (PARTITION BY c.country ORDER BY c.period) as stocks_3months_later
FROM cardboard_production c
LEFT JOIN worldbank_gdp wb ON c.country = wb.country AND c.period = wb.period
LEFT JOIN stock_indices s ON c.country = s.country
WHERE c.period > '2020-01-01'
ORDER BY c.country, c.period;

-- ML model: Cardboard YoY → Predict GDP growth
```

### 2. Energia + Port Traffic → Industrial Activity

```sql
-- Detectar recessão ANTES dos dados oficiais
SELECT
  e.country,
  e.period,
  e.consumption_change_pct as electricity_change,
  p.container_volume_change_pct as port_change,
  (e.consumption_change_pct + p.container_volume_change_pct) / 2 as combined_indicator,
  CASE
    WHEN combined_indicator < -5 THEN 'Recession Risk'
    WHEN combined_indicator < 0 THEN 'Slowdown'
    WHEN combined_indicator < 3 THEN 'Stable'
    ELSE 'Expansion'
  END as economic_signal
FROM electricity_consumption e
JOIN port_traffic p ON e.country = p.country AND e.period = p.period;
```

### 3. Patents (China + EUA + EU) → Tech Leadership

```sql
-- Quem está liderando em AI/5G/Batteries?
SELECT
  technology_area,
  SUM(CASE WHEN patent_office = 'CNIPA' THEN 1 ELSE 0 END) as china_patents,
  SUM(CASE WHEN patent_office = 'USPTO' THEN 1 ELSE 0 END) as usa_patents,
  SUM(CASE WHEN patent_office = 'EPO' THEN 1 ELSE 0 END) as eu_patents
FROM (
  SELECT 'CNIPA' as patent_office, classifications as tech FROM cnipa_patents
  UNION ALL
  SELECT 'USPTO', classifications FROM patents
  UNION ALL
  SELECT 'EPO', classifications FROM epo_patents
) all_patents,
UNNEST(tech) as technology_area
WHERE technology_area IN ('G06N', 'H04W', 'H01M') -- AI, 5G, Batteries
GROUP BY technology_area;
```

### 4. Research → Startups → IPOs (Innovation Pipeline)

```sql
-- Da pesquisa ao mercado: quanto tempo leva?
WITH research_topics AS (
  SELECT
    UNNEST(keywords) as topic,
    MIN(publication_date) as first_paper_date
  FROM openalex_papers
  WHERE publication_date > '2015-01-01'
  GROUP BY topic
),
startup_activity AS (
  SELECT
    sector as topic,
    MIN(founded_date) as first_startup_date
  FROM china_startups
  UNION ALL
  SELECT sector, MIN(announced_date) FROM funding_rounds
),
ipo_activity AS (
  SELECT
    sector as topic,
    MIN(ipo_date) as first_ipo_date
  FROM china_ipos
  UNION ALL
  SELECT sector, MIN(collected_at) FROM market_data_nasdaq
)
SELECT
  r.topic,
  r.first_paper_date,
  s.first_startup_date,
  i.first_ipo_date,
  s.first_startup_date - r.first_paper_date as research_to_startup_days,
  i.first_ipo_date - s.first_startup_date as startup_to_ipo_days
FROM research_topics r
LEFT JOIN startup_activity s ON r.topic = s.topic
LEFT JOIN ipo_activity i ON s.topic = i.topic
ORDER BY research_to_startup_days;
```

---

## 📊 Database Schema - Novos Indicadores

```sql
-- Papelão (Leading Indicator!)
CREATE TABLE cardboard_production (
  id SERIAL PRIMARY KEY,
  country VARCHAR(100),
  period VARCHAR(7), -- YYYY-MM
  production_tons BIGINT,
  yoy_change_pct DECIMAL(6,2),
  source VARCHAR(100), -- 'AFPA' | 'FEFCO' | etc
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(country, period)
);

-- Energia
CREATE TABLE electricity_consumption (
  id SERIAL PRIMARY KEY,
  country VARCHAR(100),
  region VARCHAR(100), -- estado/província
  period VARCHAR(7),
  consumption_mwh BIGINT,
  yoy_change_pct DECIMAL(6,2),
  source VARCHAR(50),
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(country, region, period)
);

-- Portos
CREATE TABLE port_traffic (
  id SERIAL PRIMARY KEY,
  port_name VARCHAR(255),
  country VARCHAR(100),
  period VARCHAR(7),
  container_teu BIGINT, -- Twenty-foot Equivalent Units
  cargo_tons BIGINT,
  yoy_change_pct DECIMAL(6,2),
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(port_name, period)
);

-- Commodities
CREATE TABLE commodity_prices (
  id SERIAL PRIMARY KEY,
  commodity VARCHAR(100), -- 'copper' | 'oil_brent' | 'steel' | etc
  period VARCHAR(7),
  price_usd DECIMAL(12,2),
  unit VARCHAR(20), -- 'per_ton' | 'per_barrel' | etc
  yoy_change_pct DECIMAL(6,2),
  source VARCHAR(50),
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(commodity, period)
);

-- World Bank / IMF / OECD
CREATE TABLE macro_indicators (
  id SERIAL PRIMARY KEY,
  country VARCHAR(100),
  indicator VARCHAR(100), -- 'GDP_growth' | 'unemployment' | 'inflation' | etc
  period VARCHAR(7),
  value DECIMAL(15,2),
  unit VARCHAR(50),
  source VARCHAR(50), -- 'WorldBank' | 'IMF' | 'OECD'
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(country, indicator, period, source)
);

-- OpenAlex (250M papers!)
CREATE TABLE openalex_papers (
  id SERIAL PRIMARY KEY,
  openalex_id VARCHAR(50) UNIQUE,
  doi VARCHAR(100),
  title TEXT,
  publication_date DATE,
  authors TEXT[],
  institutions TEXT[],
  countries VARCHAR(10)[],
  concepts TEXT[], -- AI-generated topics
  citations_count INT,
  referenced_works TEXT[],
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

## ✅ Checklist - Dados PRIORITÁRIOS

### Econômicos (Para ML!)
- [ ] Cardboard production (EUA, EU, China, Brasil)
- [ ] Electricity consumption (real-time via EIA)
- [ ] Port traffic (top 10 portos mundiais)
- [ ] Commodity prices (FRED API - cobre, petróleo, aço)
- [ ] FRED indicators (50+ series econômicas EUA)

### China (Gap crítico!)
- [ ] WIPO patents (chineses com tradução)
- [ ] UN Comtrade (trade data China)
- [ ] GitHub China (location filter)
- [ ] Yahoo Finance HKEX (Hong Kong stocks)

### Research (Para ML!)
- [ ] OpenAlex (250M papers - MELHOR FONTE)
- [ ] PubMed Central (full text biomédica)
- [ ] CORE (200M papers open access)

### Macro Global
- [ ] World Bank (GDP, demographics)
- [ ] IMF (economic indicators)
- [ ] Eurostat (Europa)
- [ ] OECD (países desenvolvidos)

---

**🎯 Com esses dados, teremos:**
- Leading indicators econômicos (2-3 meses de antecedência!)
- Cobertura China (fechando gap ENORME)
- 250M+ papers para ML treinar
- Macro indicators de 200+ países

**Próximo passo**: Implementar Fase 1 (Indicadores Econômicos) esta semana?
