# 🆓 Ferramentas GRATUITAS para Data Mining - Sofia Pulse

**Objetivo**: Gerar insights dos ~970 registros (29 tabelas) SEM pagar por APIs.

---

## 🎯 Estratégia: 3 Camadas de Análise

### 1. **Análise Estatística Automática** (Sem IA)
   - Correlações, anomalias, tendências
   - Completamente grátis, rápido

### 2. **Machine Learning Local** (PostgreSQL)
   - Clustering, regressão, classificação
   - Roda dentro do PostgreSQL, sem custos

### 3. **LLM Local** (Opcional, para narrativas)
   - Ollama + Llama 3.2 (3B)
   - Roda 100% local, sem internet, grátis

---

## 📊 CAMADA 1: Análise Estatística (Sempre Funciona)

### Ferramentas Python (Já no Setup):

#### **Pandas Profiling** - EDA Automático
```bash
pip install ydata-profiling
```

**O que faz**:
- Gera relatório HTML completo de TODOS os dados
- Correlações automáticas
- Valores faltantes, outliers
- Distribuições, histogramas

**Exemplo**:
```python
from ydata_profiling import ProfileReport

# Carregar TODOS os dados do banco
all_data = pd.read_sql("SELECT * FROM sofia.market_data_brazil", engine)

# Gerar relatório automático
profile = ProfileReport(all_data, title="Sofia Pulse - B3 Analysis")
profile.to_file("reports/b3-analysis.html")
```

**Resultado**: Relatório HTML com 50+ análises automáticas!

---

#### **Sweetviz** - Comparações Automáticas
```bash
pip install sweetviz
```

**O que faz**:
- Compara datasets (ex: B3 vs NASDAQ)
- Análise visual automática
- Detecta correlações entre tabelas

**Exemplo**:
```python
import sweetviz as sv

b3 = pd.read_sql("SELECT * FROM sofia.market_data_brazil", engine)
nasdaq = pd.read_sql("SELECT * FROM sofia.market_data_nasdaq", engine)

# Comparar mercados
report = sv.compare([b3, "B3"], [nasdaq, "NASDAQ"])
report.show_html("reports/b3-vs-nasdaq.html")
```

---

#### **D-Tale** - Exploração Interativa
```bash
pip install dtale
```

**O que faz**:
- Dashboard web interativo
- Filtros, correlações, gráficos
- Exporta insights para código

**Exemplo**:
```python
import dtale

# Carregar dados
data = pd.read_sql("SELECT * FROM sofia.funding_rounds", engine)

# Abrir dashboard interativo
d = dtale.show(data)
d.open_browser()
```

**Acessa**: http://localhost:40000

---

## 🤖 CAMADA 2: Machine Learning no PostgreSQL

### **Apache MADlib** - ML dentro do PostgreSQL

**O que é**: Biblioteca de ML que roda SQL queries diretamente no banco.

**Instalação** (Docker):
```bash
# MADlib já vem em algumas imagens PostgreSQL
# Ou instalar extensão:
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "CREATE EXTENSION madlib;"
```

**Capacidades**:
- Regressão linear/logística
- K-Means clustering
- Decision Trees
- PCA (redução dimensionalidade)
- Análise de séries temporais

**Exemplo - Clustering de Setores**:
```sql
-- Criar tabela de features
CREATE TABLE sector_features AS
SELECT
  sector,
  AVG(change_pct) as avg_performance,
  SUM(volume) as total_volume,
  COUNT(*) as num_companies
FROM sofia.market_data_brazil
GROUP BY sector;

-- Rodar K-Means (3 clusters)
SELECT madlib.kmeans(
  'sector_features',           -- tabela
  'sector_clusters',           -- output
  'avg_performance,total_volume', -- features
  3                            -- num clusters
);

-- Ver resultados
SELECT * FROM sector_clusters;
```

**Resultado**: Setores agrupados por performance/volume (ex: "High Growth", "Stable", "Declining")

---

### **PostgreSQL pg_stat_statements** - Query Analytics

**O que faz**: Rastreia patterns de acesso aos dados.

**Exemplo**:
```sql
-- Ver queries mais lentas (otimizar)
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## 🧠 CAMADA 3: LLM Local (Ollama)

### **Ollama** - Rodar Llama/Mistral localmente

**O que é**: Roda modelos de IA 100% no seu computador, sem internet, grátis.

**Instalação**:
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Baixar modelo Llama 3.2 (3B - leve)
ollama pull llama3.2:3b

# Testar
ollama run llama3.2:3b "Hello!"
```

