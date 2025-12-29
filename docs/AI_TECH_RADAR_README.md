# 🤖 AI Technology Radar - Complete Documentation

**Data**: 2025-12-04
**Status**: ✅ SISTEMA COMPLETO - 100+ TECNOLOGIAS DE IA MONITORADAS
**Fontes**: GitHub, PyPI, NPM, HuggingFace, ArXiv

---

## 📋 RESUMO EXECUTIVO

O **AI Technology Radar** monitora o crescimento e adoção de **100+ tecnologias de IA** através de 5 fontes de dados diferentes:

### 🎯 O que monitora:

- **LLMs**: GPT-4, Claude, Gemini, Llama, DeepSeek, Mistral, Phi, Qwen, Gemma, etc.
- **Image/Video Gen**: Stable Diffusion, DALL-E, Midjourney, FLUX, Sora, Runway
- **Agent Frameworks**: LangChain, LangGraph, AutoGen, CrewAI, Pydantic AI
- **Inference**: vLLM, TensorRT-LLM, ONNX Runtime, llama.cpp, GGUF
- **RAG & Vectors**: ChromaDB, Milvus, pgvector, LanceDB, Qdrant, Weaviate
- **Multimodal**: LLaVA, CLIP, Qwen-VL, DeepSeek-VL
- **Audio**: Whisper, Bark, OpenVoice, ElevenLabs, MusicGen
- **Dev Tools**: Cursor, Aider, Continue, GitHub Copilot, Codeium
- **Edge/On-Device**: Apple MLX, TensorFlow Lite, Core ML
- **Safety**: Guardrails AI, RLHF, Constitutional AI
- **Observability**: LangFuse, LangSmith, Phoenix
- **Testing**: RAGAS, PromptFoo, EvalPlus

### 📊 Métricas Calculadas:

- **Hype Index** (0-100): Score composto de todas as fontes
- **Momentum** (%): Taxa de crescimento (7d, 30d, 90d)
- **Growth Rate**: Taxa de crescimento anualizada
- **Developer Adoption Score**: GitHub + PyPI + NPM
- **Research Interest Score**: ArXiv + HuggingFace
- **Velocity**: Stars/downloads por dia

### 🎁 Outputs:

- **1 Relatório TXT** completo (`ai-tech-radar-report.txt`)
- **6 CSVs** com rankings:
  - Top 20 tecnologias (hype index)
  - Rising Stars (highest momentum)
  - Dark Horses (high growth, low visibility)
  - By Category (top 5 em cada categoria)
  - Developer Adoption leaders
  - Research Interest leaders

---

## 🏗️ ARQUITETURA

### Estrutura de Arquivos (NOVOS)

```
sofia-pulse/
├── db/migrations/
│   └── 020_create_ai_tech_radar.sql          # Migration principal (5 tabelas)
│
├── sql/
│   └── 04-ai-tech-radar-views.sql            # 9 views SQL com métricas
│
├── scripts/
│   ├── collect-ai-github-trends.ts           # GitHub collector (TypeScript)
│   ├── collect-ai-pypi-packages.py           # PyPI collector (Python)
│   ├── collect-ai-npm-packages.ts            # NPM collector (TypeScript)
│   ├── collect-ai-huggingface-models.py      # HuggingFace collector (Python)
│   └── collect-ai-arxiv-keywords.py          # ArXiv collector (Python)
│
├── analytics/
│   └── ai-tech-radar-report.py               # Report generator (Python)
│
├── collect-ai-tech-radar.sh                  # Pipeline completo
├── test-ai-tech-radar.sh                     # Quick test
└── AI_TECH_RADAR_README.md                   # Esta documentação
```

### Tabelas do Banco de Dados

**1. `sofia.ai_github_trends`**
- Métricas de GitHub por tecnologia
- Campos: `tech_key`, `category`, `total_repos`, `total_stars`, `stars_7d`, `stars_30d`

**2. `sofia.ai_pypi_packages`**
- Downloads de pacotes Python
- Campos: `package_name`, `tech_key`, `downloads_7d`, `downloads_30d`, `downloads_90d`

**3. `sofia.ai_npm_packages`**
- Downloads de pacotes JavaScript
- Campos: `package_name`, `tech_key`, `downloads_7d`, `downloads_30d`, `downloads_90d`

**4. `sofia.ai_huggingface_models`**
- Popularidade de modelos HuggingFace
- Campos: `model_id`, `tech_key`, `likes`, `downloads_30d`, `downloads_total`

