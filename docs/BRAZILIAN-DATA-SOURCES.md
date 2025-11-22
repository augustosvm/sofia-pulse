# 🇧🇷 Brazilian Data Sources - Complete Reference

**Last Updated**: 2025-11-22
**Status**: Documented and Partially Implemented

---

## 📊 Overview

This document catalogs all Brazilian data sources investigated for Sofia Pulse, including official APIs, open data portals, and industry federation data.

---

## ✅ IMPLEMENTED - Working APIs

### 1. BACEN SGS API (Banco Central do Brasil)
- **Status**: ✅ Implemented
- **File**: `scripts/collect-bacen-sgs.py`
- **URL**: https://api.bcb.gov.br/dados/serie/
- **Auth**: None required (public API)
- **Data**:
  - Selic (series 432) - Daily interest rate
  - IPCA (series 433) - Monthly inflation
  - Dollar exchange (series 1) - Daily
  - PIB mensal (series 4189) - Monthly GDP
  - IGP-M (series 11) - General inflation
  - Unemployment (series 4390)
  - International reserves (series 13522)
- **Use Cases**: Correlate Selic with startup funding, track inflation vs tech salaries

### 2. IBGE SIDRA API
- **Status**: ✅ Implemented (fixed)
- **File**: `scripts/collect-ibge-api.py`
- **URL**: https://apisidra.ibge.gov.br/
- **Auth**: None required (public API)
- **Data**:
  - PIB (Table 1737)
  - IPCA inflation (Table 6381)
  - Unemployment PNAD (Table 6784)
  - Industrial production (Table 6385)
  - Average income (Table 6786)
- **Use Cases**: Economic indicators for expansion analysis

### 3. IPEA API
- **Status**: ✅ Implemented
- **File**: `scripts/collect-ipea-api.py`
- **URL**: http://ipeadata.gov.br/api/
- **Auth**: None required
- **Data**:
  - Historical series since 1940s
  - IPC-A inflation
  - Unemployment rate
  - Real average income
- **Use Cases**: Long-term trend analysis, historical comparisons

---

## 🔧 READY TO IMPLEMENT - Open Data Platforms

### 4. Base dos Dados (basedosdados.org)
- **Status**: 🔧 Collector created, needs BigQuery setup
- **File**: `scripts/collect-basedosdados.py`
- **URL**: https://basedosdados.org/
- **Auth**: Google Cloud Project (free tier: 1TB/month)
- **Installation**: `pip install basedosdados pandas`
- **Data Available**:
  - **FIRJAN IFDM** - Municipal Development Index (all 5,500+ municipalities)
  - **FIRJAN IFGF** - Fiscal Management Index
  - **PIB Municipal** - GDP by municipality
  - **PIB Estadual** - GDP by state
  - **IPCA** - Inflation by month
  - **BACEN Series** - Central Bank time series
  - Hundreds more datasets!
- **Setup**:
  ```bash
  # 1. Create Google Cloud project (free)
  # 2. Enable BigQuery API
  # 3. Set environment variable
  export GOOGLE_CLOUD_PROJECT="your-project-id"
  # 4. Run collector
  python scripts/collect-basedosdados.py
  ```
- **Use Cases**:
  - Municipal development for expansion decisions
  - Fiscal health of cities for investment
  - Complete economic picture of Brazil

### 5. Portal Brasileiro de Dados Abertos
- **Status**: ⏳ Not implemented
- **URL**: https://dados.gov.br/
- **Auth**: None
- **Data**: Government datasets (education, health, infrastructure)
- **Format**: CSV, JSON, XML

### 6. Brasil.IO
- **Status**: ⏳ Not implemented
- **URL**: https://brasil.io/datasets/
- **Auth**: None
- **Data**: Curated Brazilian datasets, company registrations
- **Format**: CSV, API

---

## 🏭 INDUSTRY FEDERATIONS

### 7. CNI - Confederação Nacional da Indústria
- **Status**: ⚠️ No public API (requires partnership)
- **URLs**:
  - Portal: https://www.portaldaindustria.com.br/cni/
  - Statistics: https://www.portaldaindustria.com.br/cni/estatisticas/
  - Industry Profile: https://perfildaindustria.portaldaindustria.com.br/
  - Observatory: https://www.portaldaindustria.com.br/canais/observatorio-nacional-da-industria/
- **Data Available** (via dashboards, not API):
  - Industrial Indicators (monthly)
  - Business Confidence Index
  - Industrial Capacity Utilization
  - Sectoral data
- **Access**: Data loads via internal JSON endpoints (not documented)
- **Alternative**: Use IBGE industrial production data instead

### 8. FIESP - Federação das Indústrias de São Paulo
- **Status**: ⚠️ Restricted access (association members only)
- **URLs**:
  - Portal: https://www.fiesp.com.br/
  - Data Platform: https://inteligencia-dados.fiesp.com.br/
  - Economic Indices: https://inteligencia-dados.fiesp.com.br/indices-economicos/