**Uso no Python**:
```bash
pip install ollama
```

```python
import ollama

# Gerar insights a partir de dados
data_summary = f"""
B3 (Brasil): 64 stocks, média +1.63%
NASDAQ: 24 stocks, média +0.85%
Funding: $17.3B investidos, AI sector lidera

Encontre correlações e oportunidades.
"""

response = ollama.chat(model='llama3.2:3b', messages=[
  {'role': 'user', 'content': data_summary}
])

print(response['message']['content'])
```

**Resultado**: Narrativas e insights gerados localmente!

**Modelos Recomendados**:
- `llama3.2:3b` - Leve, rápido, ~2GB RAM
- `mistral:7b` - Melhor qualidade, ~4GB RAM
- `phi3:mini` - Muito leve, ~2GB RAM

---

## 📦 Extensões PostgreSQL para "Data Lake"

### **FDW (Foreign Data Wrappers)** - Acessar múltiplas fontes

**O que faz**: Conecta PostgreSQL a outras fontes (CSV, MongoDB, APIs) como se fossem tabelas.

**Instalação**:
```bash
docker exec -it sofia-postgres psql -U sofia -d sofia_db
```

```sql
-- Habilitar FDW
CREATE EXTENSION file_fdw;

-- Acessar CSV como tabela
CREATE SERVER csv_server FOREIGN DATA WRAPPER file_fdw;

CREATE FOREIGN TABLE external_data (
  date DATE,
  value NUMERIC
)
SERVER csv_server
OPTIONS (filename '/data/external.csv', format 'csv', header 'true');

-- Query como tabela normal
SELECT * FROM external_data;
```

---

### **pg_analytics** - OLAP no PostgreSQL

**O que é**: Transforma PostgreSQL em data warehouse (DuckDB integrado).

**Instalação**:
```bash
# Adicionar extensão
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "CREATE EXTENSION pg_analytics;"
```

**Uso**:
```sql
-- Queries OLAP otimizadas
SELECT
  sector,
  date_trunc('month', collected_at) as month,
  SUM(amount_usd) as total_funding
FROM sofia.funding_rounds
GROUP BY sector, month
ORDER BY month, total_funding DESC;
```

---

### **TimescaleDB** - Séries Temporais

**O que faz**: Otimiza PostgreSQL para dados de tempo (preços, volumes).

**Instalação**:
```bash
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "CREATE EXTENSION timescaledb;"
```

**Uso**:
```sql
-- Converter tabela para hypertable (otimizada)
SELECT create_hypertable('sofia.market_data_brazil', 'collected_at');

-- Queries otimizadas
SELECT
  time_bucket('1 day', collected_at) AS day,
  ticker,
  AVG(price) as avg_price
FROM sofia.market_data_brazil
WHERE collected_at > NOW() - INTERVAL '30 days'
GROUP BY day, ticker;
```

---

## 🚀 Stack Recomendado (100% Grátis)

### Mínimo (Rápido):
```bash
pip install ydata-profiling sweetviz dtale
```
→ Relatórios HTML automáticos em 5min

### Completo (Melhor):
```bash
# Python
pip install ydata-profiling sweetviz dtale ollama

# PostgreSQL Extensions
docker exec -it sofia-postgres psql -U sofia -d sofia_db
CREATE EXTENSION madlib;      -- ML
CREATE EXTENSION file_fdw;    -- Data lake
CREATE EXTENSION timescaledb; -- Time series

# Ollama (LLM local)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
```

---

## 📋 Workflow Completo

### 1. EDA Automático (Pandas Profiling)
```python
from ydata_profiling import ProfileReport

all_tables = ['market_data_brazil', 'market_data_nasdaq', 'funding_rounds']
for table in all_tables:
    df = pd.read_sql(f"SELECT * FROM sofia.{table}", engine)
    profile = ProfileReport(df, title=f"Sofia - {table}")
    profile.to_file(f"reports/{table}-analysis.html")
```

**Output**: 3 relatórios HTML com análise completa.

---

### 2. Correlações Cross-Table (SQL)
```sql
-- Funding vs Performance
WITH funding_by_sector AS (
  SELECT sector, SUM(amount_usd) as total_funding
  FROM sofia.funding_rounds
  GROUP BY sector
),
performance_by_sector AS (
  SELECT sector, AVG(change_pct) as avg_performance
  FROM sofia.market_data_brazil
  GROUP BY sector
)
SELECT
  f.sector,
  f.total_funding / 1000000000.0 as funding_billions,
  p.avg_performance,
  CORR(f.total_funding, p.avg_performance) OVER () as correlation
FROM funding_by_sector f
JOIN performance_by_sector p ON f.sector = p.sector;
```