**5. `sofia.ai_arxiv_keywords`**
- Contagem de papers ArXiv por keyword
- Campos: `keyword`, `tech_key`, `paper_count`, `year`, `month`

**6. `sofia.ai_tech_categories`** (referência)
- Mapeamento de tech_key → categoria + aliases
- 100+ tecnologias pré-cadastradas

### Views SQL (9 views)

**Métricas por Fonte**:
1. `sofia.ai_github_metrics` - GitHub com momentum_7d, momentum_30d, velocity
2. `sofia.ai_pypi_metrics` - PyPI com momentum e growth rate
3. `sofia.ai_npm_metrics` - NPM com momentum e growth rate
4. `sofia.ai_huggingface_metrics` - HuggingFace com momentum
5. `sofia.ai_arxiv_metrics` - ArXiv com momentum mensal

**Views Consolidadas**:
6. `sofia.ai_tech_radar_consolidated` - **VIEW PRINCIPAL** com todas as métricas agregadas
7. `sofia.ai_top_technologies_by_category` - Top 5 em cada categoria
8. `sofia.ai_rising_stars` - Tecnologias com maior momentum
9. `sofia.ai_dark_horses` - Tecnologias com alto crescimento + baixa visibilidade

---

## 🚀 COMO USAR

### Setup Inicial

```bash
# 1. Certifique-se de que o .env está configurado
cat .env  # Verificar DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# 2. Certifique-se de ter as dependências
npm install  # Para collectors TypeScript
pip3 install psycopg2-binary pandas requests python-dotenv  # Para Python

# 3. (Opcional) Configure API tokens para rate limits maiores
# GitHub: https://github.com/settings/tokens (recomendado!)
# HuggingFace: https://huggingface.co/settings/tokens (opcional)
```

### Quick Test (Recomendado primeiro!)

```bash
# Testa 1 collector + migration + views
bash test-ai-tech-radar.sh

# Output esperado:
# ✅ Database connection successful
# ✅ Migration successful
# ✅ Views created
# ✅ PyPI collector test successful
# ✅ Data inserted successfully (XX records)
# ✅ View query successful
# ✅ ALL TESTS PASSED!
```

### Execução Completa

```bash
# Rodar TODOS os collectors + analytics + report
bash collect-ai-tech-radar.sh

# Isso vai:
# 1. Rodar migration + criar views
# 2. Coletar de GitHub (100+ tecnologias)
# 3. Coletar de PyPI (70+ pacotes)
# 4. Coletar de NPM (30+ pacotes)
# 5. Coletar de HuggingFace (modelos por tech)
# 6. Coletar de ArXiv (papers por keyword)
# 7. Gerar relatório completo + 6 CSVs
```

**⏱️ Tempo estimado**: 15-30 minutos (dependendo de rate limits)

### Execução Individual

```bash
# Rodar apenas 1 collector específico
npx tsx scripts/collect-ai-github-trends.ts
python3 scripts/collect-ai-pypi-packages.py
npx tsx scripts/collect-ai-npm-packages.ts
python3 scripts/collect-ai-huggingface-models.py
python3 scripts/collect-ai-arxiv-keywords.py

# Gerar apenas o relatório (requer dados já coletados)
python3 analytics/ai-tech-radar-report.py
```

---

## 📊 OUTPUTS

### 1. Relatório TXT (`output/ai-tech-radar-report.txt`)

**Seções**:
1. **TOP 20 AI TECHNOLOGIES** - Ranking geral por hype index
2. **RISING STARS** - 15 tecnologias com maior momentum
3. **DARK HORSES** - Tecnologias em crescimento + baixa visibilidade
4. **TOP TECHNOLOGIES BY CATEGORY** - Top 5 em cada categoria
5. **DEVELOPER ADOPTION LEADERS** - Mais usados por devs
6. **RESEARCH INTEREST LEADERS** - Mais pesquisados
7. **SUMMARY STATISTICS** - Estatísticas gerais

### 2. CSVs (6 arquivos)

**`ai_tech_top20.csv`**:
- Colunas: `tech_key`, `display_name`, `category`, `hype_index`, `overall_momentum`, `developer_adoption_score`, `research_interest_score`, `github_stars`, `pypi_downloads_30d`, `npm_downloads_30d`, `hf_likes`, `arxiv_papers_monthly`

