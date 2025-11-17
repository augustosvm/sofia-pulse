# Sofia Pulse Analytics Layer

## 🎯 Visão Geral

Esta camada transforma dados brutos coletados pelo Sofia Pulse em **insights acionáveis** que alimentam a Sofia IA.

```
[Raw Data] → [SQL Analytics] → [Insights API] → [Sofia IA] → [Recomendações Personalizadas]
```

---

## 📁 Estrutura

```
analytics/
├── README.md                          # Este arquivo
├── queries/                           # SQL queries por nicho
│   ├── education-insights.sql         # Estudantes, PhDs, professores
│   ├── investment-insights.sql        # VCs, angels, investidores
│   └── career-business-insights.sql   # Profissionais, CTOs, headhunters
├── notebooks/                         # Jupyter notebooks (análise exploratória)
│   └── (to be created)
└── dashboards/                        # Configs Grafana (futuro)
    └── (to be created)
```

---

## 🔧 Stack Tecnológico

### ✅ Já Configurado:
1. **PostgreSQL 15+** - Banco de dados com todas as tabelas
2. **Grafana** - Visualizações e dashboards (porta 3000)
   - Documentação: `DEPLOY.md` linha 260
   - Datasource: `sofia-postgres:5432`

### 🎯 Próximos:
3. **Jupyter Notebooks** - Exploração de dados e prototipagem
4. **FastAPI** - REST API para Sofia consumir insights
5. **Redis** - Cache de queries frequentes

---

## 📊 Queries Disponíveis

### 1. Education Insights (`queries/education-insights.sql`)

**Público**: Estudantes, mestrandos, doutorandos, professores

**Queries Principais**:
- **Research Gaps**: Temas com muito funding mas poucos papers (oportunidade para PhD!)
- **Emerging Topics**: Papers crescendo >200% (próximos hot topics)
- **Top Universities**: Ranking por área de pesquisa
- **Best PIs**: Pesquisadores com track record de funding
- **Scholarship Deadlines**: NSF GRFP, NIH F31, Fulbright, CAPES
- **Cross-disciplinary**: AI + Bio, Quantum + ML, etc.

**Exemplo de uso**:
```bash
# Conectar ao PostgreSQL
docker exec -it sofia-postgres psql -U sofia -d sofia_db

# Rodar query
\i /path/to/education-insights.sql
```

**Output exemplo**:
```
research_area         | NIH Grants | Total Funding | Papers | Grant/Paper Ratio | Opportunity
CRISPR Epigenetics    | 150        | $300M         | 20     | 7.5              | HIGH OPPORTUNITY
mRNA Cancer Therapy   | 80         | $160M         | 15     | 5.3              | HIGH OPPORTUNITY
```

---

### 2. Investment Insights (`queries/investment-insights.sql`)

**Público**: VCs, angels, family offices, investidores

**Queries Principais**:
- **Arbitrage Opportunities**: Research momentum mas poucas startups (timing ideal!)
- **Emerging Sectors**: Setores em early-stage com crescimento acelerado
- **Bubble Detection**: Funding alto vs. fundamentação científica fraca (evitar!)
- **University Spin-offs**: Papers com potencial comercial
- **Competitive Intelligence**: Quem está investindo onde
- **Economic Leading Indicators**: Cardboard, eletricidade (timing macro)
- **Patent Moats**: Empresas com vantagem competitiva via IP
- **Biotech Pipeline**: NIH grants hoje = produtos em 5-7 anos

**Exemplo de uso**:
```sql
-- Rodar query 1: Arbitrage Opportunities
-- Output:
technology          | Papers (12mo) | Startups | Paper/Startup Ratio | Signal
Diffusion Models    | 500           | 8        | 62.5               | STRONG BUY
AI Protein Design   | 150           | 3        | 50.0               | STRONG BUY
Neuromorphic        | 120           | 5        | 24.0               | BUY
```

**Decisão de investimento**:
- **Diffusion Models**: Technology de-risked (500 papers), mercado nascente (só 8 startups)
- **Ação**: Investir seed/Series A em próximas 3-5 startups nessa área

---

### 3. Career & Business Insights (`queries/career-business-insights.sql`)

**Público**: Profissionais, headhunters, CTOs, product managers

**Queries Principais**:

**Career**:
- **Emerging Roles**: Detecta roles que vão explodir em 6-12 meses
- **Skills Gap**: Supply vs. Demand (onde há shortage = salários altos)
- **Career Transitions**: De Software Engineer → ML Engineer (ROI +40%)

**Business**:
- **Competitor Tracking**: Patentes dos competidores
- **Technology Adoption Curve**: Onde cada tech está no hype cycle (Gartner-style)
- **Build vs. Buy vs. Partner**: Decision matrix data-driven
- **Talent Availability**: Onde contratar para cada skill
- **Innovation Budget**: Como alocar R&D budget baseado em trends

**Exemplo de uso**:
```sql
-- Query: Emerging Roles
-- Output:
Emerging Role/Skill    | Papers (6mo) | Growth % | Career Opportunity         | Salary Range
LLM Evaluation         | 150          | 1000%    | EXPLOSIVE - Learn NOW      | $150k-300k
AI Safety Engineering  | 80           | 500%     | VERY HIGH - Strong career  | $160k-320k
Multimodal AI          | 120          | 300%     | VERY HIGH                  | $140k-280k
```