- **Data Available**:
  - São Paulo industrial indicators
  - Economic conjuncture
  - Foreign trade data
  - Market intelligence
- **Access**: Full access requires association membership
- **Alternative**: Use IBGE São Paulo state data

### 9. FIRJAN - Federação das Indústrias do Rio de Janeiro
- **Status**: ✅ Data available via Base dos Dados
- **URLs**:
  - Portal: https://www.firjan.com.br/
  - IFDM: https://www.firjan.com.br/ifdm/
  - Open Data: https://firjan.com.br/sesi-transparencia/transparencia/dados-abertos/
- **Data Available**:
  - **IFDM** - Development index (education, health, income)
  - **IFGF** - Fiscal management index
- **Access**: Via Base dos Dados (basedosdados.org)
- **Use Cases**: Best for expansion/investment decisions by municipality

### 10. Other State Federations
| Federation | State | Public API | Notes |
|------------|-------|------------|-------|
| FIEMG | Minas Gerais | ❌ | PDFs and reports only |
| FIERJ | Rio de Janeiro | ❌ | Same as FIEMG |
| FIESC | Santa Catarina | ❌ | Industrial Guide (cadastral) |
| FIEP | Paraná | ❌ | Reports only |
| FIEC | Ceará | ❌ | observatorio.ind.br (no API) |

---

## 🔒 REQUIRES SPECIAL ACCESS

### 11. MDIC ComexStat (Foreign Trade)
- **Status**: ⚠️ API deprecated/changed
- **Old URL**: http://api.comexstat.mdic.gov.br/
- **Alternative**: Use Portal Siscomex or Base dos Dados
- **Data**: Import/export by product, country, state, port

### 12. B3 (Brazilian Stock Exchange)
- **Status**: ⚠️ Requires certification
- **URL**: https://www.b3.com.br/
- **Data**: Stock prices, market data
- **Alternative**: Alpha Vantage or Yahoo Finance

---

## 📈 RECOMMENDED IMPLEMENTATION PRIORITY

### Phase 1 - Quick Wins (Done) ✅
1. ✅ BACEN SGS - Selic, IPCA, Dollar
2. ✅ IBGE SIDRA - PIB, unemployment, production
3. ✅ IPEA - Historical series

### Phase 2 - High Value (Next)
4. 🔧 Base dos Dados - FIRJAN indices, municipal data
   - Requires: Google Cloud project setup
   - Impact: Complete municipal analysis for expansion

### Phase 3 - Future Enhancements
5. ⏳ Brasil.IO - Company registrations
6. ⏳ Portal Dados Abertos - Government datasets

---

## 🔗 Quick Reference Links

### Official APIs (Public)
- BACEN: https://api.bcb.gov.br/dados/serie/
- IBGE SIDRA: https://apisidra.ibge.gov.br/
- IPEA: http://ipeadata.gov.br/api/

### Open Data Platforms
- Base dos Dados: https://basedosdados.org/
- Dados.gov.br: https://dados.gov.br/
- Brasil.IO: https://brasil.io/

### Industry Federations (No API)
- CNI: https://www.portaldaindustria.com.br/cni/estatisticas/
- FIESP: https://inteligencia-dados.fiesp.com.br/
- FIRJAN: https://www.firjan.com.br/ifdm/

---

## 💡 Use Cases for Sofia Pulse

### For Expansion Analysis
```
FIRJAN IFDM + PIB Municipal + Funding Data
= Best cities for tech companies to expand
```

### For Economic Forecasting
```
Selic + IPCA + Dollar Exchange + Startup Funding
= Predict investment cycles
```

### For Talent Decisions
```
Unemployment Rate + Average Income + Education Index
= Best cities for hiring tech talent
```

### For Investment Timing
```
Industrial Production + Business Confidence + GDP Growth
= Optimal timing for market entry
```

---

## 🛠️ Setup Instructions

### 1. Run existing collectors
```bash
cd ~/sofia-pulse
bash collect-brazilian-apis.sh
```

### 2. Setup Base dos Dados (optional but recommended)
```bash
# Install package
pip install basedosdados pandas

# Create Google Cloud project (free)
# 1. Go to: https://console.cloud.google.com/
# 2. Create new project
# 3. Enable BigQuery API
# 4. Copy project ID

# Set environment variable
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Run collector
python scripts/collect-basedosdados.py
```

### 3. Add to crontab
```bash
# Add Brazilian APIs to collection schedule
# Run after IBGE/BACEN (data released monthly)
0 12 1 * * cd ~/sofia-pulse && bash collect-brazilian-apis.sh
```

---

**Document maintained by Sofia Pulse Team**
**Last verified**: 2025-11-22