**`ai_tech_rising_stars.csv`**:
- Tecnologias com maior momentum (crescimento)

**`ai_tech_dark_horses.csv`**:
- Tecnologias escondidas com alto potencial

**`ai_tech_by_category.csv`**:
- Top 5 em cada categoria (LLM, agents, RAG, etc.)

**`ai_tech_developer_adoption.csv`**:
- Ranking por adoção de desenvolvedores

**`ai_tech_research_interest.csv`**:
- Ranking por interesse acadêmico

---

## 🔍 QUERIES SQL ÚTEIS

### Top 10 Tecnologias (Hype Index)

```sql
SELECT
    display_name,
    category,
    hype_index,
    overall_momentum,
    github_stars,
    pypi_downloads_30d
FROM sofia.ai_tech_radar_consolidated
ORDER BY hype_index DESC
LIMIT 10;
```

### Rising Stars (Momentum > 50%)

```sql
SELECT
    display_name,
    category,
    overall_momentum,
    hype_index
FROM sofia.ai_tech_radar_consolidated
WHERE overall_momentum > 50
ORDER BY overall_momentum DESC;
```

### Dark Horses (Momentum alto + Hype baixo)

```sql
SELECT * FROM sofia.ai_dark_horses;
```

### Comparar LLMs (apenas categoria LLM)

```sql
SELECT
    display_name,
    hype_index,
    github_stars,
    hf_likes,
    arxiv_papers_monthly
FROM sofia.ai_tech_radar_consolidated
WHERE category = 'llm'
ORDER BY hype_index DESC;
```

### Growth Leaders (Top 10 por Growth Rate)

```sql
SELECT
    g.tech_key,
    c.display_name,
    g.growth_rate_annual,
    g.momentum_30d,
    g.total_stars
FROM sofia.ai_github_metrics g
JOIN sofia.ai_tech_categories c USING (tech_key)
ORDER BY g.growth_rate_annual DESC NULLS LAST
LIMIT 10;
```

---

## 📈 METODOLOGIAS

### Hype Index (0-100)

**Fórmula**:
```
hype_index = (
    normalized(github_stars) * 25% +
    normalized(pypi_downloads) * 20% +
    normalized(npm_downloads) * 15% +
    normalized(hf_likes) * 20% +
    normalized(arxiv_papers) * 20%
) * 100
```

**Normalization**:
- GitHub: stars / 10,000 (capped at 1.0)
- PyPI: downloads / 10M (capped at 1.0)
- NPM: downloads / 10M (capped at 1.0)
- HF: likes / 1,000 (capped at 1.0)
- ArXiv: papers/month / 100 (capped at 1.0)

### Developer Adoption Score (0-100)

**Fórmula**:
```
developer_adoption = (
    normalized(github_stars) * 40% +
    normalized(pypi_downloads) * 30% +
    normalized(npm_downloads) * 30%
) * 100
```

### Research Interest Score (0-100)

**Fórmula**:
```
research_interest = (
    normalized(arxiv_papers) * 60% +
    normalized(hf_likes) * 40%
) * 100
```

### Momentum Calculations

**Momentum 30d (%)**: `((current - 30d_ago) / 30d_ago) * 100`

**Growth Rate (annualized)**: `(POWER(current / 30d_ago, 365/30) - 1) * 100`

**Velocity (daily)**: `stars_30d / 30` ou `downloads_30d / 30`

---

## 🔧 INTEGRAÇÃO COM PIPELINE EXISTENTE

### Adicionar ao Cron Schedule

Editar `update-crontab-distributed.sh`:

```bash
# Add AI Tech Radar collection (weekly on Sundays at 8:00 UTC)
0 8 * * 0 bash /path/to/sofia-pulse/collect-ai-tech-radar.sh
```

### Adicionar ao Email Diário

Editar `send-email-mega.py`:

```python
# Add AI Tech Radar report
attachments.append('output/ai-tech-radar-report.txt')
attachments.append('output/ai_tech_top20.csv')
attachments.append('output/ai_tech_rising_stars.csv')
```

### Adicionar ao WhatsApp Alerts

Editar `send-reports-whatsapp.py`:

```python
# Send AI Tech Radar summary
with open('output/ai-tech-radar-report.txt') as f:
    lines = f.readlines()[:50]  # First 50 lines
    summary = ''.join(lines)
    send_whatsapp(f"🤖 AI Tech Radar Report\n\n{summary}")
```