**Decisão de carreira**:
- **LLM Evaluation**: Papers cresceram 1000% mas vagas ainda raras
- **Ação**: Estudar AGORA (HELM, red-teaming, benchmarking) → Em 6-12 meses, explosão de demanda

---

## 🚀 Como Usar

### Opção 1: Direto no PostgreSQL

```bash
# 1. Conectar ao banco
docker exec -it sofia-postgres psql -U sofia -d sofia_db

# 2. Rodar query específica
\i /home/user/sofia-pulse/analytics/queries/education-insights.sql

# 3. Ou copiar/colar queries individuais
```

### Opção 2: Via Grafana (Visual)

```bash
# 1. Acessar Grafana
http://SEU_IP:3000
# Login: admin/admin

# 2. Add datasource:
Configuration → Data Sources → Add PostgreSQL
Host: sofia-postgres:5432
Database: sofia_db
User: sofia
Password: (sua senha)

# 3. Criar dashboard:
Create → Dashboard → Add panel → Copiar SQL query
```

### Opção 3: Via Script Python (Programático)

```python
import psycopg2
import pandas as pd

# Conectar
conn = psycopg2.connect(
    host="localhost",
    database="sofia_db",
    user="sofia",
    password="sua_senha"
)

# Ler query de arquivo
with open('analytics/queries/investment-insights.sql', 'r') as f:
    query = f.read()

# Executar e transformar em DataFrame
df = pd.read_sql(query, conn)
print(df.head())

conn.close()
```

### Opção 4: Via Jupyter Notebook (Exploratório)

```bash
# Instalar Jupyter (se ainda não tiver)
pip install jupyter psycopg2-binary pandas matplotlib

# Iniciar Jupyter
jupyter notebook analytics/notebooks/
```

**Notebook exemplo** (`analytics/notebooks/exploration.ipynb`):
```python
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

# Conectar
conn = psycopg2.connect(...)

# Query
query = "SELECT * FROM education_insights LIMIT 100"
df = pd.read_sql(query, conn)

# Visualizar
df.plot(x='research_area', y='grant_paper_ratio', kind='bar')
plt.show()
```

---

## 🔮 Roadmap

### ✅ Fase 1: SQL Queries (Atual)
- [x] Education insights (8 queries)
- [x] Investment insights (10 queries)
- [x] Career & Business insights (10 queries)
- [ ] Government/Policy insights (futuro)
- [ ] Journalist insights (futuro)

### 🎯 Fase 2: Insights API (Próximo)
- [ ] FastAPI REST endpoints (`/api/insights/{niche}`)
- [ ] GraphQL para queries customizadas
- [ ] WebSocket para real-time alerts
- [ ] Rate limiting e caching (Redis)

**Estrutura da API**:
```
GET /api/insights/education?level=phd&area=biotech
GET /api/insights/investment?sector=ai&stage=seed
GET /api/insights/career?current_role=engineer&interests=ai
GET /api/insights/business?industry=ecommerce
```

**Response exemplo**:
```json
{
  "insights": [
    {
      "type": "research_gap",
      "title": "CRISPR Epigenético - Alto Funding, Baixa Competição",
      "confidence": 0.92,
      "data": {
        "nih_grants": 150,
        "papers_published": 20,
        "gap_ratio": 7.5
      },
      "recommendation": "Proposta de doutorado tem 92% chance de funding",
      "action_items": ["Estudar papers recentes", "Conectar com PIs top"]
    }
  ]
}
```

### 📊 Fase 3: Advanced Analytics
- [ ] Jupyter Notebooks com análises aprofundadas
- [ ] Machine Learning para previsões (RandomForest, XGBoost)
- [ ] Anomaly detection (bolhas, crises, breakthroughs)
- [ ] Correlation analysis (leading indicators)
- [ ] Time-series forecasting (ARIMA, Prophet)

### 🎨 Fase 4: Dashboards
- [ ] Grafana dashboards por nicho
- [ ] Real-time metrics (collectors rodando, data freshness)
- [ ] KPIs: Papers/dia, Funding/semana, Patents/mês
- [ ] Alertas automáticos (via Slack, email)

---

## 💡 Casos de Uso Práticos

### 1. Estudante de Doutorado

**Pergunta**: "Qual tema escolher para meu PhD em biotech?"

**Query**: `education-insights.sql` → Query 1 (Research Gaps)

**Resultado**:
```
CRISPR Epigenetics: 150 grants, 20 papers → Gap ratio 7.5 → HIGH OPPORTUNITY
```

**Ação**:
1. Ler 20 papers existentes
2. Conectar com PIs: Jennifer Doudna, David Liu
3. Aplicar para NIH F31 (deadline outubro)

---

### 2. VC (Seed Stage)

**Pergunta**: "Onde investir $5M em AI?"

**Query**: `investment-insights.sql` → Query 1 (Arbitrage Opportunities)

