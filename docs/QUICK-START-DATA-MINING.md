# 🚀 Quick Start - Data Mining com Gemini AI

**Setup completo em 5 minutos** para análise de TODOS os dados do Sofia Pulse!

---

## ⚡ Setup Rápido (1 comando)

```bash
cd ~/sofia-pulse
./setup-data-mining.sh
```

**O que instala**:
- ✅ Pandas, NumPy, SciPy (data analysis)
- ✅ Scikit-learn (ML, clustering)
- ✅ Matplotlib, Seaborn, Plotly (visualizações)
- ✅ **Google Gemini SDK** (AI insights - 10x mais barato que Claude!)
- ✅ **Pandas Profiling** (relatórios automáticos - GRÁTIS!)
- ✅ **Sweetviz** (comparações - GRÁTIS!)
- ✅ **D-Tale** (dashboard interativo - GRÁTIS!)
- ✅ Jupyter Lab (notebooks)
- ✅ PostgreSQL connectors

**Tempo**: ~3-5 minutos

---

## 🔑 Configurar Gemini API Key (GRÁTIS!)

### 1. Obter API Key:
https://aistudio.google.com/app/apikey

**Tier grátis**:
- ✅ 15 requests/min (Gemini Flash)
- ✅ 1,500 requests/dia
- ✅ Sem cartão de crédito necessário

### 2. Adicionar ao .env:

```bash
echo 'GEMINI_API_KEY=sua_key_aqui' >> ~/.env
```

**Pronto!** Já pode usar AI insights gratuitamente.

---

## 📊 Opção 1: Jupyter Notebook (Recomendado)

### Iniciar Jupyter:

```bash
cd ~/sofia-pulse
source venv-analytics/bin/activate
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser
```

**Acesso**:
```
http://seu-servidor:8888
```

**Senha/Token**: Aparece no terminal após rodar comando acima.

### Abrir Notebook:

```
analytics/notebooks/data-mining-gemini.ipynb
```

**O que faz**:
1. ✅ Carrega TODOS os ~970 registros do banco
2. ✅ Calcula correlações entre funding e performance
3. ✅ Clustering de setores (K-Means)
4. ✅ Detecta anomalias (Z-score)
5. ✅ **Gera insights com Gemini AI** (narrativas automáticas)
6. ✅ Cria relatórios HTML interativos
7. ✅ Exporta tudo para CSV

**Tempo de execução**: ~2-3 minutos

---

## 📈 Opção 2: EDA Rápido (Sem IA)

Se quiser apenas **relatórios automáticos** sem usar IA:

```bash
cd ~/sofia-pulse
source venv-analytics/bin/activate

python3 << 'EOF'
import pandas as pd
from sqlalchemy import create_engine
from ydata_profiling import ProfileReport

# Conectar
engine = create_engine('postgresql://sofia:sofia123strong@localhost:5432/sofia_db')

# Carregar dados
df_b3 = pd.read_sql('SELECT * FROM sofia.market_data_brazil', engine)

# Gerar relatório automático
profile = ProfileReport(df_b3, title="Sofia Pulse - B3 Analysis")
profile.to_file('analytics/reports/b3-analysis.html')

print("✅ Relatório: analytics/reports/b3-analysis.html")
EOF
```

**Output**: Relatório HTML com 50+ análises automáticas!

**Tempo**: ~1 minuto

---

## 🤖 Opção 3: Apenas Gemini Insights

Se quiser apenas **insights de IA** dos dados existentes:

```bash
cd ~/sofia-pulse
source venv-analytics/bin/activate

python3 << 'EOF'
import pandas as pd
from sqlalchemy import create_engine
import google.generativeai as genai
import os

# Configurar
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

# Conectar e carregar
engine = create_engine('postgresql://sofia:sofia123strong@localhost:5432/sofia_db')
df_b3 = pd.read_sql('SELECT * FROM sofia.market_data_brazil', engine)
df_funding = pd.read_sql('SELECT * FROM sofia.funding_rounds', engine)

# Preparar summary
summary = f"""
B3: {len(df_b3)} stocks, média {df_b3['change_pct'].mean():.2f}%
Funding: ${df_funding['amount_usd'].sum():,.0f} investidos

Top setores funding:
{df_funding.groupby('sector')['amount_usd'].sum().nlargest(5)}
"""

# Gerar insights
response = model.generate_content(f"Analise estes dados financeiros e identifique oportunidades:\n\n{summary}")

print(response.text)
EOF
```

**Output**: Insights em texto direto no terminal.

**Custo**: $0.0013 (tier grátis!)

---

## 📁 Estrutura de Outputs

Depois de rodar qualquer análise, os resultados ficam em:

```
analytics/
├── reports/
│   ├── b3-profiling-report.html          # Pandas Profiling (abrir no browser)
│   └── b3-vs-nasdaq-comparison.html      # Sweetviz (abrir no browser)
│
├── insights/
│   ├── correlation-analysis.csv          # Correlações numéricas
│   ├── sector-clusters.csv               # Clusters identificados
│   ├── anomalies-detected.csv            # Outliers
│   ├── top-performers-b3.csv             # Top 20 B3
│   ├── top-funding-deals.csv             # Top 20 funding
│   └── gemini-insights-latest.md         # Narrativas AI
│
└── notebooks/
    └── data-mining-gemini.ipynb          # Notebook completo
```