---

### 3. Clustering (MADlib)
```sql
-- Agrupar empresas por características
SELECT madlib.kmeans(
  'market_data_brazil',
  'company_clusters',
  'price,volume,change_pct',
  3
);

SELECT cluster_id, COUNT(*), AVG(change_pct)
FROM company_clusters
GROUP BY cluster_id;
```

---

### 4. Narrativa (Ollama)
```python
import ollama

clusters = pd.read_sql("SELECT * FROM company_clusters", engine)
summary = f"Cluster 0: {clusters[0].describe()}\n..."

insights = ollama.chat(model='llama3.2:3b', messages=[
  {'role': 'user', 'content': f'Analise estes clusters:\n{summary}'}
])

print(insights['message']['content'])
```

---

## 💾 Estrutura de Outputs

```
analytics/
├── reports/
│   ├── market_data_brazil-analysis.html      # Pandas Profiling
│   ├── market_data_nasdaq-analysis.html
│   ├── funding_rounds-analysis.html
│   ├── b3-vs-nasdaq-comparison.html          # Sweetviz
│   └── correlation-matrix.png                # Matplotlib
├── insights/
│   ├── sector-clusters.csv                   # K-Means output
│   ├── anomalies-detected.csv                # Outliers
│   ├── time-series-forecast.csv              # Prophet
│   └── ai-insights.txt                       # Ollama narratives
└── notebooks/
    ├── exploratory-analysis.ipynb            # Jupyter
    └── correlation-study.ipynb
```

---

## ⚡ Quick Start (Agora!)

```bash
cd ~/sofia-pulse

# 1. Instalar ferramentas básicas (5min)
source venv-analytics/bin/activate
pip install ydata-profiling sweetviz dtale

# 2. Gerar primeiro relatório (2min)
python3 << 'EOF'
import pandas as pd
from sqlalchemy import create_engine
from ydata_profiling import ProfileReport

engine = create_engine('postgresql://sofia:sofia123strong@localhost:5432/sofia_db')
df = pd.read_sql("SELECT * FROM sofia.market_data_brazil", engine)

profile = ProfileReport(df, title="Sofia Pulse - B3 Analysis")
profile.to_file("analytics/reports/b3-auto-analysis.html")
print("✅ Relatório gerado: analytics/reports/b3-auto-analysis.html")
EOF

# 3. Abrir no browser
xdg-open analytics/reports/b3-auto-analysis.html
```

**Resultado**: Relatório completo de B3 em HTML, 100% grátis, sem IA paga!

---

## 🆚 Comparação: Claude (Pago) vs Grátis

| Feature | Claude API (Pago) | Ferramentas Grátis |
|---------|-------------------|-------------------|
| **EDA** | ❌ Não faz | ✅ Pandas Profiling (melhor) |
| **Correlações** | ✅ Identifica | ✅ SQL + Pandas (igual) |
| **Clustering** | ❌ Não faz | ✅ MADlib + Scikit-learn |
| **Narrativas** | ✅ Excelente | ✅ Ollama (bom, local) |
| **Custo** | $$$$ | **$0** |
| **Privacidade** | ❌ Envia dados | ✅ 100% local |
| **Velocidade** | ~10s/request | ⚡ Instantâneo (SQL/Pandas) |

---

## 🎯 Recomendação Final

**Para Sofia Pulse**, use:

1. **Pandas Profiling** → Relatórios automáticos
2. **SQL queries** → Correlações e agregações
3. **MADlib** → Clustering e ML (se precisar)
4. **Ollama** → Narrativas (opcional, só se tiver GPU/RAM)

**Não precisa de Claude** para maioria dos insights. SQL + Pandas + Profiling já resolve 90%!

---

## 📚 Recursos

- Pandas Profiling: https://github.com/ydataai/ydata-profiling
- Sweetviz: https://github.com/fbdesignpro/sweetviz
- D-Tale: https://github.com/man-group/dtale
- MADlib: https://madlib.apache.org/
- Ollama: https://ollama.com/
- TimescaleDB: https://docs.timescale.com/

---

**Próximo Passo**: Rodar `setup-data-mining-free.sh` (sem dependências pagas)!
