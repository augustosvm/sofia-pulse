# 📊 FONTES DE DADOS GLOBAIS - Sofia Pulse

Guia completo de onde buscar dados REAIS para expandir o sistema.

---

## 🔋 ENERGIA GLOBAL

### **EIA (US Energy Information Administration)** - GRÁTIS ✅
- **URL**: https://www.eia.gov/opendata/
- **API Key**: Grátis (precisa registrar)
- **Dados**:
  - Produção de energia por país (coal, gas, nuclear, hydro, solar, wind)
  - Consumo de energia elétrica
  - Capacidade instalada por tipo
  - Preços de energia
- **Formato**: JSON, CSV
- **Como usar**:
  ```bash
  # Registrar em: https://www.eia.gov/opendata/register.php
  # Adicionar ao .env: EIA_API_KEY=xxx
  ```

### **Our World in Data - Energy** - GRÁTIS ✅
- **URL**: https://github.com/owid/energy-data
- **Dados**:
  - Capacidade renovável por país (GW)
  - Emissões de CO2 por fonte
  - Consumo per capita
  - Mix energético (%)
- **Formato**: CSV direto
- **Como usar**:
  ```bash
  curl https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv -o data/energy-global.csv
  ```

### **IRENA (Renewable Energy Statistics)** - GRÁTIS ✅
- **URL**: https://www.irena.org/Data/Downloads
- **Dados**:
  - Capacidade renovável instalada (solar, wind, hydro, bio, geo) por país
  - Investimentos em renováveis
  - Jobs em energia renovável
- **Formato**: Excel, CSV (precisa baixar manual)

### **IEA World Energy Statistics** - PAGO ❌
- Dados mais completos mas caro (~$1000/ano)
- Alternativa GRÁTIS: IEA Sankey Diagrams (visual, não API)

### **Global Energy Monitor** - GRÁTIS ✅
- **URL**: https://globalenergymonitor.org/projects/global-coal-plant-tracker/
- **Dados**:
  - Usinas de carvão planejadas/construindo/operando
  - Projetos solares e eólicos
  - Gas power plants
- **Formato**: CSV downloads

---

## 🚗 AUTOMÓVEIS & EVs

### **EV-Volumes.com** - GRÁTIS (LIMITED) ⚠️
- **URL**: http://www.ev-volumes.com/
- **Dados**:
  - Vendas de EVs por país e modelo
  - Market share de EVs
  - Top modelos
- **Formato**: Scraping (não tem API)

### **IEA Global EV Outlook** - GRÁTIS ✅
- **URL**: https://www.iea.org/data-and-statistics/data-tools/global-ev-data-explorer
- **Dados**:
  - EV stock por país
  - EV sales
  - Charging infrastructure
- **Formato**: Download Excel

### **BNEF (Bloomberg NEF)** - PAGO ❌
- Melhor fonte mas caro
- Alternativa: Relatórios públicos anuais (grátis)

---

## 🔋 BATERIAS

### **Benchmark Mineral Intelligence** - PAGO ❌
- Melhor dados de baterias mas $$$
- Alternativa: Relatórios grátis trimestrais

### **USGS Mineral Commodity Summaries** - GRÁTIS ✅
- **URL**: https://www.usgs.gov/centers/nmic/lithium-statistics-and-information
- **Dados**:
  - Produção de lítio por país
  - Reservas de cobalto, níquel, lítio
  - Preços de materiais
- **Formato**: PDF, Excel

### **FastMarkets / Platts** - PAGO ❌
- Preços de lítio, cobalto em tempo real
- Alternativa: Trading Economics (alguns dados grátis)

---

## 📱 SMARTPHONES

### **IDC Quarterly Mobile Phone Tracker** - PAGO ❌
- Dados oficiais de vendas
- Alternativa: Press releases (Samsung, Apple, etc)

### **Counterpoint Research** - GRÁTIS (LIMITED) ⚠️
- **URL**: https://www.counterpointresearch.com/
- **Dados**:
  - Market share de smartphones
  - Vendas por região
  - Top vendors
- **Formato**: Web scraping de relatórios

### **Statista** - PAGO ❌
- Gráficos grátis (watermark), dados pagos

---

## 🗄️ DATABASES