---

## 🎯 Casos de Uso

### 1. Análise Diária Automática

Adicione ao cron para rodar toda noite:

```bash
# Crontab entry:
0 22 * * * cd ~/sofia-pulse && source venv-analytics/bin/activate && python3 scripts/daily-insights.py
```

(Criar script `scripts/daily-insights.py` depois)

---

### 2. Exploração Manual

Use D-Tale para explorar dados interativamente:

```bash
cd ~/sofia-pulse
source venv-analytics/bin/activate

python3 << 'EOF'
import pandas as pd
from sqlalchemy import create_engine
import dtale

engine = create_engine('postgresql://sofia:sofia123strong@localhost:5432/sofia_db')
df = pd.read_sql('SELECT * FROM sofia.market_data_brazil', engine)

d = dtale.show(df)
d.open_browser()
EOF
```

**Acesso**: http://localhost:40000

**Features**:
- Filtros interativos
- Correlações clicáveis
- Gráficos on-demand
- Export para CSV/Excel

---

### 3. Comparar Períodos

```python
# No Jupyter:
df_today = df_b3[df_b3['collected_at'] >= '2025-11-17']
df_yesterday = df_b3[df_b3['collected_at'] == '2025-11-16']

comparison = sv.compare([df_today, "Hoje"], [df_yesterday, "Ontem"])
comparison.show_html('analytics/reports/today-vs-yesterday.html')
```

---

## 💰 Custos (Gemini)

### Tier Grátis:
- ✅ 15 requests/min (Flash)
- ✅ 1,500 requests/dia
- ✅ **Suficiente para Sofia Pulse!**

### Se exceder tier grátis:

| Uso | Custo/Mês |
|-----|-----------|
| 1 análise/dia (30 req) | $0.04 |
| 2 análises/dia (60 req) | $0.08 |
| 10 análises/dia (300 req) | $0.39 |

**Comparação**:
- Claude: $1.80/mês (mesma carga)
- GPT-4o: $1.35/mês
- **Gemini: $0.39/mês** (10 análises/dia!)

---

## 🔧 Troubleshooting

### Erro: "GEMINI_API_KEY not found"

```bash
# Verificar .env:
grep GEMINI ~/.env

# Se vazio, adicionar:
echo 'GEMINI_API_KEY=sua_key' >> ~/.env
```

### Erro: "ModuleNotFoundError: google.generativeai"

```bash
source venv-analytics/bin/activate
pip install google-generativeai
```

### Jupyter não abre:

```bash
# Verificar porta 8888:
netstat -tuln | grep 8888

# Se ocupada, usar outra:
jupyter lab --port=8889
```

### Relatórios HTML não abrem:

```bash
# Abrir manualmente:
xdg-open analytics/reports/b3-analysis.html

# Ou via Python HTTP server:
cd analytics/reports
python3 -m http.server 8000
# Acesse: http://localhost:8000
```

---

## 📚 Próximos Passos

### 1. Testar Agora:

```bash
cd ~/sofia-pulse
./setup-data-mining.sh

# Depois:
source venv-analytics/bin/activate
jupyter lab
# Abrir: data-mining-gemini.ipynb
```

### 2. Explorar Relatórios:

Abra no browser:
- `analytics/reports/b3-profiling-report.html`
- `analytics/reports/b3-vs-nasdaq-comparison.html`

### 3. Ler Insights:

```bash
cat analytics/insights/gemini-insights-latest.md
```

### 4. Automatizar:

Criar script de análise diária (próximo passo!)

---

## 🆚 Comparação: Com IA vs Sem IA

| Feature | Sem IA (Grátis) | Com Gemini (Barato) | Com Claude (Caro) |
|---------|-----------------|---------------------|-------------------|
| **Correlações** | ✅ Pandas | ✅ Pandas + narrativa | ✅ Pandas + narrativa |
| **Clustering** | ✅ K-Means | ✅ K-Means + interpretação | ✅ K-Means + interpretação |
| **Anomalias** | ✅ Z-score | ✅ Z-score + explicação | ✅ Z-score + explicação |
| **Relatórios** | ✅ HTML automático | ✅ HTML + texto | ✅ HTML + texto |
| **Narrativas** | ❌ | ✅ Sim | ✅ Sim (melhor) |
| **Custo/mês** | **$0** | **$0.39** | **$1.80** |
| **Qualidade** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Recomendação**: Comece sem IA (grátis), depois adicione Gemini se quiser narrativas.

---

## 🎉 Resultado Esperado

Depois de rodar tudo, você terá:

1. ✅ **Relatórios HTML** com 50+ análises automáticas
2. ✅ **Correlações** entre funding e performance de mercado
3. ✅ **Clusters** de setores similares (ex: "Tech High Growth", "Financials Stable")
4. ✅ **Anomalias** detectadas (outliers para investigar)
5. ✅ **Insights narrativos** gerados por IA (ex: "Setor AI recebeu $10B mas performance média é apenas +0.5%, possível sobrevalorização")
6. ✅ **CSVs exportados** para uso em dashboards/BI
7. ✅ **Comparações** B3 vs NASDAQ

**Tudo isso em ~5 minutos de setup + 2 minutos de execução!**

---

**Começe agora**:
```bash
cd ~/sofia-pulse && ./setup-data-mining.sh
```

🚀 **Happy Data Mining!**