**Resultado**:
```
Diffusion Models: 500 papers, 8 startups → Paper/Startup ratio 62.5 → STRONG BUY
```

**Ação**:
1. Shortlist 3-5 startups (Stability AI, Midjourney competitors)
2. Diligence técnica (papers citados, team background)
3. Oferecer seed $2-5M (valuation $15-30M pré-money)

---

### 3. Software Engineer (Career Transition)

**Pergunta**: "Para onde pivotar minha carreira?"

**Query**: `career-business-insights.sql` → Query 1 (Emerging Roles)

**Resultado**:
```
LLM Evaluation: Growth 1000%, Salary $150k-300k → EXPLOSIVE - Learn NOW
```

**Ação**:
1. Estudar: HELM, TruthfulQA, red-teaming
2. Contribuir: EleutherAI/lm-evaluation-harness
3. Aplicar: Anthropic, OpenAI (daqui 6-12 meses quando demanda explodir)

---

### 4. CTO de E-commerce

**Pergunta**: "Devo construir ou comprar recomendação com AI?"

**Query**: `career-business-insights.sql` → Query 6 (Build vs. Buy)

**Resultado**:
```
AI Recommendations: Market maturity HIGH, 15+ vendors → BUY (Algolia, Bloomreach)
```

**Ação**:
1. RFP para 3 vendors
2. POC 30 dias
3. Decisão: SaaS ($50k-200k/ano) vs. Build ($500k+ team)

---

## 🔐 Segurança e Privacidade

- **Dados públicos**: Todos os dados coletados são públicos (papers, patents, grants)
- **Nenhum PII**: Não coletamos dados pessoais identificáveis
- **API Authentication**: Em produção, usar API keys (JWT tokens)
- **Rate Limiting**: Evitar abuse (100 requests/min por IP)

---

## 🤝 Como Sofia IA Consome

```python
# Sofia IA chamando Insights API
import requests

# Pergunta do usuário: "Quero fazer doutorado em CRISPR, vale a pena?"
user_profile = {
    "type": "phd_student",
    "area": "biotech",
    "interest": "CRISPR"
}

# Sofia chama API
response = requests.get(
    "http://sofia-pulse-api/insights/education",
    params={"area": "biotech", "topic": "CRISPR"}
)

insights = response.json()

# Sofia processa e responde
if insights[0]['opportunity_level'] == 'HIGH OPPORTUNITY':
    sofia_response = f"""
    Sim, vale MUITO a pena! Detectei um GAP DE PESQUISA:
    - 150 grants do NIH nos últimos 2 anos ($300M funding total)
    - Apenas 20 papers publicados
    - Grant/Paper ratio: 7.5 (MUITO ALTO!)

    Recomendação:
    1. Focar em 'CRISPR Epigenetics' especificamente
    2. PIs recomendados: Jennifer Doudna (Berkeley), David Liu (Harvard)
    3. Deadline próximo: NIH F31 (outubro), NSF GRFP (outubro)
    4. Probabilidade de conseguir funding: 92%

    Quer que eu te ajude a draftar uma proposta de pesquisa?
    """
```

---

## 📈 Métricas de Sucesso

**Para Education**:
- % de teses baseadas em recomendações Sofia (target: 20%)
- Taxa de aprovação de propostas (target: >70% vs. baseline 15%)

**Para Investment**:
- ROI de recomendações (target: >3x em 5 anos)
- Precision de timing (target: investir 6-12mo antes do hype)

**Para Career**:
- % conseguindo emprego em áreas recomendadas (target: >60%)
- Aumento salarial médio (target: >40%)

**Para Business**:
- % empresas adotando techs recomendadas (target: >30%)
- ROI de decisões build/buy/partner (target: >2x)

---

## 🐛 Troubleshooting

### Erro: "relation does not exist"
```sql
-- Solução: Rodar collectors primeiro
npm run collect:arxiv-ai
npm run collect:ai-companies
npm run collect:nih-grants
```

### Erro: "connection refused"
```bash
# Verificar PostgreSQL rodando
docker ps | grep sofia-postgres

# Restart se necessário
docker restart sofia-postgres
```

### Query muito lenta
```sql
-- Adicionar índice
CREATE INDEX idx_arxiv_keywords ON arxiv_ai_papers USING GIN (keywords);
CREATE INDEX idx_arxiv_date ON arxiv_ai_papers (published_date DESC);
```

---

## 📚 Referências

- **OpenAlex**: https://openalex.org/ (250M papers)
- **ArXiv**: https://arxiv.org/ (2.3M preprints)
- **NIH RePORTER**: https://reporter.nih.gov/ ($42B grants)
- **EPO**: https://www.epo.org/ (European patents)
- **Grafana Docs**: https://grafana.com/docs/

---

## 🤝 Contribuindo

Para adicionar novas queries:

1. Criar arquivo em `analytics/queries/{niche}-insights.sql`
2. Seguir padrão: Comentários explicativos + CTEs + ORDER BY + LIMIT
3. Testar com dados reais
4. Documentar casos de uso neste README

---

**Status**: 🚧 Em construção
**Última atualização**: 2025-01-17
**Contato**: Sofia Intelligence Hub