---

## ⚠️ LIMITAÇÕES & NOTAS

### Rate Limits

| API | Limite sem token | Limite com token | Solução |
|-----|------------------|------------------|---------|
| GitHub | 60 req/hora | 5000 req/hora | Usar GITHUB_TOKEN |
| PyPI | Sem limite oficial | - | Delay de 1s entre requests |
| NPM | Sem limite oficial | - | Delay de 1s |
| HuggingFace | 1000 req/hora | Maior | Usar HF_TOKEN (opcional) |
| ArXiv | ~1 req/3s | - | Delay de 3s entre requests |

**Recomendação**: Rodar 1x por semana (domingo) para evitar rate limits.

### Dados não disponíveis

- ❌ **Demographics** (sexo, idade, localização): NÃO disponível nas APIs públicas (privacidade)
- ⚠️ **Downloads exatos**: PyPI/NPM fornecem apenas aproximações
- ⚠️ **HuggingFace downloads_30d**: API retorna apenas total downloads (não diferencia 30d)

### Dados estimados

- NPM `downloads_7d`: Estimado como 25% de `downloads_30d`
- NPM `downloads_90d`: Estimado como 3x `downloads_30d`
- PyPI `downloads_90d`: Estimado como 3x `downloads_30d`

---

## 🐛 TROUBLESHOOTING

### Erro: "relation 'sofia.ai_github_trends' does not exist"

**Solução**:
```bash
# Rodar migration manualmente
psql -h localhost -U sofia -d sofia_db -f db/migrations/020_create_ai_tech_radar.sql
```

### Erro: "GitHub API rate limit exceeded"

**Solução**:
```bash
# Adicionar GITHUB_TOKEN ao .env
echo "GITHUB_TOKEN=ghp_your_token_here" >> .env

# Obter token em: https://github.com/settings/tokens
```

### Erro: "No module named 'psycopg2'"

**Solução**:
```bash
pip3 install psycopg2-binary pandas requests python-dotenv
```

### Erro: "npx: command not found"

**Solução**:
```bash
npm install -g tsx
```

### View retorna 0 resultados

**Solução**:
```bash
# Verificar se os collectors rodaram com sucesso
psql -h localhost -U sofia -d sofia_db -c "SELECT COUNT(*) FROM sofia.ai_github_trends;"
psql -h localhost -U sofia -d sofia_db -c "SELECT COUNT(*) FROM sofia.ai_pypi_packages;"

# Se COUNT = 0, rodar os collectors novamente
```

---

## 📚 REFERÊNCIAS

### APIs Utilizadas

- **GitHub API**: https://docs.github.com/en/rest
- **PyPI Stats API**: https://pypistats.org/api/
- **NPM Registry API**: https://github.com/npm/registry/blob/master/docs/REGISTRY-API.md
- **HuggingFace Hub API**: https://huggingface.co/docs/hub/api
- **ArXiv API**: https://arxiv.org/help/api/

### Bibliotecas

- **TypeScript**: pg, dotenv, axios
- **Python**: psycopg2, pandas, requests, python-dotenv

---

## 🎯 PRÓXIMOS PASSOS

### Melhorias Futuras

1. **Dashboard Web** - Visualização interativa (Plotly, Streamlit)
2. **API REST** - Expor dados via API
3. **Alertas automáticos** - WhatsApp quando tecnologia atinge momentum > 100%
4. **Previsões ML** - LSTM para prever hype_index futuro
5. **Competitor Analysis** - Comparar tecnologias similares
6. **Historical Tracking** - Gráficos de evolução ao longo do tempo
7. **Sentiment Analysis** - Análise de sentimento em GitHub Issues/Reddit
8. **Job Market Integration** - Correlacionar com vagas de emprego

### Dados Adicionais

- **Reddit** (r/MachineLearning, r/LocalLLaMA)
- **StackOverflow** (tag counts)
- **LinkedIn Jobs** (vagas por tecnologia)
- **Twitter/X** (menções de tecnologias)
- **YouTube** (tutoriais por tecnologia)

---

## 📧 CONTATO

**Projeto**: Sofia Pulse
**Maintainer**: augustosvm@gmail.com
**Repositório**: sofia-pulse
**Documentação**: AI_TECH_RADAR_README.md

---

**Última Atualização**: 2025-12-04
**Versão**: 1.0.0
**Status**: ✅ Production Ready