### **DB-Engines Ranking** - GRÁTIS ✅
- **URL**: https://db-engines.com/en/ranking
- **Dados**:
  - Ranking de popularidade de databases
  - Trends ao longo do tempo
  - Categorias (relational, NoSQL, graph, etc)
- **Formato**: Web scraping (não tem API)

### **Stack Overflow Survey** - GRÁTIS ✅
- **URL**: https://insights.stackoverflow.com/survey
- **Dados**:
  - Databases mais usados
  - Developer preferences
- **Formato**: CSV download anual

---

## 🤖 EDGE AI / EMBEDDED

### **OpenVINO Benchmark** - GRÁTIS ✅
- **URL**: https://docs.openvino.ai/latest/openvino_docs_performance_benchmarks.html
- **Dados**:
  - Performance de edge devices (Jetson, TPU, etc)

### **MLPerf Inference** - GRÁTIS ✅
- **URL**: https://mlcommons.org/en/inference-edge-20/
- **Dados**:
  - Benchmark de edge AI devices
  - Latency, throughput
- **Formato**: CSV results

---

## 🌍 DADOS GEOPOLÍTICOS + ENERGIA

### **World Bank Open Data** - GRÁTIS ✅
- **URL**: https://data.worldbank.org/
- **Dados**:
  - Electric power consumption (kWh per capita)
  - Access to electricity (%)
  - Renewable energy consumption (% of total)
- **API**: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- **Como usar**:
  ```python
  import wbdata
  indicators = {'EG.USE.ELEC.KH.PC': 'electricity_consumption'}
  df = wbdata.get_dataframe(indicators)
  ```

### **UN Energy Statistics** - GRÁTIS ✅
- **URL**: https://unstats.un.org/unsd/energystats/data/
- **Dados**:
  - Energia primária por fonte
  - Balances energéticos por país
- **Formato**: CSV/Excel downloads

---

## 🎯 FONTES RECOMENDADAS PARA IMPLEMENTAR

### **Prioridade CRÍTICA** (implementar já):
1. **Our World in Data - Energy** (CSV direto, fácil)
2. **EIA API** (grátis, JSON, completo)
3. **DB-Engines** (scraping simples)
4. **World Bank API** (energia, consumo)

### **Prioridade ALTA** (próximos 30 dias):
5. **IRENA** (renewables)
6. **Global Energy Monitor** (projetos)
7. **USGS** (minerals, batteries)
8. **IEA Global EV Outlook** (EVs)

### **Prioridade MÉDIA** (quando tiver budget):
9. **BNEF** (comprar se tiver $$)
10. **IDC** (smartphones, pago)

---

## 🗺️ MAPA GLOBAL - IMPLEMENTAÇÃO

Vou criar `analytics/energy-global-map.py` que gera:

1. **Mapa mundial** com:
   - Círculos coloridos por tipo de energia dominante
   - Tamanho = capacidade instalada (GW)
   - Cor = % renovável vs fóssil

2. **Top Countries**:
   - Por capacidade renovável
   - Por investimento em baterias
   - Por adoção de EVs

3. **Trends**:
   - Crescimento de solar/wind YoY
   - Nuclear vs renewables
   - Grid storage deployments

**Bibliotecas Python**:
```bash
pip install plotly geopandas matplotlib seaborn pandas wbdata
```

---

## 📝 PROXIMOS PASSOS

1. **Criar collectors**:
   - `scripts/collect-energy-eia.ts` (EIA API)
   - `scripts/collect-energy-owid.py` (Our World in Data CSV)
   - `scripts/collect-db-ranking.py` (DB-Engines scraper)

2. **Criar tabelas**:
   - `energy_global` (países, capacidade por tipo, consumo)
   - `ev_market` (vendas, market share, modelos)
   - `battery_materials` (lítio, cobalto, preços)
   - `database_ranking` (PostgreSQL, MongoDB, etc trends)

3. **Gerar mapas**:
   - `analytics/energy-global-map.py` → gera PNG/HTML interativo
   - Incluir no email como anexo

---

**IMPORTANTE**: Muitas fontes premium (BNEF, IDC, Statista) são PAGAS. Para começar, vamos usar fontes GRATUITAS e depois evoluir.
